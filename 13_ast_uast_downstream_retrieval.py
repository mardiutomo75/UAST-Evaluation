import json
from collections import defaultdict

import psycopg2
from psycopg2.extras import Json, execute_batch
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from constant import languages


DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "codesearchnet",
    "user": "postgres",
    "password": "postgres",
    "options": "-c search_path=public",
}

ACTIVE_LANGUAGES = [lang for lang in languages if lang not in ("php", "cs", "ruby")]
REPRESENTATIONS = {
    "Original AST": "ast_original",
    "UAST": "ast_unified",
}


def table_name(lang):
    return f"heval_{lang}"


def flatten_ast_text(value):
    if value is None:
        return ""
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except Exception:
            return value

    tokens = []
    stack = [value]
    while stack:
        node = stack.pop()
        if not isinstance(node, dict):
            continue
        node_type = str(node.get("type", "") or "").strip()
        text = str(node.get("text", "") or "").strip()
        if node_type:
            tokens.append(node_type)
        if text and not node.get("children"):
            tokens.append(text)
        children = node.get("children", []) or []
        stack.extend(reversed(children))
    return " ".join(tokens)


def load_representations(cur, lang, column):
    cur.execute(
        f"""
        SELECT id, {column}
        FROM {table_name(lang)}
        WHERE ast_status=1
          AND {column} IS NOT NULL
        ORDER BY id
        """
    )
    return [(int(row_id), flatten_ast_text(value)) for row_id, value in cur.fetchall()]


def retrieval_metrics(source_rows, target_rows):
    source_texts = [text for _, text in source_rows]
    target_texts = [text for _, text in target_rows]
    if not source_texts or not target_texts:
        return None

    vectorizer = TfidfVectorizer(
        lowercase=True,
        token_pattern=r"(?u)\b\w+\b",
        ngram_range=(1, 2),
        min_df=1,
    )
    matrix = vectorizer.fit_transform(source_texts + target_texts)
    source_matrix = matrix[: len(source_rows)]
    target_matrix = matrix[len(source_rows):]
    sims = cosine_similarity(source_matrix, target_matrix)

    target_ids = [row_id for row_id, _ in target_rows]
    ranks = []
    for i, (source_id, _) in enumerate(source_rows):
        ranked_indices = sorted(range(len(target_ids)), key=lambda j: sims[i, j], reverse=True)
        rank = next(
            (pos for pos, j in enumerate(ranked_indices, start=1) if target_ids[j] == source_id),
            None,
        )
        if rank is not None:
            ranks.append(rank)

    if not ranks:
        return None

    return {
        "sample_count": len(ranks),
        "mrr": sum(1.0 / rank for rank in ranks) / len(ranks),
        "recall_at_1": sum(1 for rank in ranks if rank <= 1) / len(ranks),
        "recall_at_5": sum(1 for rank in ranks if rank <= 5) / len(ranks),
        "mean_positive_rank": sum(ranks) / len(ranks),
        "median_positive_rank": sorted(ranks)[len(ranks) // 2],
    }


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


def store_rows(cur, rows):
    cur.execute("DELETE FROM downstream_representation_results WHERE dataset=%s", ("HumanEval-X AST/UAST retrieval",))
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
    aggregate = defaultdict(list)

    cache = {}
    for representation, column in REPRESENTATIONS.items():
        for lang in ACTIVE_LANGUAGES:
            cache[(representation, lang)] = load_representations(cur, lang, column)

    for representation in REPRESENTATIONS:
        for lang1 in ACTIVE_LANGUAGES:
            for lang2 in ACTIVE_LANGUAGES:
                if lang1 == lang2:
                    continue
                metrics = retrieval_metrics(
                    cache[(representation, lang1)],
                    cache[(representation, lang2)],
                )
                if metrics is None:
                    continue
                aggregate[representation].append(metrics)
                rows.append(
                    (
                        "HumanEval-X AST/UAST retrieval",
                        lang1,
                        lang2,
                        representation,
                        metrics["sample_count"],
                        metrics["mrr"],
                        metrics["recall_at_1"],
                        metrics["recall_at_5"],
                        metrics["mean_positive_rank"],
                        metrics["median_positive_rank"],
                        Json({"scoring": "TF-IDF cosine over flattened representation"}),
                    )
                )

    for representation, values in aggregate.items():
        if not values:
            continue
        n_pairs = len(values)
        sample_count = sum(v["sample_count"] for v in values)
        rows.append(
            (
                "HumanEval-X AST/UAST retrieval",
                "ALL",
                "ALL",
                representation,
                sample_count,
                sum(v["mrr"] for v in values) / n_pairs,
                sum(v["recall_at_1"] for v in values) / n_pairs,
                sum(v["recall_at_5"] for v in values) / n_pairs,
                sum(v["mean_positive_rank"] for v in values) / n_pairs,
                None,
                Json({"directed_language_pairs": n_pairs, "aggregation": "macro-average over directed language pairs"}),
            )
        )

    store_rows(cur, rows)
    conn.commit()

    cur.execute(
        """
        SELECT representation, sample_count, mrr, recall_at_1, recall_at_5, mean_positive_rank
        FROM downstream_representation_results
        WHERE dataset=%s AND language1='ALL' AND language2='ALL'
        ORDER BY representation
        """,
        ("HumanEval-X AST/UAST retrieval",),
    )
    for row in cur.fetchall():
        print(row)

    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
