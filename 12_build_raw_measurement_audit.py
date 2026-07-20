import hashlib
import json

import psycopg2
from psycopg2.extras import Json, execute_batch


DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "codesearchnet",
    "user": "postgres",
    "password": "postgres",
    "options": "-c search_path=public",
}

BATCH_SIZE = 5000

TABLES = [
    ("Code2Code Java-C#", "c2c_cs", "cs"),
    ("Code2Code Java-C#", "c2c_java", "java"),
    ("CodeXGLUE code-to-text", "c2t_go", "go"),
    ("CodeXGLUE code-to-text", "c2t_java", "java"),
    ("CodeXGLUE code-to-text", "c2t_javascript", "javascript"),
    ("CodeXGLUE code-to-text", "c2t_php", "php"),
    ("CodeXGLUE code-to-text", "c2t_python", "python"),
    ("CodeXGLUE code-to-text", "c2t_ruby", "ruby"),
    ("HumanEval-X", "heval_cpp", "cpp"),
    ("HumanEval-X", "heval_go", "go"),
    ("HumanEval-X", "heval_java", "java"),
    ("HumanEval-X", "heval_javascript", "javascript"),
    ("HumanEval-X", "heval_python", "python"),
    ("HumanEval-X", "heval_rust", "rust"),
]


def sha256_text(value):
    if value is None:
        return None
    if not isinstance(value, str):
        value = json.dumps(value, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def iter_table_rows(cur, table, last_id=0):
    while True:
        cur.execute(
            f"""
            SELECT id, split, code, ast_original, ast_unified,
                   dtime, dtime1, dtime2, dtime3,
                   dmem, dmem1, dmem2, dmem3,
                   compression_ratio, f1, precision, recall,
                   pec_score, pec_score_all, attribut_ori, attribut_uni, attribut_loss
            FROM {table}
            WHERE id > %s
              AND ast_original IS NOT NULL
              AND ast_unified IS NOT NULL
            ORDER BY id
            LIMIT %s
            """,
            (last_id, BATCH_SIZE),
        )
        rows = cur.fetchall()
        if not rows:
            break
        for row in rows:
            last_id = row[0]
            yield row


def build_audit_row(dataset, table, language, row):
    (
        row_id,
        split,
        code,
        ast_original,
        ast_unified,
        dtime,
        dtime1,
        dtime2,
        dtime3,
        dmem,
        dmem1,
        dmem2,
        dmem3,
        compression_ratio,
        f1,
        precision,
        recall,
        pec_score,
        pec_score_all,
        attribut_ori,
        attribut_uni,
        attribut_loss,
    ) = row

    summary = {
        "timing_seconds": {
            "ast_time": float(dtime) if dtime is not None else None,
            "total_time": float(dtime1) if dtime1 is not None else None,
            "uast_extra_time": float(dtime2) if dtime2 is not None else None,
            "time_overhead_percent": float(dtime3) if dtime3 is not None else None,
        },
        "memory_bytes": {
            "ast_memory": float(dmem) if dmem is not None else None,
            "total_memory": float(dmem1) if dmem1 is not None else None,
            "uast_extra_memory": float(dmem2) if dmem2 is not None else None,
            "memory_overhead_percent": float(dmem3) if dmem3 is not None else None,
        },
        "representation": {
            "compression_ratio": float(compression_ratio) if compression_ratio is not None else None,
            "attributes_original": int(attribut_ori) if attribut_ori is not None else None,
            "attributes_unified": int(attribut_uni) if attribut_uni is not None else None,
            "attribute_loss": float(attribut_loss) if attribut_loss is not None else None,
        },
        "identifier_preservation": {
            "f1": float(f1) if f1 is not None else None,
            "precision": float(precision) if precision is not None else None,
            "recall": float(recall) if recall is not None else None,
        },
        "pec": {
            "pec_score": float(pec_score) if pec_score is not None else None,
            "pec_score_all": float(pec_score_all) if pec_score_all is not None else None,
        },
    }

    raw_runs = {
        "measurement_count": 1,
        "time_source": "time.perf_counter()",
        "memory_source": "tracemalloc peak bytes",
        "columns": {
            "dtime": "AST original parse + AST dict extraction time in seconds",
            "dtime1": "total AST + UAST construction time in seconds",
            "dtime2": "UAST extra time in seconds",
            "dtime3": "time overhead percentage",
            "dmem": "AST memory peak in bytes",
            "dmem1": "total memory peak in bytes",
            "dmem2": "UAST extra memory in bytes",
            "dmem3": "memory overhead percentage",
        },
    }

    return (
        dataset,
        table,
        language,
        split,
        row_id,
        sha256_text(code),
        sha256_text(ast_original),
        sha256_text(ast_unified),
        Json(summary),
        Json(raw_runs),
    )


def flush(cur, rows):
    if not rows:
        return
    execute_batch(
        cur,
        """
        INSERT INTO raw_measurement_audit (
            dataset, table_name, language, split, row_id,
            code_sha256, ast_sha256, uast_sha256,
            summary, raw_runs
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        rows,
        page_size=len(rows),
    )


def main():
    conn = psycopg2.connect(**DB_CONFIG)
    read_cur = conn.cursor()
    write_cur = conn.cursor()

    write_cur.execute("TRUNCATE raw_measurement_audit RESTART IDENTITY")
    conn.commit()

    total = 0
    for dataset, table, language in TABLES:
        batch = []
        table_count = 0
        for row in iter_table_rows(read_cur, table):
            batch.append(build_audit_row(dataset, table, language, row))
            table_count += 1
            total += 1
            if len(batch) >= BATCH_SIZE:
                flush(write_cur, batch)
                conn.commit()
                batch.clear()
        if batch:
            flush(write_cur, batch)
            conn.commit()
        print(f"{table}: {table_count}")

    read_cur.close()
    write_cur.close()
    conn.close()
    print(f"raw_measurement_audit rows: {total}")


if __name__ == "__main__":
    main()
