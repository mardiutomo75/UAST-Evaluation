import hashlib
from collections import defaultdict
import subprocess
import time

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
MAX_GPU_TEMP_C = 75


def stable_order_key(*parts):
    text = "|".join(map(str, parts)).encode("utf-8")
    return hashlib.md5(text).hexdigest()


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


def load_heval_pairs(cur):
    cur.execute(
        """
        SELECT language1, language2, func_id
        FROM heval_matrix
        WHERE ted IS NOT NULL AND similarity IS NOT NULL
        ORDER BY md5(language1 || '|' || language2 || '|' || func_id::text)
        """
    )
    return cur.fetchall()


def load_c2c_pairs(cur):
    cur.execute(
        """
        SELECT j.id
        FROM c2c_java j
        INNER JOIN c2c_cs c ON j.id = c.id
        WHERE j.ast_status IN (1, 2)
          AND c.ast_status IN (1, 2)
          AND j.code IS NOT NULL
          AND c.code IS NOT NULL
        ORDER BY md5(j.id::text)
        """
    )
    return [int(row[0]) for row in cur.fetchall()]


def fetch_heval_code_pairs(cur):
    pairs = load_heval_pairs(cur)
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


def fetch_c2c_code_pairs(cur):
    ids = load_c2c_pairs(cur)
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
        wait_for_gpu_cooldown()
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


def gpu_temperature_c():
    try:
        output = subprocess.check_output(
            [
                "nvidia-smi",
                "--query-gpu=temperature.gpu",
                "--format=csv,noheader,nounits",
            ],
            text=True,
        ).strip()
        if not output:
            return None
        return max(int(line.strip()) for line in output.splitlines() if line.strip())
    except Exception:
        return None


def wait_for_gpu_cooldown():
    while True:
        temp = gpu_temperature_c()
        if temp is None or temp < MAX_GPU_TEMP_C:
            return temp
        print(f"GPU temperature {temp}C >= {MAX_GPU_TEMP_C}C, waiting 30s")
        time.sleep(30)


def codebert_similarity(rows):
    if not rows:
        return None
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is required for this baseline run")
    device = torch.device("cuda:0")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModel.from_pretrained(MODEL_NAME).to(device)
    model.eval()

    codes1 = [row["code1"] for row in rows]
    codes2 = [row["code2"] for row in rows]
    emb1 = encode_texts(tokenizer, model, codes1, device, batch_size=8)
    emb2 = encode_texts(tokenizer, model, codes2, device, batch_size=8)
    sim = torch.nn.functional.cosine_similarity(emb1, emb2, dim=1)
    return float(sim.mean().item()), len(rows), device.type


def store_rows(cur, rows):
    cur.execute("DELETE FROM baseline_comparison_results WHERE baseline_name = %s", ("CodeBERT raw-code cosine (all)",))
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

    heval_pairs = fetch_heval_code_pairs(cur)
    heval_codebert = codebert_similarity(
        sorted(heval_pairs, key=lambda row: stable_order_key(row["language1"], row["language2"], row["func_id"]))
    )
    if heval_codebert is not None:
        mean_sim, sample_count, device_type = heval_codebert
        rows.append(
            (
                "HumanEval-X",
                "CodeBERT raw-code cosine (all)",
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
                        "sampling": "all available heval_matrix pairs with ted and similarity not null",
                    }
                ),
            )
        )

    c2c_pairs = fetch_c2c_code_pairs(cur)
    c2c_codebert = codebert_similarity(
        sorted(c2c_pairs, key=lambda row: stable_order_key(row["func_id"]))
    )
    if c2c_codebert is not None:
        mean_sim, sample_count, device_type = c2c_codebert
        rows.append(
            (
                "Code2Code Java-C#",
                "CodeBERT raw-code cosine (all)",
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
                        "sampling": "all available aligned Java-C# pairs with code and ast_status valid",
                    }
                ),
            )
        )

    store_rows(cur, rows)
    conn.commit()

    cur.execute(
        """
        SELECT dataset, baseline_name, sample_count, code_similarity
        FROM baseline_comparison_results
        WHERE baseline_name = 'CodeBERT raw-code cosine (all)'
        ORDER BY dataset
        """
    )
    for row in cur.fetchall():
        print(row)

    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
