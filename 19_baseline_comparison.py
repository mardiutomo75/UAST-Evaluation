import hashlib
import json
from collections import defaultdict

import psycopg2
from psycopg2.extras import Json, execute_values
import torch
from transformers import AutoModel, AutoTokenizer


DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "codesearchnet",
    "user": "postgres",
    "password": "postgres",
    "options": "-c search_path=public",
}

MODEL_NAME = "microsoft/codebert-base"
HEVAL_SAMPLE_LIMIT = 300
C2C_SAMPLE_LIMIT = 300


def stable_order_key(*parts):
    text = "|".join(map(str, parts)).encode("utf-8")
    return hashlib.md5(text).hexdigest()


def mean(values):
    values = [float(v) for v in values if v is not None]
    if not values:
        return None
    return sum(values) / len(values)


def ensure_table(cur):
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS baseline_comparison_results (
            id BIGSERIAL PRIMARY KEY,
            created_at timestamptz DEFAULT now(),
            dataset text NOT NULL,
            baseline_name text NOT NULL,
            language1 text,
            language2 text,
            sample_count integer,
            pec_core numeric,
            pec_all numeric,
            clsa numeric,
            resr numeric,
            code_similarity numeric,
            details jsonb
        )
        """
    )


def sample_pairs(cur, query, limit):
    cur.execute(query, (limit,))
    return cur.fetchall()


def load_heval_pairs(cur, limit):
    cur.execute(
        """
        SELECT language1, language2, func_id
        FROM heval_matrix
        ORDER BY md5(language1 || '|' || language2 || '|' || func_id::text)
        LIMIT %s
        """,
        (limit,),
    )
    return cur.fetchall()


def load_c2c_pairs(cur, limit):
    cur.execute(
        """
        SELECT id
        FROM c2c_java
        WHERE ast_status IN (1, 2)
          AND code IS NOT NULL
        ORDER BY md5(id::text)
        LIMIT %s
        """,
        (limit,),
    )
    return [int(row[0]) for row in cur.fetchall()]


def fetch_heval_code_pairs(cur, limit):
    pairs = load_heval_pairs(cur, limit)
    grouped = defaultdict(list)
    for language1, language2, func_id in pairs:
        grouped[(language1, language2)].append(int(func_id))

    rows = []
    for (language1, language2), func_ids in grouped.items():
        table1 = f"heval_{language1}"
        table2 = f"heval_{language2}"
        cur.execute(
            f"""
            SELECT l.id, l.code, r.code
            FROM {table1} l
            INNER JOIN {table2} r ON l.id = r.id
            WHERE l.id = ANY(%s)
              AND l.ast_status IN (1, 2)
              AND r.ast_status IN (1, 2)
            ORDER BY l.id
            """,
            (func_ids,),
        )
        for func_id, code1, code2 in cur.fetchall():
            rows.append(
                {
                    "func_id": int(func_id),
                    "language1": language1,
                    "language2": language2,
                    "code1": code1 or "",
                    "code2": code2 or "",
                }
            )
    return rows


def fetch_c2c_code_pairs(cur, limit):
    ids = load_c2c_pairs(cur, limit)
    if not ids:
        return []
    cur.execute(
        """
        SELECT j.id, j.code, c.code
        FROM c2c_java j
        INNER JOIN c2c_cs c ON j.id = c.id
        WHERE j.id = ANY(%s)
          AND j.ast_status IN (1, 2)
          AND c.ast_status IN (1, 2)
        ORDER BY j.id
        """,
        (ids,),
    )
    return [
        {
            "func_id": int(func_id),
            "language1": "java",
            "language2": "cs",
            "code1": code1 or "",
            "code2": code2 or "",
        }
        for func_id, code1, code2 in cur.fetchall()
    ]


def encode_texts(tokenizer, model, texts, device, batch_size=16, max_length=256):
    embeddings = []
    for start in range(0, len(texts), batch_size):
        batch_texts = texts[start:start + batch_size]
        encoded = tokenizer(
            batch_texts,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=max_length,
        ).to(device)
        with torch.no_grad():
            output = model(**encoded)
        last_hidden = output.last_hidden_state
        mask = encoded["attention_mask"].unsqueeze(-1)
        pooled = (last_hidden * mask).sum(dim=1) / mask.sum(dim=1).clamp(min=1)
        embeddings.append(pooled.detach().cpu())
    return torch.cat(embeddings, dim=0)


def codebert_similarity(rows):
    if not rows:
        return None

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModel.from_pretrained(MODEL_NAME).to(device)
    model.eval()

    codes1 = [row["code1"] for row in rows]
    codes2 = [row["code2"] for row in rows]
    emb1 = encode_texts(tokenizer, model, codes1, device)
    emb2 = encode_texts(tokenizer, model, codes2, device)
    sim = torch.nn.functional.cosine_similarity(emb1, emb2, dim=1)
    return float(sim.mean().item()), len(rows), device.type


def store_rows(cur, rows):
    cur.execute("DELETE FROM baseline_comparison_results")
    query = """
        INSERT INTO baseline_comparison_results (
            dataset, baseline_name, language1, language2, sample_count,
            pec_core, pec_all, clsa, resr, code_similarity, details
        )
        VALUES %s
    """
    execute_values(cur, query, rows, page_size=50)


def main():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    ensure_table(cur)

    rows = []

    cur.execute(
        """
        SELECT
            count(*) AS sample_count,
            avg(pec_score) AS pec_core,
            avg(pec_score_all) AS pec_all,
            avg(1 - compression_ratio) AS resr
        FROM (
            SELECT pec_score, pec_score_all, compression_ratio FROM heval_cpp WHERE pec_score IS NOT NULL AND pec_score_all IS NOT NULL AND compression_ratio IS NOT NULL
            UNION ALL
            SELECT pec_score, pec_score_all, compression_ratio FROM heval_go WHERE pec_score IS NOT NULL AND pec_score_all IS NOT NULL AND compression_ratio IS NOT NULL
            UNION ALL
            SELECT pec_score, pec_score_all, compression_ratio FROM heval_java WHERE pec_score IS NOT NULL AND pec_score_all IS NOT NULL AND compression_ratio IS NOT NULL
            UNION ALL
            SELECT pec_score, pec_score_all, compression_ratio FROM heval_javascript WHERE pec_score IS NOT NULL AND pec_score_all IS NOT NULL AND compression_ratio IS NOT NULL
            UNION ALL
            SELECT pec_score, pec_score_all, compression_ratio FROM heval_python WHERE pec_score IS NOT NULL AND pec_score_all IS NOT NULL AND compression_ratio IS NOT NULL
            UNION ALL
            SELECT pec_score, pec_score_all, compression_ratio FROM heval_rust WHERE pec_score IS NOT NULL AND pec_score_all IS NOT NULL AND compression_ratio IS NOT NULL
        ) x
        """
    )
    sample_count, pec_core, pec_all, resr = cur.fetchone()
    cur.execute(
        """
        SELECT avg(ted), avg(similarity)
        FROM heval_matrix
        WHERE ted IS NOT NULL AND similarity IS NOT NULL
        """
    )
    clsa, code_similarity = cur.fetchone()
    rows.append(
        (
            "HumanEval-X",
            "UAST intrinsic summary",
            "ALL",
            "ALL",
            int(sample_count or 0),
            float(pec_core) if pec_core is not None else None,
            float(pec_all) if pec_all is not None else None,
            float(clsa) if clsa is not None else None,
            float(resr) if resr is not None else None,
            float(code_similarity) if code_similarity is not None else None,
            Json({"source": "heval_cpp aggregate placeholder"}),
        )
    )

    cur.execute(
        """
        SELECT
            count(*) AS sample_count,
            avg(pec_score) AS pec_core,
            avg(pec_score_all) AS pec_all,
            avg(1 - compression_ratio) AS resr,
            avg(similarity) AS clsa,
            avg(ted) AS code_similarity
        FROM c2c_java
        WHERE pec_score IS NOT NULL
          AND pec_score_all IS NOT NULL
          AND compression_ratio IS NOT NULL
        """
    )
    sample_count, pec_core, pec_all, resr, clsa, code_similarity = cur.fetchone()
    rows.append(
        (
            "Code2Code Java-C#",
            "UAST intrinsic summary",
            "ALL",
            "ALL",
            int(sample_count or 0),
            float(pec_core) if pec_core is not None else None,
            float(pec_all) if pec_all is not None else None,
            float(clsa) if clsa is not None else None,
            float(resr) if resr is not None else None,
            float(code_similarity) if code_similarity is not None else None,
            Json({"source": "c2c_java aggregate"}),
        )
    )

    heval_pairs = fetch_heval_code_pairs(cur, HEVAL_SAMPLE_LIMIT)
    heval_codebert = codebert_similarity(
        sorted(heval_pairs, key=lambda row: stable_order_key(row["language1"], row["language2"], row["func_id"]))
    )
    if heval_codebert is not None:
        mean_sim, sample_count, device_type = heval_codebert
        rows.append(
            (
                "HumanEval-X",
                "CodeBERT raw-code cosine",
                "ALL",
                "ALL",
                sample_count,
                None,
                None,
                None,
                None,
                mean_sim,
                Json(
                    {
                        "model": MODEL_NAME,
                        "device": device_type,
                        "sample_limit": HEVAL_SAMPLE_LIMIT,
                        "sampling": "ORDER BY md5(language1||language2||func_id)",
                    }
                ),
            )
        )

    c2c_pairs = fetch_c2c_code_pairs(cur, C2C_SAMPLE_LIMIT)
    c2c_codebert = codebert_similarity(
        sorted(c2c_pairs, key=lambda row: stable_order_key(row["func_id"]))
    )
    if c2c_codebert is not None:
        mean_sim, sample_count, device_type = c2c_codebert
        rows.append(
            (
                "Code2Code Java-C#",
                "CodeBERT raw-code cosine",
                "ALL",
                "ALL",
                sample_count,
                None,
                None,
                None,
                None,
                mean_sim,
                Json(
                    {
                        "model": MODEL_NAME,
                        "device": device_type,
                        "sample_limit": C2C_SAMPLE_LIMIT,
                        "sampling": "ORDER BY md5(id::text)",
                    }
                ),
            )
        )

    store_rows(cur, rows)
    conn.commit()

    cur.execute(
        """
        SELECT dataset, baseline_name, sample_count, pec_core, pec_all, clsa, resr, code_similarity
        FROM baseline_comparison_results
        ORDER BY dataset, baseline_name
        """
    )
    for row in cur.fetchall():
        print(row)

    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
