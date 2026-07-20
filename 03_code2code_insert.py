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

# ---------- FILE SPLIT ----------
DATASETS_CS = {
    "train": "train.java-cs.txt.cs",
    "valid": "valid.java-cs.txt.cs",
    "test":  "test.java-cs.txt.cs",
}
DATASETS_JAVA = {
    "train": "train.java-cs.txt.java",
    "valid": "valid.java-cs.txt.java",
    "test":  "test.java-cs.txt.java",
}
BASE_DIR = "../disertasi_datasets/code2code"
BATCH_SIZE = 5000


def flush_batch(cur, conn, lang, batch):
    if not batch:
        return 0

    query = f"""
        INSERT INTO public.c2c_{lang} (split, func_name, code, status)
        VALUES %s
    """
    execute_values(cur, query, batch, page_size=len(batch))
    conn.commit()
    return cur.rowcount


def goinsert(cur, conn, lang, DATASETS):
    for split, filename in DATASETS.items():
        path = BASE_DIR+"/"+filename
        print(f"Import {path} -> split={split}")

        batch = []
        inserted = 0
        with open(path, "rb") as f:
            for i, raw in enumerate(f, start=1):
                code = (
                    raw.replace(b"\x00", b"")
                       .decode("utf-8", errors="replace")
                       .strip()
                )
    
                if not code:
                    continue

                func_name = f"{split}_func_{i}"
                batch.append((split, func_name, code, 0))

                if len(batch) >= BATCH_SIZE:
                    inserted += flush_batch(cur, conn, lang, batch)
                    batch.clear()

                if i % 5000 == 0:
                    print(f"\r  read={i}, inserted~{inserted}", end="")

        if batch:
            inserted += flush_batch(cur, conn, lang, batch)

        print(f"\n  DONE {split}, inserted~{inserted}")


conn = psycopg2.connect(**DB_CONFIG)
cur = conn.cursor()
try:
    goinsert(cur, conn, 'cs', DATASETS_CS)
    goinsert(cur, conn, 'java', DATASETS_JAVA)
finally:
    cur.close()
    conn.close()

print("ALL DONE")
