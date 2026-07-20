import argparse
import json
import os
import sys
from pathlib import Path

CONDA_PYTHON = Path.home() / "miniconda3/envs/codesearchnet-prep/bin/python"
if CONDA_PYTHON.exists() and Path(sys.executable).resolve() != CONDA_PYTHON.resolve():
    os.execv(str(CONDA_PYTHON), [str(CONDA_PYTHON), *sys.argv])

import psycopg2
from psycopg2 import sql
from psycopg2.extras import Json, execute_batch

from parserfunc import programming_element_completeness


DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "codesearchnet",
    "user": "postgres",
    "password": "postgres",
    "options": "-c search_path=public",
}

DEFAULT_TABLES = (
    "c2c_cs",
    "c2c_java",
    "c2t_cpp",
    "c2t_cs",
    "c2t_go",
    "c2t_java",
    "c2t_javascript",
    "c2t_php",
    "c2t_python",
    "c2t_ruby",
    "c2t_rust",
    "heval",
    "heval_cpp",
    "heval_go",
    "heval_java",
    "heval_javascript",
    "heval_python",
    "heval_rust",
)

TABLE_WHITELIST = set(DEFAULT_TABLES)

TABLE_LANGUAGE = {
    "c2c_cs": "cs",
    "c2c_java": "java",
    "c2t_cpp": "cpp",
    "c2t_cs": "cs",
    "c2t_go": "go",
    "c2t_java": "java",
    "c2t_javascript": "javascript",
    "c2t_php": "php",
    "c2t_python": "python",
    "c2t_ruby": "ruby",
    "c2t_rust": "rust",
    "heval_cpp": "cpp",
    "heval_go": "go",
    "heval_java": "java",
    "heval_javascript": "javascript",
    "heval_python": "python",
    "heval_rust": "rust",
}


def parse_tables(raw_tables):
    if not raw_tables:
        return list(DEFAULT_TABLES)

    tables = [table.strip() for table in raw_tables.split(",") if table.strip()]
    invalid = sorted(set(tables) - TABLE_WHITELIST)
    if invalid:
        allowed = ", ".join(DEFAULT_TABLES)
        raise ValueError(f"Tabel tidak dikenal: {', '.join(invalid)}. Pilihan: {allowed}")

    return tables


def parse_ast(value, table, row_id, column):
    if isinstance(value, dict):
        return value

    try:
        return json.loads(value)
    except Exception as exc:
        raise ValueError(f"{table}.id={row_id}: gagal baca JSON {column}: {exc}") from exc


def count_rows(cur, table, only_with_pec_data=False):
    extra = sql.SQL(" AND pec_data IS NOT NULL") if only_with_pec_data else sql.SQL("")
    query = sql.SQL(
        """
        SELECT count(*)
        FROM {table}
        WHERE ast_original IS NOT NULL
          AND ast_unified IS NOT NULL
          {extra}
        """
    ).format(table=sql.Identifier(table), extra=extra)
    cur.execute(query)
    return cur.fetchone()[0]


def fetch_batch(cur, table, last_id, batch_size, only_with_pec_data=False, limit=None):
    extra = sql.SQL(" AND pec_data IS NOT NULL") if only_with_pec_data else sql.SQL("")
    batch_limit = batch_size if limit is None else min(batch_size, limit)

    query = sql.SQL(
        """
        SELECT id, ast_original, ast_unified
        FROM {table}
        WHERE ast_original IS NOT NULL
          AND ast_unified IS NOT NULL
          AND id > %s
          {extra}
        ORDER BY id
        LIMIT %s
        """
    ).format(table=sql.Identifier(table), extra=extra)

    cur.execute(query, (last_id, batch_limit))
    return cur.fetchall()


def update_batch(cur, table, rows):
    query = sql.SQL(
        """
        UPDATE {table}
        SET pec_score = %s,
            pec_score_all = %s,
            pec_data = %s
        WHERE id = %s
        """
    ).format(table=sql.Identifier(table))

    execute_batch(cur, query.as_string(cur), rows, page_size=len(rows))


def recalculate_table(conn, table, batch_size, only_with_pec_data=False, dry_run=False, limit=None):
    read_cur = conn.cursor()
    write_cur = conn.cursor()
    total_rows = count_rows(read_cur, table, only_with_pec_data=only_with_pec_data)
    if limit is not None:
        total_rows = min(total_rows, limit)

    if total_rows == 0:
        print(f"[SKIP] {table}: 0 rows")
        return 0, 0

    print(f"[START] {table}: {total_rows} rows")

    processed = 0
    failed = 0
    last_id = 0
    table_language = TABLE_LANGUAGE.get(table)

    while True:
        remaining = None if limit is None else limit - processed
        if remaining is not None and remaining <= 0:
            break

        rows = fetch_batch(
            read_cur,
            table,
            last_id,
            batch_size,
            only_with_pec_data=only_with_pec_data,
            limit=remaining,
        )
        if not rows:
            break

        updates = []
        for row_id, ast_original_raw, ast_unified_raw in rows:
            last_id = row_id
            try:
                ast_original = parse_ast(ast_original_raw, table, row_id, "ast_original")
                ast_unified = parse_ast(ast_unified_raw, table, row_id, "ast_unified")
                pec_result = programming_element_completeness(
                    ast_original,
                    ast_unified,
                    language=table_language,
                )
                updates.append(
                    (
                        pec_result["pec"],
                        pec_result["pec_all"],
                        Json(pec_result),
                        row_id,
                    )
                )
            except Exception as exc:
                failed += 1
                print(f"[WARN] {exc}")

        if updates and not dry_run:
            update_batch(write_cur, table, updates)
            conn.commit()

        processed += len(rows)
        if processed % (batch_size * 10) == 0 or processed >= total_rows:
            mode = "DRY-RUN" if dry_run else "PROGRESS"
            print(f"[{mode}] {table}: {processed}/{total_rows}")

    if dry_run:
        conn.rollback()

    print(f"[DONE] {table}: processed={processed}, failed={failed}")
    return processed, failed


def refresh_pec_result(conn, dry_run=False):
    if dry_run:
        print("[DRY-RUN] skip refresh_pec_result()")
        return

    cur = conn.cursor()
    try:
        cur.execute("SELECT refresh_pec_result();")
        conn.commit()
        print("[DONE] pec_result cache refreshed")
    except psycopg2.Error as exc:
        conn.rollback()
        print(f"[WARN] refresh_pec_result() gagal atau belum tersedia: {exc}")


def build_arg_parser():
    parser = argparse.ArgumentParser(
        description="Hitung ulang PEC dari ast_original/ast_unified tanpa reparsing source code."
    )
    parser.add_argument(
        "--tables",
        help="Daftar tabel dipisah koma. Default: semua tabel yang punya kolom PEC.",
    )
    parser.add_argument("--batch-size", type=int, default=1000)
    parser.add_argument(
        "--only-with-pec-data",
        action="store_true",
        help="Hanya hitung ulang baris yang pec_data lama sudah ada.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Batas jumlah baris per tabel, berguna untuk smoke test.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Hitung tanpa menulis hasil ke database.",
    )
    parser.add_argument(
        "--no-refresh-pec-result",
        action="store_true",
        help="Jangan refresh materialized view pec_result_cache setelah selesai.",
    )
    return parser


def main():
    args = build_arg_parser().parse_args()

    if args.batch_size <= 0:
        raise ValueError("--batch-size harus lebih besar dari 0")
    if args.limit is not None and args.limit <= 0:
        raise ValueError("--limit harus lebih besar dari 0")

    tables = parse_tables(args.tables)

    conn = psycopg2.connect(**DB_CONFIG)
    try:
        total_processed = 0
        total_failed = 0

        for table in tables:
            processed, failed = recalculate_table(
                conn,
                table,
                args.batch_size,
                only_with_pec_data=args.only_with_pec_data,
                dry_run=args.dry_run,
                limit=args.limit,
            )
            total_processed += processed
            total_failed += failed

        if not args.no_refresh_pec_result:
            refresh_pec_result(conn, dry_run=args.dry_run)

        print(f"[SUMMARY] processed={total_processed}, failed={total_failed}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
