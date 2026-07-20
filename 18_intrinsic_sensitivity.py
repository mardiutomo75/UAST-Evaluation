import copy
import hashlib
import json
import re
from itertools import combinations

import psycopg2
from psycopg2.extras import Json, execute_values
from scipy.stats import spearmanr

from parserfunc import ast_compression_ratio, calculate_pec, count_ast_nodes, ted_similarity


DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "codesearchnet",
    "user": "postgres",
    "password": "postgres",
    "options": "-c search_path=public",
}

CORRUPTION_LEVELS = [0.0, 0.10, 0.25, 0.50, 0.75]
PEC_SAMPLE_LIMIT = 40
CLSA_PAIR_LIMIT = 20
SEED = 20240629

HUMANEVAL_LANGUAGES = ["cpp", "go", "java", "javascript", "python", "rust"]
C2C_LANGUAGES = [("java", "cs")]


def table_name(prefix, language):
    return f"{prefix}_{language}"


def load_json(value):
    if value is None:
        return None
    if isinstance(value, dict):
        return value
    return json.loads(value)


def stable_unit_float(*parts):
    text = "|".join(map(str, parts)).encode("utf-8")
    digest = hashlib.sha256(text).digest()
    return int.from_bytes(digest[:8], "big") / float(1 << 64)


def normalize_token(value):
    token = re.sub(r"\W+", "_", str(value or "").strip().lower()).strip("_")
    return token or "node"


def degrade_ast(node, severity, seed, path=()):
    if not isinstance(node, dict):
        return node

    new_node = {k: copy.deepcopy(v) for k, v in node.items() if k != "children"}
    node_score = stable_unit_float(seed, path, "node")

    if path and severity > 0 and node_score < severity * 0.55:
        new_node["type"] = f"masked_{normalize_token(node.get('type'))}"

    text_value = new_node.get("text")
    if text_value is not None and severity > 0 and node_score < severity * 0.70:
        new_node["text"] = ""

    children = node.get("children") or []
    if children:
        kept_children = []
        for idx, child in enumerate(children):
            child_path = path + (idx,)
            child_score = stable_unit_float(seed, child_path, "drop")
            if child_score < severity:
                continue
            kept_children.append(degrade_ast(child, severity, seed, child_path))

        if not kept_children:
            best_idx = min(
                range(len(children)),
                key=lambda idx: stable_unit_float(seed, path + (idx,), "drop"),
            )
            kept_children.append(degrade_ast(children[best_idx], severity, seed, path + (best_idx,)))

        new_node["children"] = kept_children
    else:
        new_node.pop("children", None)

    return new_node


def summary_stats(values):
    values = [float(v) for v in values]
    if not values:
        return None
    mean = sum(values) / len(values)
    if len(values) > 1:
        variance = sum((v - mean) ** 2 for v in values) / (len(values) - 1)
        std = variance ** 0.5
    else:
        std = 0.0
    return {
        "count": len(values),
        "mean": mean,
        "std": std,
        "min": min(values),
        "max": max(values),
    }


def build_seed(*parts):
    return "|".join(map(str, parts))


def ensure_table(cur):
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS intrinsic_sensitivity_results (
            id BIGSERIAL PRIMARY KEY,
            created_at timestamptz DEFAULT now(),
            dataset text NOT NULL,
            task text NOT NULL,
            metric text NOT NULL,
            language1 text,
            language2 text,
            sample_key text NOT NULL,
            representation text NOT NULL,
            corruption_type text NOT NULL,
            corruption_level numeric NOT NULL,
            sample_count integer,
            baseline_value numeric,
            value numeric NOT NULL,
            delta numeric,
            details jsonb
        )
        """
    )
    cur.execute(
        """
        CREATE INDEX IF NOT EXISTS intrinsic_sensitivity_lookup
            ON intrinsic_sensitivity_results (dataset, task, metric, corruption_type, corruption_level)
        """
    )


def load_pec_samples(cur, table, limit):
    cur.execute(
        f"""
        SELECT id, ast_original, ast_unified
        FROM {table}
        WHERE ast_status IN (1, 2)
          AND ast_original IS NOT NULL
          AND ast_unified IS NOT NULL
        ORDER BY md5(id::text)
        LIMIT %s
        """,
        (limit,),
    )
    rows = []
    for row_id, ast_original, ast_unified in cur.fetchall():
        rows.append(
            {
                "id": int(row_id),
                "ast_original": load_json(ast_original),
                "ast_unified": load_json(ast_unified),
            }
        )
    return rows


def load_clsa_pairs(cur, table_left, table_right, limit):
    cur.execute(
        f"""
        SELECT
            l.id,
            l.ast_unified,
            r.ast_unified
        FROM {table_left} l
        INNER JOIN {table_right} r ON l.id = r.id
        WHERE l.ast_status IN (1, 2)
          AND r.ast_status IN (1, 2)
          AND l.ast_unified IS NOT NULL
          AND r.ast_unified IS NOT NULL
        ORDER BY md5(l.id::text)
        LIMIT %s
        """,
        (limit,),
    )
    rows = []
    for row_id, left_ast, right_ast in cur.fetchall():
        rows.append(
            {
                "id": int(row_id),
                "left_ast": load_json(left_ast),
                "right_ast": load_json(right_ast),
            }
        )
    return rows


def pec_row(dataset, language, sample_id, severity, ast_original, ast_unified):
    seed = build_seed("pec", dataset, language, sample_id, SEED)
    corrupted = degrade_ast(ast_unified, severity, seed)
    pec = calculate_pec(ast_original, corrupted)
    baseline = calculate_pec(ast_original, ast_unified)
    comp_ratio = ast_compression_ratio(ast_original, corrupted)
    return (
        dataset,
        "PEC",
        "PEC",
        language,
        None,
        f"{dataset}:{language}:{sample_id}",
        "UAST",
        "node_drop_mask",
        severity,
        1,
        baseline["pec"],
        pec["pec"],
        pec["pec"] - baseline["pec"],
        Json(
            {
                "seed": seed,
                "original_nodes": count_ast_nodes(ast_unified),
                "corrupted_nodes": count_ast_nodes(corrupted),
                "compression_ratio": comp_ratio["compression_ratio"],
                "compression_gain": comp_ratio["compression_gain"],
                "baseline_pec_all": baseline["pec_all"],
                "corrupted_pec_all": pec["pec_all"],
            }
        ),
    )


def clsa_row(dataset, lang1, lang2, sample_id, severity, left_ast, right_ast):
    seed = build_seed("clsa", dataset, lang1, lang2, sample_id, SEED)
    corrupted_left = degrade_ast(left_ast, severity, seed)
    baseline = ted_similarity(left_ast, right_ast)
    value = ted_similarity(corrupted_left, right_ast)
    return (
        dataset,
        "CLSA",
        "CLSA",
        lang1,
        lang2,
        f"{dataset}:{lang1}:{lang2}:{sample_id}",
        "UAST",
        "node_drop_mask",
        severity,
        1,
        baseline["similarity"],
        value["similarity"],
        value["similarity"] - baseline["similarity"],
        Json(
            {
                "seed": seed,
                "baseline_distance": baseline["distance"],
                "corrupted_distance": value["distance"],
                "baseline_similarity": baseline["similarity"],
                "corrupted_nodes": count_ast_nodes(corrupted_left),
                "left_nodes": count_ast_nodes(left_ast),
                "right_nodes": count_ast_nodes(right_ast),
            }
        ),
    )


def store_rows(cur, rows):
    cur.execute("DELETE FROM intrinsic_sensitivity_results")
    query = """
        INSERT INTO intrinsic_sensitivity_results (
            dataset, task, metric, language1, language2, sample_key,
            representation, corruption_type, corruption_level,
            sample_count, baseline_value, value, delta, details
        ) VALUES %s
    """
    execute_values(cur, query, rows, page_size=500)


def fetch_and_build(cur):
    rows = []

    pec_sources = [
        ("HumanEval-X", "cpp", "heval_cpp"),
        ("HumanEval-X", "go", "heval_go"),
        ("HumanEval-X", "java", "heval_java"),
        ("HumanEval-X", "javascript", "heval_javascript"),
        ("HumanEval-X", "python", "heval_python"),
        ("HumanEval-X", "rust", "heval_rust"),
        ("Code2Code Java-C#", "java", "c2c_java"),
        ("Code2Code Java-C#", "cs", "c2c_cs"),
    ]

    for dataset, language, table in pec_sources:
        samples = load_pec_samples(cur, table, PEC_SAMPLE_LIMIT)
        for sample in samples:
            for severity in CORRUPTION_LEVELS:
                rows.append(
                    pec_row(
                        dataset,
                        language,
                        sample["id"],
                        severity,
                        sample["ast_original"],
                        sample["ast_unified"],
                    )
                )

    heval_pairs = list(combinations(HUMANEVAL_LANGUAGES, 2))
    for lang1, lang2 in heval_pairs:
        samples = load_clsa_pairs(cur, f"heval_{lang1}", f"heval_{lang2}", CLSA_PAIR_LIMIT)
        for sample in samples:
            for severity in CORRUPTION_LEVELS:
                rows.append(
                    clsa_row(
                        "HumanEval-X",
                        lang1,
                        lang2,
                        sample["id"],
                        severity,
                        sample["left_ast"],
                        sample["right_ast"],
                    )
                )

    for lang1, lang2 in C2C_LANGUAGES:
        samples = load_clsa_pairs(cur, f"c2c_{lang1}", f"c2c_{lang2}", CLSA_PAIR_LIMIT)
        for sample in samples:
            for severity in CORRUPTION_LEVELS:
                rows.append(
                    clsa_row(
                        "Code2Code Java-C#",
                        lang1,
                        lang2,
                        sample["id"],
                        severity,
                        sample["left_ast"],
                        sample["right_ast"],
                    )
                )

    return rows


def print_summary(rows):
    grouped = {}
    for row in rows:
        key = (row[0], row[1], row[2], row[8])
        grouped.setdefault(key, []).append(float(row[11]))

    for key in sorted(grouped):
        stats = summary_stats(grouped[key])
        dataset, task, metric, severity = key
        print(
            (
                dataset,
                task,
                metric,
                severity,
                stats["count"],
                round(stats["mean"], 6),
                round(stats["std"], 6),
                round(stats["min"], 6),
                round(stats["max"], 6),
            )
        )


def print_spearman(rows):
    grouped = {}
    for row in rows:
        key = (row[0], row[1], row[2])
        grouped.setdefault(key, {"x": [], "y": []})
        grouped[key]["x"].append(float(row[8]))
        grouped[key]["y"].append(float(row[11]))

    for key in sorted(grouped):
        x = grouped[key]["x"]
        y = grouped[key]["y"]
        if len(set(x)) < 2 or len(set(y)) < 2:
            continue
        rho = spearmanr(x, y).correlation
        print((key[0], key[1], key[2], round(float(rho), 6)))


def main():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    ensure_table(cur)

    rows = fetch_and_build(cur)
    store_rows(cur, rows)
    conn.commit()

    cur.execute(
        """
        SELECT dataset, task, metric, corruption_level, count(*),
               round(avg(value), 6), round(stddev_samp(value), 6),
               round(min(value), 6), round(max(value), 6)
        FROM intrinsic_sensitivity_results
        GROUP BY dataset, task, metric, corruption_level
        ORDER BY dataset, task, metric, corruption_level
        """
    )
    for row in cur.fetchall():
        print(row)

    print_spearman(rows)

    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
