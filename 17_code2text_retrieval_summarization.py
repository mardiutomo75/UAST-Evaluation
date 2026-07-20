import argparse
import json
import re
from collections import Counter

import psycopg2
from nltk.translate.bleu_score import SmoothingFunction, corpus_bleu
from nltk.translate.meteor_score import single_meteor_score
from psycopg2.extras import Json, execute_batch
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import NearestNeighbors


DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "codesearchnet",
    "user": "postgres",
    "password": "postgres",
    "options": "-c search_path=public",
}

DATASET = "CodeXGLUE code-to-text retrieval summarization"
LANGUAGES = ["go", "java", "javascript", "php", "python", "ruby"]
REPRESENTATIONS = {
    "Original AST Flat": ("ast_original", "flat"),
    "UAST Flat": ("ast_unified", "flat"),
    "Original AST Structural": ("ast_original", "structural"),
    "UAST Structural": ("ast_unified", "structural"),
}


def table_name(lang):
    return f"c2t_{lang}"


def normalize_token(value):
    token = re.sub(r"\W+", "_", str(value or "").strip().lower()).strip("_")
    return token or "empty"


def tokenize_text(text):
    return re.findall(r"[A-Za-z0-9_]+", (text or "").lower())


def parse_ast(value):
    if value is None:
        return None
    if isinstance(value, dict):
        return value
    try:
        return json.loads(value)
    except Exception:
        return None


def flatten_ast_text(value):
    root = parse_ast(value)
    if not isinstance(root, dict):
        return ""

    tokens = []
    stack = [root]
    while stack:
        node = stack.pop()
        if not isinstance(node, dict):
            continue
        node_type = normalize_token(node.get("type"))
        text = normalize_token(node.get("text"))
        if node_type:
            tokens.append(f"node_{node_type}")
        if text and not node.get("children"):
            tokens.append(f"leaf_{text}")
        children = node.get("children") or []
        stack.extend(reversed(children))
    return " ".join(tokens)


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
            features.append(f"edge_{path[-1]}_{node_type}")

        if not children:
            features.append("path_" + "_".join(current_path[-7:]))

        for child in reversed(children):
            stack.append((child, current_path, depth + 1))

    return " ".join(features)


def representation_text(row, column, mode):
    value = row[column]
    if mode == "raw":
        return value or ""
    if mode == "flat":
        return flatten_ast_text(value)
    if mode == "structural":
        return structural_text(value)
    raise ValueError(f"Unknown representation mode: {mode}")


def load_split(cur, lang, split, limit):
    limit_clause = "LIMIT %s" if limit else ""
    params = [split]
    if limit:
        params.append(limit)
    cur.execute(
        f"""
        SELECT id, code, ast_original, ast_unified, docstring
        FROM {table_name(lang)}
        WHERE split=%s
          AND ast_status=1
          AND code IS NOT NULL
          AND ast_original IS NOT NULL
          AND ast_unified IS NOT NULL
          AND docstring IS NOT NULL
          AND btrim(docstring) <> ''
        ORDER BY md5(id::text)
        {limit_clause}
        """,
        params,
    )
    rows = []
    for row_id, code, ast_original, ast_unified, docstring in cur.fetchall():
        rows.append(
            {
                "id": int(row_id),
                "code": code or "",
                "ast_original": ast_original,
                "ast_unified": ast_unified,
                "docstring": docstring or "",
            }
        )
    return rows


def rouge1_f1(reference_tokens, hypothesis_tokens):
    if not reference_tokens or not hypothesis_tokens:
        return 0.0
    ref_counts = Counter(reference_tokens)
    hyp_counts = Counter(hypothesis_tokens)
    overlap = sum(min(ref_counts[token], hyp_counts[token]) for token in hyp_counts)
    if overlap == 0:
        return 0.0
    precision = overlap / len(hypothesis_tokens)
    recall = overlap / len(reference_tokens)
    return 2 * precision * recall / (precision + recall)


def lcs_len(a, b):
    if not a or not b:
        return 0
    prev = [0] * (len(b) + 1)
    for token_a in a:
        curr = [0]
        for j, token_b in enumerate(b, start=1):
            if token_a == token_b:
                curr.append(prev[j - 1] + 1)
            else:
                curr.append(max(prev[j], curr[-1]))
        prev = curr
    return prev[-1]


def rouge_l_f1(reference_tokens, hypothesis_tokens):
    if not reference_tokens or not hypothesis_tokens:
        return 0.0
    lcs = lcs_len(reference_tokens, hypothesis_tokens)
    if lcs == 0:
        return 0.0
    precision = lcs / len(hypothesis_tokens)
    recall = lcs / len(reference_tokens)
    return 2 * precision * recall / (precision + recall)


def meteor_score(reference_tokens, hypothesis_tokens):
    if not reference_tokens or not hypothesis_tokens:
        return 0.0
    return single_meteor_score(reference_tokens, hypothesis_tokens)


def evaluate_summaries(references, predictions):
    reference_tokens = [tokenize_text(text) for text in references]
    prediction_tokens = [tokenize_text(text) for text in predictions]
    pairs = [
        (ref, pred)
        for ref, pred in zip(reference_tokens, prediction_tokens)
        if ref and pred
    ]
    if not pairs:
        return None

    refs = [[ref] for ref, _ in pairs]
    hyps = [pred for _, pred in pairs]
    smoothie = SmoothingFunction().method4
    bleu = corpus_bleu(refs, hyps, weights=(0.25, 0.25, 0.25, 0.25), smoothing_function=smoothie)
    meteor = sum(meteor_score(ref, hyp) for ref, hyp in pairs) / len(pairs)
    rouge1 = sum(rouge1_f1(ref, hyp) for ref, hyp in pairs) / len(pairs)
    rougel = sum(rouge_l_f1(ref, hyp) for ref, hyp in pairs) / len(pairs)
    exact = sum(1 for ref, hyp in pairs if ref == hyp) / len(pairs)

    return {
        "evaluated_count": len(pairs),
        "bleu": bleu * 100,
        "meteor": meteor * 100,
        "rouge1": rouge1 * 100,
        "rouge_l": rougel * 100,
        "exact_match": exact * 100,
    }


def predict_docstrings(train_rows, test_rows, column, mode, k):
    train_texts = [representation_text(row, column, mode) for row in train_rows]
    test_texts = [representation_text(row, column, mode) for row in test_rows]
    train_docstrings = [row["docstring"] for row in train_rows]

    vectorizer = TfidfVectorizer(
        lowercase=True,
        token_pattern=r"(?u)\b\w+\b",
        ngram_range=(1, 2),
        min_df=1,
        sublinear_tf=True,
        max_features=100000,
    )
    train_matrix = vectorizer.fit_transform(train_texts)
    test_matrix = vectorizer.transform(test_texts)
    model = NearestNeighbors(n_neighbors=k, metric="cosine", algorithm="brute")
    model.fit(train_matrix)
    _, indices = model.kneighbors(test_matrix, return_distance=True)
    return [train_docstrings[row_indices[0]] for row_indices in indices]


def ensure_table(cur):
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS code_summarization_results (
            id BIGSERIAL PRIMARY KEY,
            created_at timestamptz DEFAULT now(),
            dataset text NOT NULL,
            language text NOT NULL,
            method text NOT NULL,
            representation text NOT NULL,
            train_count integer,
            test_count integer,
            evaluated_count integer,
            k integer,
            bleu numeric,
            meteor numeric,
            rouge1 numeric,
            rouge_l numeric,
            exact_match numeric,
            details jsonb
        )
        """
    )
    cur.execute(
        """
        CREATE INDEX IF NOT EXISTS code_summarization_lookup
            ON code_summarization_results (dataset, language, method, representation)
        """
    )


def store_results(cur, rows):
    cur.execute("DELETE FROM code_summarization_results WHERE dataset=%s", (DATASET,))
    query = """
        INSERT INTO code_summarization_results (
            dataset, language, method, representation,
            train_count, test_count, evaluated_count, k,
            bleu, meteor, rouge1, rouge_l, exact_match, details
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    execute_batch(cur, query, rows, page_size=100)


def run_experiment(args):
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    ensure_table(cur)

    result_rows = []
    languages = args.languages or LANGUAGES
    for lang in languages:
        train_rows = load_split(cur, lang, "train", args.train_limit)
        test_rows = load_split(cur, lang, "test", args.test_limit)
        if not train_rows or not test_rows:
            continue

        references = [row["docstring"] for row in test_rows]
        for representation, (column, mode) in REPRESENTATIONS.items():
            predictions = predict_docstrings(train_rows, test_rows, column, mode, args.k)
            metrics = evaluate_summaries(references, predictions)
            if metrics is None:
                continue
            result_rows.append(
                (
                    DATASET,
                    lang,
                    "TF-IDF kNN docstring retrieval",
                    representation,
                    len(train_rows),
                    len(test_rows),
                    metrics["evaluated_count"],
                    args.k,
                    metrics["bleu"],
                    metrics["meteor"],
                    metrics["rouge1"],
                    metrics["rouge_l"],
                    metrics["exact_match"],
                    Json(
                        {
                            "train_split": "train",
                            "test_split": "test",
                            "train_limit": args.train_limit,
                            "test_limit": args.test_limit,
                            "sample_order": "ORDER BY md5(id::text)",
            "meteor": "NLTK single_meteor_score; standard METEOR implementation with WordNet/stemming support when available",
                            "rouge": "local ROUGE-1/ROUGE-L F1 implementation",
                        }
                    ),
                )
            )

    store_results(cur, result_rows)
    conn.commit()

    cur.execute(
        """
        SELECT language, representation, train_count, test_count,
               round(bleu, 4), round(meteor, 4), round(rouge1, 4), round(rouge_l, 4), round(exact_match, 4)
        FROM code_summarization_results
        WHERE dataset=%s
        ORDER BY language, representation
        """,
        (DATASET,),
    )
    for row in cur.fetchall():
        print(row)

    cur.close()
    conn.close()


def parse_args():
    parser = argparse.ArgumentParser(description="Non-neural code-to-text retrieval summarization baseline.")
    parser.add_argument("--train-limit", type=int, default=5000)
    parser.add_argument("--test-limit", type=int, default=500)
    parser.add_argument("--k", type=int, default=1)
    parser.add_argument("--languages", nargs="*", choices=LANGUAGES)
    return parser.parse_args()


if __name__ == "__main__":
    run_experiment(parse_args())
