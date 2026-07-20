import hashlib
import json
from pathlib import Path

import psycopg2
from psycopg2.extras import Json, execute_values


DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "codesearchnet",
    "user": "postgres",
    "password": "postgres",
    "options": "-c search_path=public",
}

BASE_DIR = Path(__file__).resolve().parent.parent
DATASET_ROOTS = [
    ("dataset", "CodeXGLUE code-to-text", BASE_DIR / "disertasi_datasets" / "codexglue"),
    ("dataset", "HumanEval-X", BASE_DIR / "disertasi_datasets" / "humaneval-x"),
]
ARTIFACT_ROOTS = [
    ("artifact", "raw_measurements", BASE_DIR / "dataset_prep" / "revision_artifacts" / "raw_measurements"),
    ("artifact", "baseline_comparison.csv", BASE_DIR / "dataset_prep" / "revision_artifacts" / "baseline_comparison.csv"),
]
FILE_ARTIFACTS = [
    ("rules", "constant.py", BASE_DIR / "dataset_preparation" / "constant.py"),
    ("rules", "parserfunc.py", BASE_DIR / "dataset_preparation" / "parserfunc.py"),
    ("rules", "create_table.sql", BASE_DIR / "dataset_preparation" / "create_table.sql"),
    ("script", "11_record_experiment_metadata.py", BASE_DIR / "dataset_preparation" / "11_record_experiment_metadata.py"),
    ("script", "18_intrinsic_sensitivity.py", BASE_DIR / "dataset_preparation" / "18_intrinsic_sensitivity.py"),
    ("script", "19_baseline_comparison.py", BASE_DIR / "dataset_preparation" / "19_baseline_comparison.py"),
    ("script", "20_dataset_artifact_hash.py", BASE_DIR / "dataset_preparation" / "20_dataset_artifact_hash.py"),
]


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def sha256_file(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def is_hidden(path):
    return any(part.startswith(".") for part in path.parts)


def collect_directory_manifest(root):
    root = Path(root)
    files = []
    total_bytes = 0
    for path in sorted(p for p in root.rglob("*") if p.is_file() and not is_hidden(p.relative_to(root))):
        rel = path.relative_to(root).as_posix()
        size = path.stat().st_size
        file_hash = sha256_file(path)
        total_bytes += size
        files.append(
            {
                "path": rel,
                "size": size,
                "sha256": file_hash,
            }
        )

    manifest_lines = [
        f"{item['path']}\t{item['size']}\t{item['sha256']}\n"
        for item in files
    ]
    manifest_hash = sha256_bytes("".join(manifest_lines).encode("utf-8"))
    return manifest_hash, len(files), total_bytes, files


def collect_file_manifest(path):
    path = Path(path)
    file_hash = sha256_file(path)
    size = path.stat().st_size
    return file_hash, 1, size, [{"path": path.name, "size": size, "sha256": file_hash}]


def ensure_table(cur):
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS dataset_artifact_hashes (
            id BIGSERIAL PRIMARY KEY,
            created_at timestamptz DEFAULT now(),
            artifact_type text NOT NULL,
            artifact_name text NOT NULL,
            artifact_path text NOT NULL,
            sha256 text NOT NULL,
            file_count integer,
            total_bytes bigint,
            details jsonb
        )
        """
    )


def build_rows():
    rows = []

    for artifact_type, artifact_name, path in DATASET_ROOTS + ARTIFACT_ROOTS:
        if not path.exists():
            continue
        if path.is_dir():
            digest, file_count, total_bytes, files = collect_directory_manifest(path)
        else:
            digest, file_count, total_bytes, files = collect_file_manifest(path)
        rows.append(
            (
                artifact_type,
                artifact_name,
                str(path),
                digest,
                file_count,
                total_bytes,
                Json(
                    {
                        "kind": "directory" if path.is_dir() else "file",
                        "root": str(path),
                        "files": files,
                        "algorithm": "sha256(path\\tsize\\tsha256(file)) over sorted relative paths",
                        "excluded_hidden": True,
                    }
                ),
            )
        )

    for artifact_type, artifact_name, path in FILE_ARTIFACTS:
        if not path.exists():
            continue
        digest, file_count, total_bytes, files = collect_file_manifest(path)
        rows.append(
            (
                artifact_type,
                artifact_name,
                str(path),
                digest,
                file_count,
                total_bytes,
                Json(
                    {
                        "kind": "file",
                        "root": str(path),
                        "files": files,
                        "algorithm": "sha256(file bytes)",
                    }
                ),
            )
        )

    return rows


def main():
    rows = build_rows()
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    ensure_table(cur)
    cur.execute("TRUNCATE dataset_artifact_hashes RESTART IDENTITY")
    execute_values(
        cur,
        """
        INSERT INTO dataset_artifact_hashes (
            artifact_type, artifact_name, artifact_path,
            sha256, file_count, total_bytes, details
        )
        VALUES %s
        """,
        rows,
        page_size=20,
    )
    conn.commit()
    cur.close()
    conn.close()
    print(f"dataset_artifact_hashes rows: {len(rows)}")


if __name__ == "__main__":
    main()
