import argparse
import json
import os
import psycopg2
from psycopg2 import sql
from psycopg2.extras import execute_values
from constant import *
from parserfunc import *

# ============================================================
# CONFIG DATABASE
# ============================================================

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "codesearchnet",
    "user": "postgres",
    "password": "postgres",
    "options": "-c search_path=public"
}

BASE_PATH = "../disertasi_datasets/codexglue"
BATCH_SIZE = 5000
SCHEMA_FILE = "create_table.sql"

# ============================================================
# GET TABLE NAME
# ============================================================

def get_table_name(language):
    return f"c2t_{language}"

# ============================================================
# INITIALIZE SCHEMA
# ============================================================

def initialize_schema(conn, schema_file=SCHEMA_FILE):
    if not os.path.exists(schema_file):
        raise FileNotFoundError(f"Schema file tidak ditemukan: {schema_file}")

    print(f"[SCHEMA] Menjalankan {schema_file}")
    print("[SCHEMA] Perhatian: file ini berisi DROP TABLE/VIEW dan akan reset schema.")

    with open(schema_file, "r", encoding="utf-8") as f:
        schema_sql = f.read()

    cur = conn.cursor()
    try:
        cur.execute(schema_sql)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()

    print("[SCHEMA] Selesai.")

def check_table_exists(conn, table_name):
    cur = conn.cursor()
    cur.execute("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables
            WHERE table_schema='public'
            AND table_name=%s
        );
    """, (table_name,))
    exists = cur.fetchone()[0]
    cur.close()

    if not exists:
        raise RuntimeError(
            f"Tabel {table_name} tidak ditemukan. Jalankan dulu: "
            f"python3 01_prepare_db.py --init-schema"
        )

    print(f"[OK] Tabel {table_name} ditemukan.")

# ============================================================
# INSERT DATA
# ============================================================

def build_insert_row(row):
    return (
        row.get("repo", "") or row.get("repo_name", ""),
        row.get("path", ""),
        row.get("split", "train"),
        row.get("func_name", ""),
        row.get("original_string", ""),
        row.get("code", ""),
        " ".join(row.get("code_tokens", [])),
        row.get("docstring", ""),
        " ".join(row.get("docstring_tokens", [])),
        1
    )

def insert_batch(conn, table_name, rows):
    if not rows:
        return 0

    cur = conn.cursor()
    query = sql.SQL("""
        INSERT INTO {} (
            repo, path, split, func_name, original_string,
            code, code_tokens, docstring, docstring_tokens, status
        )
        VALUES %s
        ON CONFLICT (func_name, split, docstring_tokens) DO NOTHING
    """).format(sql.Identifier(table_name)).as_string(conn)

    try:
        execute_values(cur, query, rows, page_size=len(rows))
        inserted = cur.rowcount
        conn.commit()
        return inserted

    except Exception as e:
        conn.rollback()
        print(f"[DB ERROR] {e}")
        return 0
    finally:
        cur.close()

# ============================================================
# PROCESS JSONL
# ============================================================

def process_jsonl(filepath, split_name, table_name, conn):
    print(f"\n[LOAD] {filepath}")

    print("[Resume] Import semua baris; duplikat dilewati oleh ON CONFLICT.")

    batch = []
    inserted = 0
    total = 0
    with open(filepath, "r", encoding="utf-8") as f:
        for i, line in enumerate(f, start=1):
            total = i
            try:
                data = json.loads(line.strip())
                data["split"] = split_name
                batch.append(build_insert_row(data))

                if len(batch) >= BATCH_SIZE:
                    inserted += insert_batch(conn, table_name, batch)
                    batch.clear()

                if i % 500 == 0:
                    print(f"\r   -> read={i}, inserted~{inserted}", end="")

            except Exception as e:
                print(f"[JSON ERROR] line {i}: {e}")

    if batch:
        inserted += insert_batch(conn, table_name, batch)

    print(f"\n[DONE] Import read={total}, inserted~{inserted} dari {filepath}")

# ============================================================
# VERIFIER
# ============================================================

def verify_dataset(conn, languages):
    print("\n==================== VERIFIER ====================")

    for lang in languages:
        table = get_table_name(lang)
        print(f"\n[VERIF] Tabel: {table}")

        cur = conn.cursor()
        cur.execute(sql.SQL("""
            SELECT split, COUNT(*)
            FROM {}
            GROUP BY split
            ORDER BY split;
        """).format(sql.Identifier(table)))

        rows = cur.fetchall()
        for row in rows:
            print(row)

        cur.close()

    print("\n=================================================\n")

# ============================================================
# ARGUMENTS / MAIN
# ============================================================

def build_arg_parser():
    parser = argparse.ArgumentParser(
        description="Inisialisasi schema dari create_table.sql dan import CodeXGLUE ke DB."
    )
    parser.add_argument(
        "--init-schema",
        action="store_true",
        help="Jalankan create_table.sql satu kali di awal. Ini akan DROP/RESET tabel sesuai isi file SQL.",
    )
    parser.add_argument(
        "--schema-only",
        action="store_true",
        help="Hanya jalankan create_table.sql, tanpa import dataset.",
    )
    parser.add_argument(
        "--schema-file",
        default=SCHEMA_FILE,
        help=f"Path file schema SQL. Default: {SCHEMA_FILE}",
    )
    return parser


def main():
    args = build_arg_parser().parse_args()
    conn = psycopg2.connect(**DB_CONFIG)

    if args.init_schema:
        initialize_schema(conn, args.schema_file)
        if args.schema_only:
            conn.close()
            print("\n=== INISIALISASI SCHEMA SELESAI ===\n")
            return

    for lang in languages:
        table_name = get_table_name(lang)
        check_table_exists(conn, table_name)

        lang_folder = os.path.join(BASE_PATH, lang)
        if not os.path.exists(lang_folder):
            print(f"[SKIP] Folder tidak ditemukan: {lang_folder}")
            continue

        print(f"\n=========== IMPORT {lang.upper()} ===========")

        for split in splits:
            fp = os.path.join(lang_folder, f"{split}.jsonl")

            if os.path.exists(fp):
                process_jsonl(fp, split, table_name, conn)
            else:
                print(f"[SKIP] File tidak ditemukan: {fp}")

    verify_dataset(conn, languages)
    conn.close()

    print("\n=== IMPORT & VERIFIKASI SELESAI ===\n")

if __name__ == "__main__":
    main()
