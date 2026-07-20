import json
import random
from dataclasses import dataclass

import psycopg2
from psycopg2.extras import Json, execute_batch
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    balanced_accuracy_score,
    f1_score,
    matthews_corrcoef,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.model_selection import train_test_split

from constant import languages


DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "codesearchnet",
    "user": "postgres",
    "password": "postgres",
    "options": "-c search_path=public",
}

ACTIVE_HEVAL_LANGUAGES = [lang for lang in languages if lang not in ("php", "cs", "ruby")]
REPRESENTATIONS = {
    "Original AST": "ast_original",
    "UAST": "ast_unified",
}

BATCH_SIZE = 100
TEST_RATIO = 0.30
SEED = 42


@dataclass(frozen=True)
class PairConfig:
    dataset: str
    left_table: str
    right_table: str
    left_language: str
    right_language: str
    split_filter: str | None
    ast_status: int


PAIR_CONFIGS = [
    PairConfig(
        dataset="Code2Code Java-C# clone detection",
        left_table="c2c_java",
        right_table="c2c_cs",
        left_language="java",
        right_language="cs",
        split_filter="test",
        ast_status=2,
    ),
]


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


def load_aligned_pairs(cur, left_table, right_table, column, ast_status, split_filter=None):
    where_clauses = [
        f"l.ast_status = {ast_status}",
        f"r.ast_status = {ast_status}",
        f"l.{column} IS NOT NULL",
        f"r.{column} IS NOT NULL",
    ]
    params = []
    if split_filter is not None:
        where_clauses.append("l.split = %s")
        where_clauses.append("r.split = %s")
        params.extend([split_filter, split_filter])

    query = f"""
        SELECT l.id, l.{column}, r.{column}
        FROM {left_table} l
        INNER JOIN {right_table} r ON l.id = r.id
        WHERE {' AND '.join(where_clauses)}
        ORDER BY l.id
    """
    cur.execute(query, params)
    rows = cur.fetchall()
    aligned = []
    for row_id, left_value, right_value in rows:
        aligned.append(
            {
                "id": int(row_id),
                "left": left_value,
                "right": right_value,
            }
        )
    return aligned


def make_examples(aligned_rows, representation):
    positives = []
    negatives = []

    right_values = [row["right"] for row in aligned_rows]
    shifted_right_values = right_values[1:] + right_values[:1]

    for row, shifted_right in zip(aligned_rows, shifted_right_values):
        left_text = flatten_ast_text(row["left"])
        right_text = flatten_ast_text(row["right"])
        negative_right_text = flatten_ast_text(shifted_right)
        positives.append((1, left_text, right_text))
        negatives.append((0, left_text, negative_right_text))

    return positives + negatives


def pair_similarity_scores(examples):
    source_texts = [source for _, source, _ in examples]
    target_texts = [target for _, _, target in examples]
    if not source_texts or not target_texts:
        return []

    vectorizer = TfidfVectorizer(
        lowercase=True,
        token_pattern=r"(?u)\b\w+\b",
        ngram_range=(1, 2),
        min_df=1,
    )
    matrix = vectorizer.fit_transform(source_texts + target_texts)
    source_matrix = matrix[: len(examples)]
    target_matrix = matrix[len(examples):]
    sims = cosine_similarity(source_matrix, target_matrix)
    return [float(sims[i, i]) for i in range(len(examples))]


def choose_threshold(labels, scores):
    if len(set(labels)) < 2:
        return 0.5
    fpr, tpr, thresholds = roc_curve(labels, scores)
    if len(thresholds) == 0:
        return 0.5
    best_idx = 1
    best_score = tpr[1] - fpr[1]
    for idx in range(2, len(thresholds)):
        j_stat = tpr[idx] - fpr[idx]
        if j_stat > best_score:
            best_score = j_stat
            best_idx = idx
    return float(thresholds[best_idx])


def evaluate_binary(labels, scores, threshold):
    preds = [1 if score >= threshold else 0 for score in scores]
    result = {
        "accuracy": accuracy_score(labels, preds),
        "precision": precision_score(labels, preds, zero_division=0),
        "recall": recall_score(labels, preds, zero_division=0),
        "f1": f1_score(labels, preds, zero_division=0),
        "balanced_accuracy": balanced_accuracy_score(labels, preds),
        "mcc": matthews_corrcoef(labels, preds),
    }
    if len(set(labels)) >= 2:
        result["roc_auc"] = roc_auc_score(labels, scores)
        result["average_precision"] = average_precision_score(labels, scores)
    else:
        result["roc_auc"] = None
        result["average_precision"] = None
    return result


def evaluate_examples(examples):
    labels = [label for label, _, _ in examples]
    scores = pair_similarity_scores(examples)
    if not scores:
        return None

    indices = list(range(len(labels)))
    train_idx, test_idx = train_test_split(
        indices,
        test_size=TEST_RATIO,
        random_state=SEED,
        stratify=labels,
    )
    cal_labels = [labels[i] for i in train_idx]
    cal_scores = [scores[i] for i in train_idx]
    test_labels = [labels[i] for i in test_idx]
    test_scores = [scores[i] for i in test_idx]

    threshold = choose_threshold(cal_labels, cal_scores)
    metrics = evaluate_binary(test_labels, test_scores, threshold)
    metrics.update(
        {
            "threshold": threshold,
            "calibration_count": len(train_idx),
            "test_count": len(test_idx),
            "positive_count": sum(labels),
            "negative_count": len(labels) - sum(labels),
            "total_count": len(labels),
            "mean_score_positive": sum(score for label, score in zip(labels, scores) if label == 1) / max(1, sum(labels)),
            "mean_score_negative": sum(score for label, score in zip(labels, scores) if label == 0) / max(1, len(labels) - sum(labels)),
        }
    )
    return metrics


def ensure_table(cur):
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS clone_detection_results (
            id BIGSERIAL PRIMARY KEY,
            created_at timestamptz DEFAULT now(),
            dataset text NOT NULL,
            language1 text NOT NULL,
            language2 text NOT NULL,
            representation text NOT NULL,
            positive_count integer,
            negative_count integer,
            total_count integer,
            calibration_count integer,
            test_count integer,
            threshold numeric,
            accuracy numeric,
            precision numeric,
            recall numeric,
            f1 numeric,
            roc_auc numeric,
            average_precision numeric,
            balanced_accuracy numeric,
            mcc numeric,
            details jsonb
        )
        """
    )
    cur.execute(
        """
        CREATE INDEX IF NOT EXISTS clone_detection_lookup
            ON clone_detection_results (dataset, representation, language1, language2)
        """
    )


def store_rows(cur, rows):
    cur.execute("DELETE FROM clone_detection_results")
    query = """
        INSERT INTO clone_detection_results (
            dataset, language1, language2, representation,
            positive_count, negative_count, total_count, calibration_count, test_count,
            threshold, accuracy, precision, recall, f1, roc_auc, average_precision,
            balanced_accuracy, mcc, details
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    execute_batch(cur, query, rows, page_size=BATCH_SIZE)


def build_aggregate_rows(rows):
    aggregates = {}
    for row in rows:
        key = (row[0], row[3])
        aggregates.setdefault(key, []).append(row)

    result = []
    for (dataset, representation), items in aggregates.items():
        metric_fields = [
            "accuracy",
            "precision",
            "recall",
            "f1",
            "roc_auc",
            "average_precision",
            "balanced_accuracy",
            "mcc",
        ]
        avg_metrics = {}
        for field in metric_fields:
            values = [item[10 + metric_fields.index(field)] for item in items if item[10 + metric_fields.index(field)] is not None]
            avg_metrics[field] = sum(values) / len(values) if values else None

        total_positive = sum(item[4] for item in items)
        total_negative = sum(item[5] for item in items)
        total_count = sum(item[6] for item in items)
        total_calibration = sum(item[7] for item in items)
        total_test = sum(item[8] for item in items)

        result.append(
            (
                dataset,
                "ALL",
                "ALL",
                representation,
                total_positive,
                total_negative,
                total_count,
                total_calibration,
                total_test,
                None,
                avg_metrics["accuracy"],
                avg_metrics["precision"],
                avg_metrics["recall"],
                avg_metrics["f1"],
                avg_metrics["roc_auc"],
                avg_metrics["average_precision"],
                avg_metrics["balanced_accuracy"],
                avg_metrics["mcc"],
                Json(
                    {
                        "aggregation": "macro-average over language pairs",
                        "pair_count": len(items),
                    }
                ),
            )
        )
    return result


def process_pair(cur, config):
    rows = {}
    for representation, column in REPRESENTATIONS.items():
        aligned = load_aligned_pairs(
            cur,
            config.left_table,
            config.right_table,
            column,
            config.ast_status,
            config.split_filter,
        )
        if len(aligned) < 2:
            continue
        examples = make_examples(aligned, representation)
        metrics = evaluate_examples(examples)
        if metrics is None:
            continue
        rows[(representation, config.left_language, config.right_language)] = (
            config.dataset,
            config.left_language,
            config.right_language,
            representation,
            metrics["positive_count"],
            metrics["negative_count"],
            metrics["total_count"],
            metrics["calibration_count"],
            metrics["test_count"],
            metrics["threshold"],
            metrics["accuracy"],
            metrics["precision"],
            metrics["recall"],
            metrics["f1"],
            metrics["roc_auc"],
            metrics["average_precision"],
            metrics["balanced_accuracy"],
            metrics["mcc"],
            Json(
                {
                    "split_filter": config.split_filter,
                    "ast_status": config.ast_status,
                    "strategy": "positive pairs use matching ids; negatives use cyclic shifted targets",
                    "calibration_ratio": 1 - TEST_RATIO,
                    "seed": SEED,
                    "mean_score_positive": metrics["mean_score_positive"],
                    "mean_score_negative": metrics["mean_score_negative"],
                }
            ),
        )
    return list(rows.values())


def process_heval(cur):
    pair_configs = []
    for i, lang1 in enumerate(ACTIVE_HEVAL_LANGUAGES):
        for lang2 in ACTIVE_HEVAL_LANGUAGES[i + 1:]:
            pair_configs.append(
                PairConfig(
                    dataset="HumanEval-X clone detection",
                    left_table=f"heval_{lang1}",
                    right_table=f"heval_{lang2}",
                    left_language=lang1,
                    right_language=lang2,
                    split_filter="humaneval",
                    ast_status=1,
                )
            )

    rows = []
    for config in pair_configs:
        rows.extend(process_pair(cur, config))
    return rows


def process_c2c(cur):
    rows = []
    for config in PAIR_CONFIGS:
        rows.extend(process_pair(cur, config))
    return rows


def main():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    ensure_table(cur)

    rows = []
    rows.extend(process_c2c(cur))
    rows.extend(process_heval(cur))
    rows.extend(build_aggregate_rows(rows))

    store_rows(cur, rows)
    conn.commit()

    cur.execute(
        """
        SELECT dataset, representation, language1, language2, positive_count, total_count, accuracy, precision, recall, f1, roc_auc
        FROM clone_detection_results
        ORDER BY dataset, representation, language1, language2
        """
    )
    for row in cur.fetchall():
        print(row)

    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
