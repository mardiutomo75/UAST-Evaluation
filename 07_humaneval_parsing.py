import os
import sys
from pathlib import Path
from itertools import combinations

CONDA_PYTHON = Path.home() / "miniconda3/envs/codesearchnet-prep/bin/python"
if CONDA_PYTHON.exists() and Path(sys.executable).resolve() != CONDA_PYTHON.resolve():
    os.execv(str(CONDA_PYTHON), [str(CONDA_PYTHON), *sys.argv])

import psycopg2
import psycopg2.extras
from psycopg2.extras import Json
from concurrent.futures import ProcessPoolExecutor, as_completed
from tqdm import tqdm
from collections import defaultdict
from constant import *
from parserfunc import *
import time
import tracemalloc

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "codesearchnet",
    "user": "postgres",
    "password": "postgres",
    "options": "-c search_path=public"
}

ACTIVE_LANGUAGES = [lang for lang in languages if lang not in ("php", "cs", "ruby")]
BATCH_SIZE = 500

# ======================================================
# GET TABLE NAME PER BAHASA
# ======================================================
def get_table(lang):
    return f"heval_{lang}"

# ======================================================
# INIT WORKER — each process gets its own parser
# ======================================================
def init_worker(langid):
    global myparser
    myparser = Myparser()
    myparser.setparser(langid)

# ======================================================
# Fetch pending rows
# ======================================================
def fetch_batch(lang, split, batch_size=BATCH_SIZE):
    table = get_table(lang)

    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    query = f"""
        WITH picked AS (
            SELECT id
            FROM {table}
            WHERE ast_status=0
            ORDER BY id
            LIMIT %s
            FOR UPDATE SKIP LOCKED
        )
        UPDATE {table} t
        SET ast_status=9
        FROM picked
        WHERE t.id=picked.id
        RETURNING t.id, t.code;
    """

    cur.execute(query, (batch_size,))
    rows = cur.fetchall()
    conn.commit()
    conn.close()
    return rows

# ======================================================
# Fetch pending rows
# ======================================================
def fetch_batch_ctc(lang1,lang2, batch_size=200):
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    table1 = get_table(lang1)
    table2 = get_table(lang2)

    query = f"""
        SELECT java.id as java_id,java.ast_unified as java_ast_unified, java.ast_original as java_ast_original, java.code as java_code, cs.id as cs_id, cs.ast_unified as cs_ast_unified, cs.ast_original as cs_ast_original,
        cs.code as cs_code FROM {table1} cs INNER JOIN {table2} java on cs.id=java.id 
        WHERE cs.ast_status=1
        AND java.ast_status=1
        AND NOT EXISTS (
            SELECT 1
            FROM heval_matrix m
            WHERE m.func_id=java.id
            AND (
                (m.language1=%s AND m.language2=%s)
                OR (m.language1=%s AND m.language2=%s)
            )
        )
        ORDER BY cs.id
        LIMIT %s;
    """

    cur.execute(query, (lang1, lang2, lang2, lang1, batch_size))
    rows = cur.fetchall()
    conn.close()
    return rows

# ======================================================
# PROCESS 1 ROW (WORKER)
# ======================================================
def process_one(row, lang):
    rid, code = row
    global myparser

    try:
        
        code = code.strip()
        source = code.encode("utf8")
        
        # start extract AST
        tracemalloc.start()
        start_time = time.perf_counter()       
        ast_tree = myparser.parse_code_to_ast(code)
        ast_ori = myparser.node_to_dict(ast_tree.root_node, source)

        baseline_time = time.perf_counter() - start_time
        current, peak = tracemalloc.get_traced_memory()
        baseline_memory = peak

        ast_uni = myparser.node_to_dict_unified(ast_tree.root_node, source)
        ast_uni = myparser.simplify_ast_use_deepest_root(ast_uni)
        
        
        full_time = time.perf_counter() - start_time
        current, peak = tracemalloc.get_traced_memory()
        full_memory = peak
        tracemalloc.stop()
        
        # overhead
        time_overhead = full_time - baseline_time
        memory_overhead = full_memory - baseline_memory
        
        time_overhead_percent = (time_overhead / baseline_time) * 100 if baseline_time > 0 else 0
        memory_overhead_percent = (memory_overhead / baseline_memory) * 100 if baseline_memory > 0 else 0
        
        comp_ratio = ast_compression_ratio(ast_ori,ast_uni)
        # extract variables/functions
        vars1, funcs1 = set(), set()
        vars2, funcs2 = set(), set()

        myparser.extract_identifiers(ast_ori, vars1, funcs1)
        myparser.extract_identifiers(ast_uni, vars2, funcs2)
        loss = attribute_loss(ast_ori, ast_uni)

        pr = myparser.precision_recall(vars1 | funcs1, vars2 | funcs2)

        # === Node type extraction ===
        node_ori = []
        node_std = []
        node_removed = []
        node_single = []

        myparser.collect_original_types(ast_ori, node_ori)
        myparser.collect_standart_types(ast_uni, node_std)
        myparser.collect_removed_types(ast_ori, ast_uni, node_removed)
        myparser.collect_single_child_types(ast_ori, node_single)
        pec_result = myparser.calculate_pec(ast_ori, ast_uni)

        return {
            "ok": True,
            "update": (
                baseline_time, baseline_memory,
                full_time, full_memory,
                time_overhead, memory_overhead,
                time_overhead_percent, memory_overhead_percent,
                loss['attributes_original'], loss['attributes_unified'], loss['attribute_loss'],
                comp_ratio['compression_ratio'],
                json.dumps(ast_ori),
                json.dumps(ast_uni),
                json.dumps(list(vars1)), json.dumps(list(funcs1)),
                json.dumps(list(vars2)), json.dumps(list(funcs2)),
                pr["f1"], pr["precision"], pr["recall"],
                pec_result["pec"], pec_result["pec_all"], json.dumps(pec_result),
                rid
            ),
            "nodes": {
                "original": node_ori,
                "standart": node_std,
                "removed": node_removed,
                "single_child": node_single
            }
        }

    except Exception as e:
        tracemalloc.stop()
        print("[WORKER ERROR]", e)
        return {"ok": False, "error": (str(e), rid), "nodes": None}


def flush_success_updates(lang, rows):
    if not rows:
        return

    table = get_table(lang)
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    query = f"""
        UPDATE {table} SET
            dtime=%s,
            dmem=%s,
            dtime1=%s,
            dmem1=%s,
            dtime2=%s,
            dmem2=%s,
            dtime3=%s,
            dmem3=%s,
            attribut_ori=%s,
            attribut_uni=%s,
            attribut_loss=%s,
            compression_ratio=%s,
            ast_original=%s,
            ast_unified=%s,
            var_original=%s::jsonb,
            func_original=%s::jsonb,
            var_unified=%s::jsonb,
            func_unified=%s::jsonb,
            f1=%s,
            precision=%s,
            recall=%s,
            ast_status=1,
            ast_error=NULL,
            pec_score=%s,
            pec_score_all=%s,
            pec_data=%s::jsonb
        WHERE id=%s
    """
    psycopg2.extras.execute_batch(cur, query, rows, page_size=len(rows))
    conn.commit()
    cur.close()
    conn.close()


def flush_error_updates(lang, rows):
    if not rows:
        return

    table = get_table(lang)
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    query = f"""
        UPDATE {table}
        SET ast_status=-1, ast_error=%s
        WHERE id=%s
    """
    psycopg2.extras.execute_batch(cur, query, rows, page_size=len(rows))
    conn.commit()
    cur.close()
    conn.close()

def get_sim_value(x):
    if isinstance(x, dict):
        return x.get("similarity", x.get("sim"))
    return x
# ======================================================
# PROCESS 1 ROW (WORKER)
# ======================================================
def process_two(row,lang1,lang2):
    java_id, java_ast_unified, java_ast_ori, java_code, cs_id, cs_ast_unified, cs_ast_ori,cs_code = row
    global myparser

    # try:
    # ted, norm, sim = myparser.fast_similarity(json.loads(java_ast_unified), json.loads(cs_ast_unified))
    # ted = tree_edit_distance(json.loads(java_ast_unified), json.loads(cs_ast_unified))
    ted = cosine_similarity_strings(java_code, cs_code, ngram=2)
    norm = path_jaccard_similarity(json.loads(java_ast_unified), json.loads(cs_ast_unified))
    sim = ted_similarity(json.loads(java_ast_unified), json.loads(cs_ast_unified))
    sim2 = ted_similarity(json.loads(java_ast_unified), json.loads(cs_ast_ori))
    sim3 = ted_similarity(json.loads(java_ast_ori), json.loads(cs_ast_unified))
    sim4 = ted_similarity(json.loads(java_ast_ori), json.loads(cs_ast_ori))
    
    # print("TED:", ted)           # misalnya 1
    # print("Normalized:", norm)   # 1 / (3+3) = 0.1666
    # print("Similarity:", sim)  
    
    # update dataset table
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    INSERT_SQL = """
    INSERT INTO heval_matrix (
        language1,language2,ted,ted2,ted3,ted4,normal,similarity,func_id 
    ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
    ON CONFLICT (language1, language2, func_id) DO NOTHING;
    """        
    try :    
        cur.execute(INSERT_SQL, (
            lang1, lang2,
            get_sim_value(sim),
            get_sim_value(sim2),
            get_sim_value(sim3),
            get_sim_value(sim4),
            get_sim_value(norm),
            get_sim_value(ted),
            java_id
        ))
        conn.commit()
        cur.close()
        conn.close()

        return True

    except Exception as e:

        print("[WORKER ERROR]", e)
        print(f"",lang1,lang2,sim['similarity'], norm['similarity'], ted['similarity'], java_id)
        raise

# ======================================================
# MERGE NODE TYPES
# ======================================================
def merge_single_nodes(parser, worker_nodes):
    if worker_nodes is None:
        return
    for cat, lst in worker_nodes.items():
        for t in lst:
            parser.single_nodes[cat][t] += 1

# ======================================================
# SAVE FINAL NODES TO DB (PER LANGUAGE)
# ======================================================
def save_single_nodes_to_db(lang, parser):
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    rows = []
    for category, freq_map in parser.single_nodes.items():
        for node_type, count in freq_map.items():
            rows.append((lang, category, node_type, count))

    print(f"[SAVE NODES] lang={lang}, total={len(rows)}")

    if rows:
        psycopg2.extras.execute_batch(cur, """
            INSERT INTO nodes (language, category, node_type, count)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (language, category, node_type)
            DO UPDATE SET count = EXCLUDED.count
        """, rows)

    conn.commit()
    cur.close()
    conn.close()

# ======================================================
# COUNT PENDING
# ======================================================
def count_pending(lang, split):
    table = get_table(lang)

    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    query = f"""
        SELECT COUNT(*) 
        FROM {table}
        WHERE ast_status=0
    """

    cur.execute(query)
    total = cur.fetchone()[0]
    conn.close()
    return total

def count_pending_ctc(lang,lang2):
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    table1 = get_table(lang)
    table2 = get_table(lang2)

    query = f"""
        SELECT COUNT(*) 
        FROM {table1} cs
        INNER JOIN {table2} java on cs.id=java.id
        WHERE cs.ast_status=1
        AND java.ast_status=1
        AND NOT EXISTS (
            SELECT 1
            FROM heval_matrix m
            WHERE m.func_id=java.id
            AND (
                (m.language1=%s AND m.language2=%s)
                OR (m.language1=%s AND m.language2=%s)
            )
        )
    """

    cur.execute(query, (lang, lang2, lang2, lang))
    total = cur.fetchone()[0]
    conn.close()
    return total
# ======================================================
# MAIN PER LANGUAGE
# ======================================================
def process_db_language(lang, lang_id, ted=0, lang2=''):

    print(f"\n==================== LANGUAGE {lang.upper()} {lang2.upper()} [TED={ted}] ====================")

    main_parser = None
    if ted == 0:
        main_parser = Myparser()
        main_parser.setparser(lang_id)

        # PENTING: pakai parser global yg dipakai worker sebelumnya
        global myparser
        myparser = main_parser

    for split in ['heval']:
        print(f"\n=== PROCESSING SPLIT: {lang} - {lang2} [TED={ted}] ===")
        if ted == 0:
            total = count_pending(lang, split)
        else:
            total = count_pending_ctc(lang,lang2)

        if total == 0:
            print("No pending rows.")
            continue

        pbar = tqdm(total=total, desc=f"{lang}-{split}", unit="row")

        while True:
            if ted == 0:
                batch = fetch_batch(lang, split, BATCH_SIZE)
            else:
                batch = fetch_batch_ctc(lang, lang2)

            if not batch:
                break

            if ted == 0:
                success_rows = []
                error_rows = []
                for row in batch:
                    result = process_one(row, lang)
                    if result and result.get("ok"):
                        success_rows.append(result["update"])
                        merge_single_nodes(main_parser, result.get("nodes"))
                    elif result:
                        error_rows.append(result["error"])
                    pbar.update(1)
                flush_success_updates(lang, success_rows)
                flush_error_updates(lang, error_rows)
            else:
                for row in batch:
                    process_two(row, lang, lang2)
                    pbar.update(1)

        pbar.close()

    if ted == 0:
        print("[SAVE NODES]", lang)
        save_single_nodes_to_db(lang, main_parser)



# ======================================================
# DRIVER
# ======================================================
if __name__ == "__main__":
    import multiprocessing
    multiprocessing.set_start_method("spawn", force=True)

    # Jangan reset ast_status otomatis di setiap run. Kalau reset diperlukan,
    # jalankan SQL reset secara eksplisit supaya proses yang sudah selesai tidak
    # diparse ulang dari nol.
    # for lang in languages:
    #     if not (lang=='php' or lang =='cs' or lang == 'ruby'):            
    #         lang_id = languages.index(lang)
    #         process_db_language(lang, lang_id)
    
    # conn = psycopg2.connect(**DB_CONFIG)
    # cur = conn.cursor()
    # for lang in languages:
    #     if not (lang=='php' or lang =='cs' or lang == 'ruby'):   
    #         query = f"""
    #             UPDATE heval_{lang} SET ast_status=0;            
    #         """
    #         cur.execute(query)   
    #         conn.commit()
    # query = f"""
    #     TRUNCATE heval_matrix restart identity;            
    # """
    # cur.execute(query)  
    # conn.commit()
    # query = f"""
    #     ALTER SEQUENCE heval_matrix_id_seq RESTART WITH 1;            
    # """
    # cur.execute(query)  
    # conn.commit()
    # conn.close()
    print("\n=== PHASE 1 : GENERATE UNIFIED AST ====================================================")
    for lang in ACTIVE_LANGUAGES:
        langid1 = languages.index(lang)
        process_db_language(lang, langid1, 0)
    
    print("\n=== PHASE 2 : COUNT TED  ==============================================================")
    for lang, lang2 in combinations(ACTIVE_LANGUAGES, 2):
        langid1 = languages.index(lang)
        process_db_language(lang, langid1, 1, lang2)

    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    for lang in ACTIVE_LANGUAGES:
        query = f"""
            UPDATE heval_{lang} SET 
            ted=(SELECT avg(ted) FROM heval_matrix where func_id=heval_{lang}.id and (language1='{lang}' or language2='{lang}')),
            normal=(SELECT avg(normal) FROM heval_matrix where func_id=heval_{lang}.id and (language1='{lang}' or language2='{lang}')),
            similarity=(SELECT avg(similarity) FROM heval_matrix where func_id=heval_{lang}.id and (language1='{lang}' or language2='{lang}'));
        """
        cur.execute(query)   
        conn.commit()
    conn.close()
            
    # lang='cs'        
    # lang_id = languages.index(lang)
    # process_db_language(lang, lang_id,1)
    print("\n=== COMPLETE ===")
