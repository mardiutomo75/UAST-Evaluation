import json
import math
from collections import defaultdict

import psycopg2
from psycopg2.extras import Json, execute_batch
from scipy.stats import pearsonr, spearmanr
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
RETRIEVAL_METRICS = ("mrr", "recall_at_1", "recall_at_5", "mean_positive_rank")


def table_name(lang):
    return f"heval_{lang}"


def safe_corr(fn, xs, ys):
    valid = [
        (float(x), float(y))
        for x, y in zip(xs, ys)
        if x is not None
        and y is not None
        and math.isfinite(float(x))
        and math.isfinite(float(y))
    ]
    if len(valid) < 3:
        return None, None

    xvals = [x for x, _ in valid]
    yvals = [y for _, y in valid]
    if len(set(xvals)) < 2 or len(set(yvals)) < 2:
        return None, None

    stat = fn(xvals, yvals)
    return float(stat.statistic), float(stat.pvalue)


def bootstrap_ci(values, alpha=0.05):
    # Keep deterministic and dependency-light; CI for the observed query scores.
    if not values:
        return None, None
    vals = sorted(float(v) for v in values)
    n = len(vals)
    lo_idx = max(0, int((alpha / 2) * n) - 1)
    hi_idx = min(n - 1, int((1 - alpha / 2) * n) - 1)
    return vals[lo_idx], vals[hi_idx]


def load_code_rows(cur, lang):
    cur.execute(
        f"""
        SELECT id, code
        FROM {table_name(lang)}
        WHERE ast_status=1 AND code IS NOT NULL
        ORDER BY id
        """
    )
    return [(int(row_id), code or "") for row_id, code in cur.fetchall()]


def code_tfidf_scores(source_rows, target_rows):
    source_codes = [code for _, code in source_rows]
    target_codes = [code for _, code in target_rows]
    vectorizer = TfidfVectorizer(
        lowercase=True,
        token_pattern=r"(?u)\b\w+\b",
        ngram_range=(1, 2),
        min_df=1,
    )
    matrix = vectorizer.fit_transform(source_codes + target_codes)
    source_matrix = matrix[: len(source_rows)]
    target_matrix = matrix[len(source_rows):]
    sims = cosine_similarity(source_matrix, target_matrix)

    scores = {}
    for i, (source_id, _) in enumerate(source_rows):
        for j, (target_id, _) in enumerate(target_rows):
            scores[(source_id, target_id)] = float(sims[i, j])
    return scores


def load_pair_scores(cur, lang1, lang2):
    cur.execute(
        """
        SELECT func_id, ted, normal, similarity, ted2, ted3, ted4
        FROM heval_matrix
        WHERE language1=%s AND language2=%s
        """,
        (lang1, lang2),
    )
    rows = cur.fetchall()
    if not rows:
        cur.execute(
            """
            SELECT func_id, ted, normal, similarity, ted2, ted3, ted4
            FROM heval_matrix
            WHERE language1=%s AND language2=%s
            """,
            (lang2, lang1),
        )
        rows = cur.fetchall()

    # heval_matrix stores only same-task pairs. These intrinsic scores are used
    # as query-level quality signals and correlated with retrieval outcomes.
    return {
        int(func_id): {
            "clsa_ted_uast": float(ted) if ted is not None else None,
            "path_jaccard": float(normal) if normal is not None else None,
            "code_ngram_similarity": float(similarity) if similarity is not None else None,
            "ted_uast_original": float(ted2) if ted2 is not None else None,
            "ted_original_uast": float(ted3) if ted3 is not None else None,
            "ted_original_original": float(ted4) if ted4 is not None else None,
        }
        for func_id, ted, normal, similarity, ted2, ted3, ted4 in rows
    }


def evaluate_retrieval(source_rows, target_rows, scores):
    target_ids = [row_id for row_id, _ in target_rows]
    query_results = {}
    label_scores = []
    label_values = []

    for source_id, _ in source_rows:
        ranked = sorted(
            ((target_id, scores[(source_id, target_id)]) for target_id in target_ids),
            key=lambda item: item[1],
            reverse=True,
        )
        rank = next((idx for idx, (target_id, _) in enumerate(ranked, start=1) if target_id == source_id), None)
        if rank is None:
            continue

        query_results[source_id] = {
            "rank": rank,
            "mrr": 1.0 / rank,
            "recall_at_1": 1.0 if rank <= 1 else 0.0,
            "recall_at_5": 1.0 if rank <= 5 else 0.0,
            "mean_positive_rank": float(rank),
        }

        for target_id, score in ranked:
            label_scores.append(score)
            label_values.append(1.0 if target_id == source_id else 0.0)

    summary = {
        metric: sum(result[metric] for result in query_results.values()) / len(query_results)
        for metric in RETRIEVAL_METRICS
        if query_results
    }
    return query_results, summary, label_scores, label_values


def store_results(cur, rows):
    cur.execute("DELETE FROM downstream_correlation_results WHERE dataset=%s", ("HumanEval-X retrieval proxy",))
    query = """
        INSERT INTO downstream_correlation_results (
            dataset, intrinsic_metric, downstream_metric, sample_count,
            pearson_r, spearman_r, ci95_low, ci95_high, details
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    execute_batch(cur, query, rows, page_size=100)


def main():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    result_rows = []
    all_pair_summaries = []
    aggregate_by_metric = defaultdict(lambda: defaultdict(list))

    for lang1 in ACTIVE_LANGUAGES:
        source_rows = load_code_rows(cur, lang1)
        if not source_rows:
            continue

        for lang2 in ACTIVE_LANGUAGES:
            if lang1 == lang2:
                continue

            target_rows = load_code_rows(cur, lang2)
            if not target_rows:
                continue

            retrieval_scores = code_tfidf_scores(source_rows, target_rows)
            query_results, summary, label_scores, label_values = evaluate_retrieval(
                source_rows,
                target_rows,
                retrieval_scores,
            )
            if not query_results:
                continue

            intrinsic_by_task = load_pair_scores(cur, lang1, lang2)
            pair_name = f"{lang1}-{lang2}"
            all_pair_summaries.append({"pair": pair_name, **summary})

            # Baseline retrieval score versus relevance label.
            pearson_r, pearson_p = safe_corr(pearsonr, label_scores, label_values)
            spearman_r, spearman_p = safe_corr(spearmanr, label_scores, label_values)
            mrr_values = [v["mrr"] for v in query_results.values()]
            ci_low, ci_high = bootstrap_ci(mrr_values)
            result_rows.append(
                (
                    "HumanEval-X retrieval proxy",
                    "tfidf_code_similarity",
                    f"{pair_name}:relevance_label",
                    len(label_values),
                    pearson_r,
                    spearman_r,
                    ci_low,
                    ci_high,
                    Json({
                        "pair": pair_name,
                        "summary": summary,
                        "pearson_p": pearson_p,
                        "spearman_p": spearman_p,
                        "positive_pairs": len(query_results),
                        "candidate_pairs": len(label_values),
                    }),
                )
            )

            # Correlate intrinsic same-task quality with downstream query outcome.
            task_ids = sorted(set(query_results) & set(intrinsic_by_task))
            for intrinsic_metric in [
                "clsa_ted_uast",
                "path_jaccard",
                "code_ngram_similarity",
                "ted_uast_original",
                "ted_original_uast",
                "ted_original_original",
            ]:
                xs = [intrinsic_by_task[task_id].get(intrinsic_metric) for task_id in task_ids]
                for downstream_metric in RETRIEVAL_METRICS:
                    ys = [query_results[task_id][downstream_metric] for task_id in task_ids]
                    pearson_r, pearson_p = safe_corr(pearsonr, xs, ys)
                    spearman_r, spearman_p = safe_corr(spearmanr, xs, ys)
                    ci_low, ci_high = bootstrap_ci(ys)
                    result_rows.append(
                        (
                            "HumanEval-X retrieval proxy",
                            intrinsic_metric,
                            f"{pair_name}:{downstream_metric}",
                            len(task_ids),
                            pearson_r,
                            spearman_r,
                            ci_low,
                            ci_high,
                            Json({
                                "pair": pair_name,
                                "summary": summary,
                                "pearson_p": pearson_p,
                                "spearman_p": spearman_p,
                            }),
                        )
                    )
                    aggregate_by_metric[intrinsic_metric][downstream_metric].extend(
                        (x, y) for x, y in zip(xs, ys) if x is not None
                    )

    # Aggregate correlations across all directed language pairs.
    for intrinsic_metric, downstream_map in aggregate_by_metric.items():
        for downstream_metric, pairs in downstream_map.items():
            xs = [x for x, _ in pairs]
            ys = [y for _, y in pairs]
            pearson_r, pearson_p = safe_corr(pearsonr, xs, ys)
            spearman_r, spearman_p = safe_corr(spearmanr, xs, ys)
            ci_low, ci_high = bootstrap_ci(ys)
            result_rows.append(
                (
                    "HumanEval-X retrieval proxy",
                    intrinsic_metric,
                    f"ALL:{downstream_metric}",
                    len(pairs),
                    pearson_r,
                    spearman_r,
                    ci_low,
                    ci_high,
                    Json({
                        "pairs": all_pair_summaries,
                        "pearson_p": pearson_p,
                        "spearman_p": spearman_p,
                    }),
                )
            )

    store_results(cur, result_rows)
    conn.commit()
    cur.close()
    conn.close()

    print(f"stored downstream correlation rows: {len(result_rows)}")
    print("pair summaries:")
    for row in all_pair_summaries[:10]:
        print(json.dumps(row, sort_keys=True))
    if len(all_pair_summaries) > 10:
        print(f"... {len(all_pair_summaries) - 10} more pairs")


if __name__ == "__main__":
    main()
