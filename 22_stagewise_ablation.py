import json
from collections import defaultdict

import psycopg2
from psycopg2.extras import Json, execute_values

from parserfunc import (
    Myparser,
    ast_compression_ratio,
    calculate_pec,
    count_ast_nodes,
    ted_similarity,
)


DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "codesearchnet",
    "user": "postgres",
    "password": "postgres",
    "options": "-c search_path=public",
}

LANG_IDS = {
    "python": 0,
    "php": 1,
    "go": 2,
    "ruby": 3,
    "java": 4,
    "javascript": 5,
    "cs": 6,
    "cpp": 7,
    "rust": 8,
}

VARIANTS = [
    ("Original AST", 0, False, False, False),
    ("Tm", 1, True, False, False),
    ("Tm+Tn", 2, True, True, False),
    ("Tm+Tn+Tc", 3, True, True, True),
]

HEVAL_LANGS = ["cpp", "go", "java", "javascript", "python", "rust"]
HEVAL_PAIR_LIMIT = None
C2C_SAMPLE_LIMIT = None
C2T_LANGS = ["go", "java", "javascript", "php", "python", "ruby"]


def ensure_table(cur):
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS stagewise_ablation_results (
            id BIGSERIAL PRIMARY KEY,
            created_at timestamptz DEFAULT now(),
            dataset text NOT NULL,
            ablation_variant text NOT NULL,
            stage_order integer NOT NULL,
            sample_count integer,
            pair_count integer,
            pec_core numeric,
            pec_all numeric,
            clsa numeric,
            resr numeric,
            avg_nodes numeric,
            details jsonb
        )
        """
    )


def valid_children(children):
    return [
        ch for ch in children
        if isinstance(ch, dict)
        and (
            (ch.get("type") or "").strip()
            or (ch.get("text") or "").strip()
            or ch.get("children")
        )
    ]


def node_to_variant(parser, node, source_code, use_tm, use_tn, use_tc, visited=None, depth=0):
    if node is None:
        return None
    if visited is None:
        visited = set()

    key = (id(node), depth)
    if key in visited:
        return None
    visited.add(key)

    if depth > parser.max_depth:
        return None
    if hasattr(node, "children") and len(node.children) > 500:
        return None

    raw_type = (node.type or "").strip()
    raw_type_l = raw_type.lower()
    node_type = parser.normalize_node_type(raw_type_l) if use_tm else raw_type_l

    try:
        text = source_code[node.start_byte:node.end_byte].decode("utf8")
    except Exception:
        text = ""

    if use_tn:
        text = text.replace("$", "").replace("@", "")
        text = text.strip(";")
        text = parser.normalize_text(text)

    children = []
    for i, child in enumerate(getattr(node, "children", [])):
        if i >= 300:
            break
        ch = node_to_variant(parser, child, source_code, use_tm, use_tn, use_tc, visited, depth + 1)
        if ch is not None:
            children.append(ch)

    children = valid_children(children)

    if use_tc:
        is_type_node = node_type == "type"
        text_key = text.lower().strip() if use_tn else text.strip().lower()
        if text_key in parser.noderemoves and not is_type_node:
            return None
        if node_type.lower().strip() in parser.noderemoves and not is_type_node:
            return None

        if len(children) == 1 and node_type not in {"module", "program", "source_file"}:
            only_child = children[0]

            def normalize_cmp(value):
                if not value:
                    return ""
                return (
                    value.replace(" ", "")
                    .replace("\t", "")
                    .replace("\n", "")
                    .replace("(", "")
                    .replace(")", "")
                    .rstrip(";")
                )

            if normalize_cmp(text) == normalize_cmp(only_child.get("text", "")):
                return only_child

        punctuation_like = {'"', "'", "<", ">", "(", ")", "{", "}", "[", "]", ",", ".", ":", ";", "...", "="}
        if raw_type_l in punctuation_like and (text == "" or text == raw_type_l) and not children:
            return None
        if node_type == "" and text == "" and not children:
            return None
        if raw_type_l in parser.nodeskips and children:
            if len(children) == 1:
                return children[0]
            return {"type": "expression", "text": text, "children": children}

    return {"type": node_type, "text": text, "children": children}


def parse_variants(parser, code):
    source = str(code).encode("utf-8")
    tree = parser.parser.parse(source)
    if tree is None or tree.root_node is None:
        return {}
    original = parser.node_to_dict(tree.root_node, source)
    variants = {"Original AST": original}
    for name, _order, use_tm, use_tn, use_tc in VARIANTS[1:]:
        variants[name] = node_to_variant(parser, tree.root_node, source, use_tm, use_tn, use_tc)
    return variants


def mean(values):
    values = [float(v) for v in values if v is not None]
    return sum(values) / len(values) if values else None


def load_heval_samples(cur):
    samples = []
    for lang in HEVAL_LANGS:
        table = f"heval_{lang}"
        cur.execute(
            f"""
            SELECT id, code
            FROM {table}
            WHERE code IS NOT NULL
              AND ast_status IN (1, 2)
            ORDER BY md5(id::text)
            """
        )
        samples.extend(("HumanEval-X", lang, int(row_id), code) for row_id, code in cur.fetchall())
    return samples


def load_heval_pairs(cur):
    cur.execute(
        """
        SELECT language1, language2, func_id
        FROM heval_matrix
        ORDER BY md5(language1 || '|' || language2 || '|' || func_id::text)
        """
    )
    pair_keys = [(l1, l2, int(fid)) for l1, l2, fid in cur.fetchall()]
    grouped = defaultdict(list)
    for l1, l2, fid in pair_keys:
        grouped[l1].append(fid)
        grouped[l2].append(fid)

    codes = {}
    for lang, ids in grouped.items():
        cur.execute(
            f"""
            SELECT id, code
            FROM heval_{lang}
            WHERE id = ANY(%s)
              AND code IS NOT NULL
              AND ast_status IN (1, 2)
            """,
            (sorted(set(ids)),),
        )
        for row_id, code in cur.fetchall():
            codes[(lang, int(row_id))] = code
    return "HumanEval-X", pair_keys, codes


def load_c2c_samples(cur):
    cur.execute(
        """
        SELECT j.id, j.code, c.code
        FROM c2c_java j
        INNER JOIN c2c_cs c ON j.id = c.id
        WHERE j.code IS NOT NULL
          AND c.code IS NOT NULL
          AND j.ast_status IN (1, 2)
          AND c.ast_status IN (1, 2)
        ORDER BY md5(j.id::text)
        """,
    )
    samples = []
    pairs = []
    codes = {}
    for row_id, java_code, cs_code in cur.fetchall():
        row_id = int(row_id)
        samples.append(("Code2Code Java-C#", "java", row_id, java_code))
        samples.append(("Code2Code Java-C#", "cs", row_id, cs_code))
        pairs.append(("java", "cs", row_id))
        codes[("java", row_id)] = java_code
        codes[("cs", row_id)] = cs_code
    return samples, ("Code2Code Java-C#", pairs, codes)


def iter_c2t_samples(cur):
    for lang in C2T_LANGS:
        table = f"c2t_{lang}"
        cur.execute(
            f"""
            SELECT id, code
            FROM {table}
            WHERE code IS NOT NULL
              AND ast_status IN (1, 2)
            ORDER BY md5(id::text)
            """
        )
        for row_id, code in cur.fetchall():
            yield ("CodeXGLUE code-to-text", lang, int(row_id), code)


def build_variant_cache(samples, pair_sets):
    parsers = {}
    cache = {}
    all_items = []
    seen = set()

    for dataset, lang, row_id, code in samples:
        key = (dataset, lang, row_id)
        if key not in seen:
            all_items.append((dataset, lang, row_id, code))
            seen.add(key)

    for dataset, _pairs, codes in pair_sets:
        for lang_row, code in codes.items():
            lang, row_id = lang_row
            key = (dataset, lang, row_id)
            if key not in seen:
                all_items.append((dataset, lang, row_id, code))
                seen.add(key)

    for dataset, lang, row_id, code in all_items:
        parser = parsers.get(lang)
        if parser is None:
            parser = Myparser()
            parser.setparser(LANG_IDS[lang])
            parsers[lang] = parser
        cache[(dataset, lang, row_id)] = parse_variants(parser, code)
    return cache


def aggregate_single_metrics(samples, cache):
    acc = defaultdict(lambda: {"pec_core": [], "pec_all": [], "resr": [], "nodes": []})
    for dataset, lang, row_id, _code in samples:
        variants = cache.get((dataset, lang, row_id), {})
        original = variants.get("Original AST")
        if not original:
            continue
        for name, order, *_flags in VARIANTS:
            tree = variants.get(name)
            if not tree:
                continue
            pec = calculate_pec(original, tree, lang)
            resr = 1.0 if name == "Original AST" else ast_compression_ratio(original, tree)["compression_ratio"]
            acc[(dataset, name, order)]["pec_core"].append(pec["pec_score"])
            acc[(dataset, name, order)]["pec_all"].append(pec["pec_score_all"])
            acc[(dataset, name, order)]["resr"].append(resr)
            acc[(dataset, name, order)]["nodes"].append(count_ast_nodes(tree))
    return acc


def aggregate_pair_metrics(pair_sets, cache):
    acc = defaultdict(lambda: {"clsa": [], "pair_count": 0})
    for dataset, pairs, _codes in pair_sets:
        for lang1, lang2, row_id in pairs:
            left = cache.get((dataset, lang1, row_id), {})
            right = cache.get((dataset, lang2, row_id), {})
            for name, order, *_flags in VARIANTS:
                t1 = left.get(name)
                t2 = right.get(name)
                if not t1 or not t2:
                    continue
                sim = ted_similarity(t1, t2)
                acc[(dataset, name, order)]["clsa"].append(sim["similarity"])
                acc[(dataset, name, order)]["pair_count"] += 1
    return acc


def aggregate_c2t_single_metrics(samples):
    acc = defaultdict(lambda: {"pec_core": [], "pec_all": [], "resr": [], "nodes": []})
    parsers = {}
    for dataset, lang, row_id, code in samples:
        parser = parsers.get(lang)
        if parser is None:
            parser = Myparser()
            parser.setparser(LANG_IDS[lang])
            parsers[lang] = parser
        variants = parse_variants(parser, code)
        original = variants.get("Original AST")
        if not original:
            continue
        for name, order, *_flags in VARIANTS:
            tree = variants.get(name)
            if not tree:
                continue
            pec = calculate_pec(original, tree, lang)
            resr = 1.0 if name == "Original AST" else ast_compression_ratio(original, tree)["compression_ratio"]
            acc[(dataset, name, order)]["pec_core"].append(pec["pec_score"])
            acc[(dataset, name, order)]["pec_all"].append(pec["pec_score_all"])
            acc[(dataset, name, order)]["resr"].append(resr)
            acc[(dataset, name, order)]["nodes"].append(count_ast_nodes(tree))
    return acc


def rows_from_aggregates(single_acc, pair_acc):
    keys = sorted(set(single_acc) | set(pair_acc), key=lambda item: (item[0], item[2]))
    rows = []
    for dataset, name, order in keys:
        single = single_acc.get((dataset, name, order), {})
        pair = pair_acc.get((dataset, name, order), {})
        rows.append(
            (
                dataset,
                name,
                order,
                len(single.get("pec_core", [])),
                pair.get("pair_count", 0),
                mean(single.get("pec_core", [])),
                mean(single.get("pec_all", [])),
                mean(pair.get("clsa", [])),
                mean(single.get("resr", [])),
                mean(single.get("nodes", [])),
                Json(
                    {
                        "variant_definition": {
                            "Original AST": "raw tree-sitter AST without UAST transformation",
                            "Tm": "node-type mapping only",
                            "Tm+Tn": "node-type mapping plus text/attribute normalization",
                            "Tm+Tn+Tc": "full UAST: mapping, normalization, structural compression",
                        }.get(name),
                        "sampling": {
                            "HumanEval-X": "all available rows and pairs",
                            "Code2Code Java-C#": "all available rows and pairs",
                            "CodeXGLUE code-to-text": "all available rows without CLSA",
                            "ordering": "deterministic ORDER BY md5(...)",
                        },
                    }
                ),
            )
        )
    return rows


def store_rows(cur, rows):
    cur.execute("DELETE FROM stagewise_ablation_results")
    execute_values(
        cur,
        """
        INSERT INTO stagewise_ablation_results (
            dataset, ablation_variant, stage_order, sample_count, pair_count,
            pec_core, pec_all, clsa, resr, avg_nodes, details
        )
        VALUES %s
        """,
        rows,
        page_size=50,
    )


def main():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    ensure_table(cur)

    print("[1/5] Loading HumanEval and Code2Code samples...", flush=True)
    heval_samples = load_heval_samples(cur)
    heval_pairs = load_heval_pairs(cur)
    c2c_samples, c2c_pairs = load_c2c_samples(cur)
    samples = heval_samples + c2c_samples
    pair_sets = [heval_pairs, c2c_pairs]

    print("[2/5] Building variant cache and single-sample aggregates...", flush=True)
    cache = build_variant_cache(samples, pair_sets)
    single_acc = aggregate_single_metrics(samples, cache)

    print("[3/5] Loading CodeXGLUE code-to-text samples...", flush=True)
    c2t_acc = aggregate_c2t_single_metrics(iter_c2t_samples(cur))
    for key, value in c2t_acc.items():
        single_acc[key]["pec_core"].extend(value["pec_core"])
        single_acc[key]["pec_all"].extend(value["pec_all"])
        single_acc[key]["resr"].extend(value["resr"])
        single_acc[key]["nodes"].extend(value["nodes"])

    print("[4/5] Building pair aggregates and final rows...", flush=True)
    pair_acc = aggregate_pair_metrics(pair_sets, cache)
    rows = rows_from_aggregates(single_acc, pair_acc)

    print("[5/5] Writing results to stagewise_ablation_results...", flush=True)
    store_rows(cur, rows)
    conn.commit()

    print("[done] Stage-wise ablation results:", flush=True)
    cur.execute(
        """
        SELECT dataset, ablation_variant, sample_count, pair_count,
               round(pec_core::numeric, 4), round(pec_all::numeric, 4),
               round(clsa::numeric, 4), round(resr::numeric, 4),
               round(avg_nodes::numeric, 2)
        FROM stagewise_ablation_results
        ORDER BY dataset, stage_order
        """
    )
    for row in cur.fetchall():
        print(row)

    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
