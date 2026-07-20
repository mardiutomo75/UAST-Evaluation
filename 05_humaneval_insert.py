import json
import psycopg2
from psycopg2.extras import execute_values
from pathlib import Path

DB_CONFIG = {
    "host": "localhost",
    "dbname": "codesearchnet",
    "user": "postgres",
    "password": "postgres",
    "port": 5432,
}


DATASETS = {
    "python": "./python/humaneval_python.jsonl",
    "java": "./java/humaneval_java.jsonl",
    "cpp":  "./cpp/humaneval_cpp.jsonl",
    "javascript": "./javascript/humaneval_javascript.jsonl",
    "rust": "./rust/humaneval_rust.jsonl",
    "go": "./go/humaneval_go.jsonl",
}
BASE_DIR = Path("../disertasi_datasets/humaneval-x")

SPLIT_VALUE = "humaneval"   # konstan karena di jsonl tidak ada split
BATCH_SIZE = 1000

INSERT_SQL = """
INSERT INTO public.heval (
    language, split, func_name,
    original_string, code, docstring,
    status, ast_status,
    func_original
) VALUES %s;
"""

def clean_text(x):
    if x is None:
        return None
    if not isinstance(x, str):
        x = str(x)
    return x.replace("\x00", "")

def pick_func_name(obj, i):
    return clean_text(
        obj.get("entry_point")
        or obj.get("func_name")
        or obj.get("name")
        or obj.get("task_id")
        or f"func_{i}"
    )

def pick_docstring(obj):
    return clean_text(
        obj.get("prompt")
        or obj.get("docstring")
        or obj.get("instruction")
        or obj.get("text")
    )

def pick_code(obj):
    return clean_text(
        obj.get("canonical_solution")
        or obj.get("solution")
        or obj.get("completion")
        or obj.get("code")
    )

def import_jsonl():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    try:
        for lang, rel in DATASETS.items():
            file_path = BASE_DIR / rel
            print(f"Import {file_path} -> language={lang}")

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

                    func_name = pick_func_name(obj, i)
                    docstring = pick_docstring(obj)
                    code = pick_code(obj)

                    original_string = clean_text(json.dumps(obj, ensure_ascii=False))

                    # simpan metadata minimal ke jsonb func_original
                    meta = {
                        "task_id": obj.get("task_id"),
                        "entry_point": obj.get("entry_point"),
                        "source_file": str(file_path),
                    }

                    row = (
                        lang,
                        SPLIT_VALUE,
                        func_name,
                        original_string,
                        code,
                        docstring,
                        1,  # status
                        0,  # ast_status
                        json.dumps(meta, ensure_ascii=False),
                    )
                    batch.append(row)

                    if len(batch) >= BATCH_SIZE:
                        execute_values(cur, INSERT_SQL, batch, page_size=BATCH_SIZE)
                        conn.commit()
                        inserted += len(batch)
                        batch.clear()

            if batch:
                execute_values(cur, INSERT_SQL, batch, page_size=BATCH_SIZE)
                conn.commit()
                inserted += len(batch)

            print(f"  DONE inserted~{inserted}")

    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    import_jsonl()
    print("ALL DONE")
