import hashlib
import importlib.metadata as md
import json
import os
import platform
import socket
import subprocess
import sys
from pathlib import Path

import psycopg2
from psycopg2.extras import Json


DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "codesearchnet",
    "user": "postgres",
    "password": "postgres",
    "options": "-c search_path=public",
}

SCRIPT_FILES = [
    "01_prepare_db.py",
    "02_parsing_ast.py",
    "03_code2code_insert.py",
    "04_parsing_ast_c2c.py",
    "05_humaneval_insert.py",
    "06_humaneval_insert_1.py",
    "07_humaneval_parsing.py",
    "09_recalculate_pec.py",
    "10_humaneval_downstream_correlation.py",
    "11_record_experiment_metadata.py",
    "12_build_raw_measurement_audit.py",
    "13_ast_uast_downstream_retrieval.py",
    "14_clone_detection.py",
    "15_code2code_downstream_retrieval.py",
    "16_structural_retrieval.py",
    "17_code2text_retrieval_summarization.py",
    "18_intrinsic_sensitivity.py",
    "19_baseline_comparison.py",
    "20_dataset_artifact_hash.py",
    "21_baseline_comparison_full.py",
    "22_stagewise_ablation.py",
    "parserfunc.py",
    "constant.py",
    "create_table.sql",
    "README.md",
]

PACKAGES = [
    "tree-sitter",
    "tree-sitter-python",
    "tree-sitter-php",
    "tree-sitter-java",
    "tree-sitter-javascript",
    "tree-sitter-go",
    "tree-sitter-ruby",
    "tree-sitter-c-sharp",
    "tree-sitter-cpp",
    "tree-sitter-rust",
    "psycopg2-binary",
    "nltk",
    "scikit-learn",
    "scipy",
    "torch",
    "transformers",
    "fastapi",
    "pydantic",
    "uvicorn",
]


def run_command(args):
    try:
        return subprocess.check_output(args, text=True, stderr=subprocess.STDOUT).strip()
    except Exception as exc:
        return f"unavailable: {exc}"


def sha256_file(path):
    p = Path(path)
    if not p.exists():
        return None
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def package_versions():
    versions = {}
    for package in PACKAGES:
        try:
            versions[package] = md.version(package)
        except md.PackageNotFoundError:
            versions[package] = None
    return versions


def postgres_version():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute("SELECT version()")
    version = cur.fetchone()[0]
    cur.close()
    conn.close()
    return version


def hardware_info():
    return {
        "hostname": socket.gethostname(),
        "platform": platform.platform(),
        "python": sys.version.replace("\n", " "),
        "cpu": run_command(["bash", "-lc", "lscpu | sed -n '1,24p'"]),
        "memory": run_command(["bash", "-lc", "free -h"]),
        "gpu": run_command([
            "bash",
            "-lc",
            "nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader 2>/dev/null || true",
        ]),
        "postgresql": postgres_version(),
    }


def script_hashes():
    return {path: sha256_file(path) for path in SCRIPT_FILES}


def table_counts():
    tables = [
        "c2c_cs",
        "c2c_java",
        "c2t_go",
        "c2t_java",
        "c2t_javascript",
        "c2t_php",
        "c2t_python",
        "c2t_ruby",
        "heval_cpp",
        "heval_go",
        "heval_java",
        "heval_javascript",
        "heval_python",
        "heval_rust",
        "heval_matrix",
        "downstream_correlation_results",
        "raw_measurement_audit",
        "downstream_representation_results",
        "clone_detection_results",
        "code_summarization_results",
        "intrinsic_sensitivity_results",
        "baseline_comparison_results",
        "dataset_artifact_hashes",
        "stagewise_ablation_results",
    ]
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    counts = {}
    for table in tables:
        cur.execute(f"SELECT count(*) FROM {table}")
        counts[table] = cur.fetchone()[0]
    cur.close()
    conn.close()
    return counts


def insert_metadata(rows):
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute(
        """
        DELETE FROM experiment_run_metadata
        WHERE notes LIKE 'revision metadata captured on current machine%'
        """
    )
    query = """
        INSERT INTO experiment_run_metadata (
            script_name, dataset, config, environment, notes
        )
        VALUES (%s, %s, %s, %s, %s)
    """
    for row in rows:
        cur.execute(
            query,
            (
                row["script_name"],
                row["dataset"],
                Json(row["config"]),
                Json(row["environment"]),
                row["notes"],
            ),
        )
    conn.commit()
    cur.close()
    conn.close()


def main():
    environment = {
        "hardware": hardware_info(),
        "packages": package_versions(),
        "script_hashes_sha256": script_hashes(),
        "cwd": os.getcwd(),
    }
    counts = table_counts()

    shared_config = {
        "batch_size": {
            "insert": 5000,
            "ast_parsing": 500,
        },
        "max_workers": {
            "02_parsing_ast.py": 4,
            "04_parsing_ast_c2c.py": 4,
            "07_humaneval_parsing.py": "serial for HumanEval AST phase; pairwise phase serial",
        },
        "measurement": {
            "time": "time.perf_counter()",
            "memory": "tracemalloc peak bytes",
            "dtime": "AST original parse + AST dict extraction time in seconds",
            "dtime1": "total AST + UAST construction time in seconds",
            "dtime2": "UAST extra time in seconds",
            "dtime3": "time overhead percentage",
            "dmem": "AST memory peak in bytes",
            "dmem1": "total memory peak in bytes",
            "dmem2": "UAST extra memory in bytes",
            "dmem3": "memory overhead percentage",
        },
        "table_counts": counts,
    }

    rows = [
        {
            "script_name": "01_prepare_db.py",
            "dataset": "CodeXGLUE code-to-text",
            "config": {
                **shared_config,
                "purpose": "Schema initialization from create_table.sql and batch import of CodeXGLUE rows.",
            },
            "environment": environment,
            "notes": "revision metadata captured on current machine; schema import uses --init-schema explicitly because create_table.sql contains DROP statements",
        },
        {
            "script_name": "02_parsing_ast.py",
            "dataset": "CodeXGLUE code-to-text",
            "config": {
                **shared_config,
                "purpose": "AST/UAST extraction, PEC, compression, identifier preservation, and computational overhead.",
            },
            "environment": environment,
            "notes": "revision metadata captured on current machine; row claiming uses ast_status=9 and FOR UPDATE SKIP LOCKED",
        },
        {
            "script_name": "04_parsing_ast_c2c.py",
            "dataset": "Code2Code Java-C#",
            "config": {
                **shared_config,
                "purpose": "AST/UAST extraction and Java-C# pairwise structural similarity for Code2Code.",
            },
            "environment": environment,
            "notes": "revision metadata captured on current machine",
        },
        {
            "script_name": "07_humaneval_parsing.py",
            "dataset": "HumanEval-X",
            "config": {
                **shared_config,
                "purpose": "AST/UAST extraction and HumanEval cross-language pairwise metrics.",
                "active_languages": ["go", "python", "java", "javascript", "cpp", "rust"],
                "pair_generation": "updated script uses unordered language combinations for new runs",
            },
            "environment": environment,
            "notes": "revision metadata captured on current machine; current database may still contain directed pair rows from previous runs",
        },
        {
            "script_name": "10_humaneval_downstream_correlation.py",
            "dataset": "HumanEval-X retrieval proxy",
            "config": {
                **shared_config,
                "purpose": "Downstream proxy validation by cross-language retrieval and correlation with intrinsic metrics.",
                "retrieval": {
                    "query": "source-language implementation",
                    "candidates": "all target-language implementations",
                    "positive_label": "same HumanEval task id",
                    "score": "TF-IDF code cosine similarity with unigram/bigram tokens",
                    "metrics": ["MRR", "Recall@1", "Recall@5", "mean positive rank"],
                },
            },
            "environment": environment,
            "notes": "revision metadata captured on current machine",
        },
        {
            "script_name": "13_ast_uast_downstream_retrieval.py",
            "dataset": "HumanEval-X AST/UAST retrieval",
            "config": {
                **shared_config,
                "purpose": "Direct downstream retrieval comparison between flattened original AST and flattened UAST representations.",
                "retrieval": {
                    "query": "flattened AST or UAST representation from a source language",
                    "candidates": "flattened AST or UAST representations from a target language",
                    "positive_label": "same HumanEval task id",
                    "score": "TF-IDF cosine similarity over flattened representation",
                    "metrics": ["MRR", "Recall@1", "Recall@5", "mean positive rank"],
                },
            },
            "environment": environment,
            "notes": "revision metadata captured on current machine",
        },
        {
            "script_name": "14_clone_detection.py",
            "dataset": "HumanEval-X and Code2Code clone detection",
            "config": {
                **shared_config,
                "purpose": "Balanced same-task clone detection proxy using TF-IDF cosine similarity on original AST and UAST representations.",
                "retrieval": {
                    "positive_label": "same task/function id",
                    "negative_label": "different task/function id",
                    "split_strategy": "70/30 stratified calibration/test split",
                    "score": "TF-IDF cosine similarity over flattened AST/UAST representation",
                    "metrics": ["accuracy", "precision", "recall", "F1", "ROC AUC", "average precision", "balanced accuracy", "MCC"],
                },
            },
            "environment": environment,
            "notes": "revision metadata captured on current machine; negatives are formed by cyclic target shifts inside each aligned language pair",
        },
        {
            "script_name": "15_code2code_downstream_retrieval.py",
            "dataset": "Code2Code Java-C# AST/UAST retrieval",
            "config": {
                **shared_config,
                "purpose": "Direct downstream retrieval comparison for Code2Code Java-C# using flattened original AST and UAST representations.",
                "retrieval": {
                    "query": "flattened representation from source language",
                    "candidates": "flattened representation from target language",
                    "positive_label": "same function id",
                    "score": "TF-IDF cosine similarity over flattened representation",
                    "metrics": ["MRR", "Recall@1", "Recall@5", "mean positive rank"],
                },
            },
            "environment": environment,
            "notes": "revision metadata captured on current machine; retrieval is computed in both Java->C# and C#->Java directions",
        },
        {
            "script_name": "16_structural_retrieval.py",
            "dataset": "HumanEval-X and Code2Code structural retrieval",
            "config": {
                **shared_config,
                "purpose": "Structure-aware retrieval comparison using AST/UAST node, edge, root-to-leaf path, depth, and arity features.",
                "retrieval": {
                    "query": "structural feature representation from source language",
                    "candidates": "structural feature representations from target language",
                    "positive_label": "same task/function id",
                    "score": "TF-IDF cosine similarity over structural features",
                    "metrics": ["MRR", "Recall@1", "Recall@5", "mean positive rank"],
                },
            },
            "environment": environment,
            "notes": "revision metadata captured on current machine; structural retrieval is computed for HumanEval-X and Code2Code Java-C#",
        },
        {
            "script_name": "17_code2text_retrieval_summarization.py",
            "dataset": "CodeXGLUE code-to-text retrieval summarization",
            "config": {
                **shared_config,
                "purpose": "Non-neural code summarization using TF-IDF kNN docstring retrieval over original AST, UAST, and structural representations.",
                "summarization": {
                    "train_split": "train",
                    "test_split": "test",
                    "target": "docstring",
                    "method": "TF-IDF kNN docstring retrieval",
                    "representations": ["Original AST Flat", "UAST Flat", "Original AST Structural", "UAST Structural"],
                    "metrics": ["BLEU", "METEOR", "ROUGE-1", "ROUGE-L", "Exact Match"],
                },
            },
            "environment": environment,
            "notes": "revision metadata captured on current machine; default run uses deterministic subset ORDER BY md5(id::text)",
        },
        {
            "script_name": "18_intrinsic_sensitivity.py",
            "dataset": "HumanEval-X and Code2Code intrinsic sensitivity",
            "config": {
                **shared_config,
                "purpose": "Controlled degradation audit for PEC and CLSA using deterministic node-drop and type-masking corruption levels.",
                "corruption": {
                    "levels": [0.0, 0.10, 0.25, 0.50, 0.75],
                    "operator": "deterministic hash-based node-drop and type-masking",
                    "baseline": "clean stored AST/UAST",
                },
                "sampling": {
                    "pec_limit_per_table": 40,
                    "clsa_pair_limit": 20,
                },
            },
            "environment": environment,
            "notes": "revision metadata captured on current machine; corruption is deterministic per node path and severity level, not random",
        },
        {
            "script_name": "19_baseline_comparison.py",
            "dataset": "HumanEval-X and Code2Code baseline comparison",
            "config": {
                **shared_config,
                "purpose": "Compare UAST intrinsic summary with a pretrained CodeBERT raw-code cosine baseline and local intrinsic baselines.",
                "pretrained_baseline": {
                    "model": "microsoft/codebert-base",
                    "metric": "cosine similarity on mean pooled embeddings",
                    "sampling": "deterministic md5 ordering",
                },
            },
            "environment": environment,
            "notes": "revision metadata captured on current machine; pretrained baseline is sampled deterministically to keep runtime bounded",
        },
    ]

    insert_metadata(rows)
    print(json.dumps({"inserted_rows": len(rows), "table_counts": counts}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
