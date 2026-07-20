import json
import psycopg2
from psycopg2.extras import execute_values
from pathlib import Path

# ---------- KONFIGURASI DB ----------
DB_CONFIG = {
    "host": "localhost",
    "dbname": "codesearchnet",
    "user": "postgres",
    "password": "postgres",
    "port": 5432,
}

# ---------- FILE PER BAHASA ----------
DATASETS = {
    "python": "./python/humaneval_python.jsonl",
    "java": "./java/humaneval_java.jsonl",
    "cpp":  "./cpp/humaneval_cpp.jsonl",
    "javascript": "./javascript/humaneval_javascript.jsonl",
    "rust": "./rust/humaneval_rust.jsonl",
    "go": "./go/humaneval_go.jsonl",
}
BASE_DIR = Path("../disertasi_datasets/humaneval-x")

SPLIT_VALUE = "humaneval"     # konstan (karena tidak ada split di file)
CODE_TOKENS_VALUE = "test"    # konstan sesuai permintaan
BATCH_SIZE = 1000

def clean_text(x):
    if x is None:
        return None
    if not isinstance(x, str):
        x = str(x)
    return x.replace("\x00", "").strip()

def pick_func_name(obj, i):
    return clean_text(
        obj.get("entry_point")
        or obj.get("func_name")
        or obj.get("name")
        or obj.get("task_id")
        or f"func_{i}"
    )

def pick_task_id(obj, i):
    return clean_text(obj.get("task_id") or obj.get("entry_point") or f"task_{i}")

def import_one_language(cur, conn, lang, rel_path):
    file_path = BASE_DIR / rel_path
    table = f'public.heval_{lang}'

    insert_sql = f"""
    INSERT INTO {table} (
        repo, path, split, func_name,
        original_string,
        code, code_tokens,
        docstring, docstring_tokens,
        status, ast_status
    ) VALUES %s
    ON CONFLICT (func_name, split, docstring_tokens) DO UPDATE SET
        repo = EXCLUDED.repo,
        path = EXCLUDED.path,
        original_string = EXCLUDED.original_string,
        code = EXCLUDED.code,
        code_tokens = EXCLUDED.code_tokens,
        docstring = EXCLUDED.docstring,
        status = EXCLUDED.status,
        ast_status = 0,
        ast_error = NULL
    """

    print(f"Import {file_path} -> {table}")

    batch = []
    inserted = 0

    with file_path.open("r", encoding="utf-8", errors="replace") as f:
        for i, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue

            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue

            # MAPPING SESUAI INFO KAMU
            code = clean_text(obj.get("canonical_solution"))
            repo = clean_text(obj.get("solution"))
            path = clean_text(obj.get("completion"))
            token = clean_text(obj.get("test"))

            # optional / tambahan
            docstring = clean_text(obj.get("prompt") or obj.get("docstring"))
            func_name = pick_func_name(obj, i)
            task_id = pick_task_id(obj, i)
            original_string = clean_text(json.dumps(obj, ensure_ascii=False))

            row = (
                repo,
                path,
                SPLIT_VALUE,
                func_name,
                original_string,
                code,
                token,
                docstring,
                task_id,
                0,  # status
                0,  # ast_status
            )
            batch.append(row)

            if len(batch) >= BATCH_SIZE:
                execute_values(cur, insert_sql, batch, page_size=BATCH_SIZE)
                conn.commit()
                inserted += len(batch)
                batch.clear()

    if batch:
        execute_values(cur, insert_sql, batch, page_size=BATCH_SIZE)
        conn.commit()
        inserted += len(batch)

    print(f"  DONE inserted~{inserted}")

def main():
    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit = False
    cur = conn.cursor()
    try:
        for lang, rel in DATASETS.items():
            import_one_language(cur, conn, lang, rel)
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    main()
    print("ALL DONE")
