import json
import re
from collections import defaultdict

import numpy as np
import psycopg2
from psycopg2.extras import Json, execute_batch
from sklearn.feature_extraction.text import TfidfVectorizer

from constant import languages


DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "codesearchnet",
    "user": "postgres",
    "password": "postgres",
    "options": "-c search_path=public",
}

BATCH_SIZE = 128
ACTIVE_HEVAL_LANGUAGES = [lang for lang in languages if lang not in ("php", "cs", "ruby")]
REPRESENTATIONS = {
    "Original AST Structural": "ast_original",
    "UAST Structural": "ast_unified",
}


def normalize_token(value):
    token = re.sub(r"\W+", "_", str(value or "").strip().lower()).strip("_")
    return token or "empty"


def parse_ast(value):
    if value is None:
        return None
    if isinstance(value, dict):
        return value
    try:
        return json.loads(value)
    except Exception:
        return None


def structural_text(value):
    root = parse_ast(value)
    if not isinstance(root, dict):
        return ""

    features = []
    stack = [(root, [], 0)]
    while stack:
        node, path, depth = stack.pop()
        if not isinstance(node, dict):
            continue

        node_type = normalize_token(node.get("type"))
        children = [child for child in (node.get("children") or []) if isinstance(child, dict)]
        current_path = path + [node_type]

        features.append(f"node_{node_type}")
        features.append(f"depth_{min(depth, 8)}_{node_type}")
        features.append(f"arity_{node_type}_{min(len(children), 8)}")

        if path:
            parent_type = path[-1]
            features.append(f"edge_{parent_type}_{node_type}")

        if not children:
            compact_path = current_path[-7:]
            features.append("path_" + "_".join(compact_path))

        for child in reversed(children):
            stack.append((child, current_path, depth + 1))

    return " ".join(features)


def ensure_table(cur):
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS downstream_representation_results (
            id BIGSERIAL PRIMARY KEY,
            created_at timestamptz DEFAULT now(),
            dataset text NOT NULL,
            language1 text NOT NULL,
            language2 text NOT NULL,
            representation text NOT NULL,
            sample_count integer,
            mrr numeric,
            recall_at_1 numeric,
            recall_at_5 numeric,
            mean_positive_rank numeric,
            median_positive_rank numeric,
            details jsonb
        )
        """
    )


def retrieval_metrics(source_rows, target_rows):
    source_texts = [text for _, text in source_rows]
    target_texts = [text for _, text in target_rows]
    if not source_texts or not target_texts:
        return None

    vectorizer = TfidfVectorizer(
        lowercase=False,
        token_pattern=r"(?u)\b\w+\b",
        ngram_range=(1, 1),
        min_df=1,
        sublinear_tf=True,
    )
    matrix = vectorizer.fit_transform(source_texts + target_texts)
    source_matrix = matrix[: len(source_rows)]
    target_matrix = matrix[len(source_rows):]
    target_ids = [row_id for row_id, _ in target_rows]
    target_index = {row_id: idx for idx, row_id in enumerate(target_ids)}

    ranks = []
    for start in range(0, len(source_rows), BATCH_SIZE):
        stop = min(start + BATCH_SIZE, len(source_rows))
        sims = (source_matrix[start:stop] @ target_matrix.T).toarray()
        for offset, (source_id, _) in enumerate(source_rows[start:stop]):
            pos_idx = target_index[source_id]
            row = sims[offset]
            pos_score = row[pos_idx]
            rank = int(np.sum(row > pos_score)) + 1
            ranks.append(rank)

    if not ranks:
        return None

    sorted_ranks = sorted(ranks)
    return {
        "sample_count": len(ranks),
        "mrr": sum(1.0 / rank for rank in ranks) / len(ranks),
        "recall_at_1": sum(1 for rank in ranks if rank <= 1) / len(ranks),
        "recall_at_5": sum(1 for rank in ranks if rank <= 5) / len(ranks),
        "mean_positive_rank": sum(ranks) / len(ranks),
        "median_positive_rank": sorted_ranks[len(sorted_ranks) // 2],
    }


def heval_table(lang):
    return f"heval_{lang}"


def load_heval(cur, lang, column):
    cur.execute(
        f"""
        SELECT id, {column}
        FROM {heval_table(lang)}
        WHERE ast_status=1 AND {column} IS NOT NULL
        ORDER BY id
        """
    )
    return [(int(row_id), structural_text(value)) for row_id, value in cur.fetchall()]


def load_code2code(cur, source_lang, target_lang, column):
    cur.execute(
        f"""
        SELECT l.id, l.{column}, r.{column}
        FROM c2c_{source_lang} l
        INNER JOIN c2c_{target_lang} r ON l.id = r.id
        WHERE l.ast_status=2 AND r.ast_status=2
          AND l.{column} IS NOT NULL
          AND r.{column} IS NOT NULL
        ORDER BY l.id
        """
    )
    source_rows = []
    target_rows = []
    for row_id, source_value, target_value in cur.fetchall():
        source_rows.append((int(row_id), structural_text(source_value)))
        target_rows.append((int(row_id), structural_text(target_value)))
    return source_rows, target_rows


def result_row(dataset, lang1, lang2, representation, metrics, details):
    return (
        dataset,
        lang1,
        lang2,
        representation,
        metrics["sample_count"],
        metrics["mrr"],
        metrics["recall_at_1"],
        metrics["recall_at_5"],
        metrics["mean_positive_rank"],
        metrics["median_positive_rank"],
        Json(details),
    )


def build_heval_rows(cur):
    dataset = "HumanEval-X structural retrieval"
    rows = []
    aggregate = defaultdict(list)
    cache = {}

    for representation, column in REPRESENTATIONS.items():
        for lang in ACTIVE_HEVAL_LANGUAGES:
            cache[(representation, lang)] = load_heval(cur, lang, column)

    for representation in REPRESENTATIONS:
        for lang1 in ACTIVE_HEVAL_LANGUAGES:
            for lang2 in ACTIVE_HEVAL_LANGUAGES:
                if lang1 == lang2:
                    continue
                metrics = retrieval_metrics(cache[(representation, lang1)], cache[(representation, lang2)])
                if metrics is None:
                    continue
                aggregate[representation].append(metrics)
                rows.append(
                    result_row(
                        dataset,
                        lang1,
                        lang2,
                        representation,
                        metrics,
                        {
                            "scoring": "TF-IDF cosine over structural node/edge/path/depth features",
                            "feature_types": ["node", "edge", "root_to_leaf_path", "depth_bucket", "arity"],
                        },
                    )
                )

    rows.extend(build_aggregate_rows(dataset, aggregate))
    return rows


def build_code2code_rows(cur):
    dataset = "Code2Code Java-C# structural retrieval"
    rows = []
    aggregate = defaultdict(list)

    for representation, column in REPRESENTATIONS.items():
        for source_lang, target_lang in [("java", "cs"), ("cs", "java")]:
            source_rows, target_rows = load_code2code(cur, source_lang, target_lang, column)
            metrics = retrieval_metrics(source_rows, target_rows)
            if metrics is None:
                continue
            aggregate[representation].append(metrics)
            rows.append(
                result_row(
                    dataset,
                    source_lang,
                    target_lang,
                    representation,
                    metrics,
                    {
                        "scoring": "TF-IDF cosine over structural node/edge/path/depth features",
                        "feature_types": ["node", "edge", "root_to_leaf_path", "depth_bucket", "arity"],
                    },
                )
            )

    rows.extend(build_aggregate_rows(dataset, aggregate))
    return rows


def build_aggregate_rows(dataset, aggregate):
    rows = []
    for representation, values in aggregate.items():
        if not values:
            continue
        metrics = {
            "sample_count": sum(v["sample_count"] for v in values),
            "mrr": sum(v["mrr"] for v in values) / len(values),
            "recall_at_1": sum(v["recall_at_1"] for v in values) / len(values),
            "recall_at_5": sum(v["recall_at_5"] for v in values) / len(values),
            "mean_positive_rank": sum(v["mean_positive_rank"] for v in values) / len(values),
            "median_positive_rank": None,
        }
        rows.append(
            (
                dataset,
                "ALL",
                "ALL",
                representation,
                metrics["sample_count"],
                metrics["mrr"],
                metrics["recall_at_1"],
                metrics["recall_at_5"],
                metrics["mean_positive_rank"],
                metrics["median_positive_rank"],
                Json({"directed_language_pairs": len(values), "aggregation": "macro-average over directed language pairs"}),
            )
        )
    return rows


def store_rows(cur, rows):
    cur.execute(
        """
        DELETE FROM downstream_representation_results
        WHERE dataset IN (%s, %s)
        """,
        ("HumanEval-X structural retrieval", "Code2Code Java-C# structural retrieval"),
    )
    query = """
        INSERT INTO downstream_representation_results (
            dataset, language1, language2, representation, sample_count,
            mrr, recall_at_1, recall_at_5, mean_positive_rank, median_positive_rank,
            details
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    execute_batch(cur, query, rows, page_size=100)


def main():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    ensure_table(cur)

    rows = []
    rows.extend(build_heval_rows(cur))
    rows.extend(build_code2code_rows(cur))
    store_rows(cur, rows)
    conn.commit()

    cur.execute(
        """
        SELECT dataset, representation, sample_count, mrr, recall_at_1, recall_at_5, mean_positive_rank
        FROM downstream_representation_results
        WHERE dataset IN (%s, %s)
          AND language1='ALL'
          AND language2='ALL'
        ORDER BY dataset, representation
        """,
        ("HumanEval-X structural retrieval", "Code2Code Java-C# structural retrieval"),
    )
    for row in cur.fetchall():
        print(row)

    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
