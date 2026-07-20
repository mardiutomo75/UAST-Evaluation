import json
from collections import defaultdict

import numpy as np
import psycopg2
from psycopg2.extras import Json, execute_batch
from sklearn.feature_extraction.text import TfidfVectorizer


DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "codesearchnet",
    "user": "postgres",
    "password": "postgres",
    "options": "-c search_path=public",
}

DATASET = "Code2Code Java-C# AST/UAST retrieval"
PAIR = ("java", "cs")
REPRESENTATIONS = {
    "Original AST": "ast_original",
    "UAST": "ast_unified",
}
REPRESENTATION_COLUMNS = {
    "Original AST": "ast_original",
    "UAST": "ast_unified",
}
BATCH_SIZE = 128


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


def load_aligned_rows(cur):
    cur.execute(
        """
        SELECT
            l.id,
            l.code, l.ast_original, l.ast_unified,
            r.code, r.ast_original, r.ast_unified
        FROM c2c_java l
        INNER JOIN c2c_cs r ON l.id = r.id
        WHERE l.ast_status = 2 AND r.ast_status = 2
        ORDER BY l.id
        """
    )
    rows = []
    for row in cur.fetchall():
        row_id, java_code, java_ast_original, java_ast_unified, cs_code, cs_ast_original, cs_ast_unified = row
        rows.append(
            {
                "id": int(row_id),
                "java": {
                    "code": java_code or "",
                    "ast_original": java_ast_original,
                    "ast_unified": java_ast_unified,
                },
                "cs": {
                    "code": cs_code or "",
                    "ast_original": cs_ast_original,
                    "ast_unified": cs_ast_unified,
                },
            }
        )
    return rows


def representation_text(entry, representation):
    value = entry[REPRESENTATION_COLUMNS[representation]]
    return flatten_ast_text(value)


def build_texts(aligned_rows, source_lang, target_lang, representation):
    source_rows = []
    target_rows = []
    for row in aligned_rows:
        source_rows.append((row["id"], representation_text(row[source_lang], representation)))
        target_rows.append((row["id"], representation_text(row[target_lang], representation)))
    return source_rows, target_rows


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

    return {
        "sample_count": len(ranks),
        "mrr": sum(1.0 / rank for rank in ranks) / len(ranks),
        "recall_at_1": sum(1 for rank in ranks if rank <= 1) / len(ranks),
        "recall_at_5": sum(1 for rank in ranks if rank <= 5) / len(ranks),
        "mean_positive_rank": sum(ranks) / len(ranks),
        "median_positive_rank": sorted(ranks)[len(ranks) // 2],
    }


def store_rows(cur, rows):
    cur.execute("DELETE FROM downstream_representation_results WHERE dataset=%s", (DATASET,))
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

    aligned_rows = load_aligned_rows(cur)
    rows = []
    aggregate = defaultdict(list)

    for representation in REPRESENTATIONS:
        for source_lang, target_lang in [(PAIR[0], PAIR[1]), (PAIR[1], PAIR[0])]:
            source_rows, target_rows = build_texts(aligned_rows, source_lang, target_lang, representation)
            metrics = retrieval_metrics(source_rows, target_rows)
            if metrics is None:
                continue
            aggregate[representation].append(metrics)
            rows.append(
                (
                    DATASET,
                    source_lang,
                    target_lang,
                    representation,
                    metrics["sample_count"],
                    metrics["mrr"],
                    metrics["recall_at_1"],
                    metrics["recall_at_5"],
                    metrics["mean_positive_rank"],
                    metrics["median_positive_rank"],
                    Json({
                        "scoring": "TF-IDF cosine over flattened representation",
                        "pair_type": "aligned same-id cross-language retrieval",
                    }),
                )
            )

    for representation, values in aggregate.items():
        if not values:
            continue
        rows.append(
            (
                DATASET,
                "ALL",
                "ALL",
                representation,
                sum(v["sample_count"] for v in values),
                sum(v["mrr"] for v in values) / len(values),
                sum(v["recall_at_1"] for v in values) / len(values),
                sum(v["recall_at_5"] for v in values) / len(values),
                sum(v["mean_positive_rank"] for v in values) / len(values),
                None,
                Json({"directed_language_pairs": len(values), "aggregation": "macro-average over directed language pairs"}),
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
        (DATASET,),
    )
    for row in cur.fetchall():
        print(row)

    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
