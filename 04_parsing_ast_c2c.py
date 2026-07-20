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
BATCH_SIZE = 500
MAX_WORKERS = 4

# ======================================================
# GET TABLE NAME PER BAHASA
# ======================================================
def get_table(lang):
    return f"c2c_{lang}"

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
            WHERE split=%s AND ast_status=0
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

    cur.execute(query, (split, batch_size))
    rows = cur.fetchall()
    conn.commit()
    conn.close()
    return rows

# ======================================================
# Fetch pending rows
# ======================================================
def fetch_batch_ctc(split, batch_size=200):
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    query = f"""
        SELECT java.id as java_id,java.ast_unified as java_ast_unified, java.ast_original as java_ast_original, java.code as java_code, 
        cs.id as cs_id, cs.ast_unified as cs_ast_unified, cs.ast_original as cs_ast_original, cs.code as cs_code FROM c2c_cs cs 
        INNER JOIN c2c_java java on cs.id=java.id 
        WHERE cs.split=%s AND cs.ast_status=1
        ORDER BY cs.id
        LIMIT %s;
    """

    cur.execute(query, (split, batch_size))
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
            status=1,
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


# ======================================================
# PROCESS 1 ROW (WORKER)
# ======================================================
def process_two(row):
    java_id, java_ast_unified,java_ast_original, java_code, cs_id, cs_ast_unified, cs_ast_original, cs_code= row
    global myparser
    table1 = "c2c_java"
    table2 = "c2c_cs"


    try:
        # ted, norm, sim = myparser.fast_similarity(json.loads(java_ast_unified), json.loads(cs_ast_unified))
        # ted = tree_edit_distance(json.loads(java_ast_unified), json.loads(cs_ast_unified))
        jau=json.loads(java_ast_unified)
        cau=json.loads(cs_ast_unified)
        jao=json.loads(java_ast_original)
        cao=json.loads(cs_ast_original)
        ted = cosine_similarity_strings(java_code, cs_code, ngram=3)
        norm = path_jaccard_similarity(jau, cau)
        sim = ted_similarity(jau,cau)
        sim2 = ted_similarity(jau,cao)
        sim3 = ted_similarity(jao,cau)
        sim4 = ted_similarity(jao,cao)
        comp_ratio1 = ast_compression_ratio(jao,jau)
        comp_ratio2 = ast_compression_ratio(cao,cau)
        # print("TED:", ted)           # misalnya 1
        # print("Normalized:", norm)   # 1 / (3+3) = 0.1666
        # print("Similarity:", sim)  
        
        # update dataset table
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        query1 = f"""
            UPDATE {table1} SET   
                compression_ratio=%s,
                ted=%s,
                ted2=%s,
                ted3=%s,
                ted4=%s,
                normal=%s,
                similarity=%s,
                status=2,
                ast_status=2             
            WHERE id=%s
        """
        query2 = f"""
            UPDATE {table2} SET                
                compression_ratio=%s,
                ted=%s,
                ted2=%s,
                ted3=%s,
                ted4=%s,
                normal=%s,
                similarity=%s,
                status=2,
                ast_status=2                
            WHERE id=%s
        """

        cur.execute(query1, (          
            comp_ratio1['compression_ratio'], sim['similarity'],sim2['similarity'],sim3['similarity'],sim4['similarity'], norm['similarity'], ted['similarity'], java_id
        ))
        conn.commit()
        cur.execute(query2, (          
           comp_ratio2['compression_ratio'], sim['similarity'],sim3['similarity'],sim2['similarity'],sim4['similarity'], norm['similarity'], ted['similarity'], cs_id
        ))
        conn.commit()

        
        cur.close()
        conn.close()

        return {
            "original": cs_ast_unified,
            "standart": java_ast_unified,
            "removed": norm,
            "single_child": sim
        }

    except Exception as e:

        # mark row as failed
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        query = f"""
            UPDATE {table1}
            SET ast_status=-2, ast_error=%s
            WHERE id=%s
        """
        cur.execute(query, (str(e), java_id))
        conn.commit()
        query = f"""
            UPDATE {table2}
            SET ast_status=-2, ast_error=%s
            WHERE id=%s
        """
        cur.execute(query, (str(e), cs_id))
        conn.commit()
        cur.close()
        conn.close()

        print("[WORKER ERROR]", e)
        return None

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
        WHERE split=%s AND ast_status=0
    """

    cur.execute(query, (split,))
    total = cur.fetchone()[0]
    conn.close()
    return total

def count_pending_ctc(split):
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    query = f"""
        SELECT COUNT(*) 
        FROM c2c_cs
        WHERE split=%s AND ast_status=1
    """

    cur.execute(query, (split,))
    total = cur.fetchone()[0]
    conn.close()
    return total
# ======================================================
# MAIN PER LANGUAGE
# ======================================================
def process_db_language(lang, lang_id,ted=0):

    print(f"\n==================== LANGUAGE {lang.upper()} ====================")

    main_parser = Myparser()
    main_parser.setparser(lang_id)

    for split in splits:
        print(f"\n=== PROCESSING SPLIT: {split} ===")
        if ted==0:
            total = count_pending(lang, split)
        else:
            total = count_pending_ctc(split)
        if total == 0:
            print("No pending rows.")
            continue

        pbar = tqdm(total=total, desc=f"{lang}-{split}", unit="row")

        with ProcessPoolExecutor(
            max_workers=MAX_WORKERS,
            initializer=init_worker,
            initargs=(lang_id,)
        ) as ex:
            while True:
                if ted==0:
                    batch = fetch_batch(lang, split)
                else:
                    batch = fetch_batch_ctc(split)
                
                if not batch:
                    break

                if ted==0:
                    futures = [ex.submit(process_one, row, lang) for row in batch]
                else:
                    futures = [ex.submit(process_two, row) for row in batch]

                success_rows = []
                error_rows = []
                for future in as_completed(futures):
                    result = future.result()
                    if ted == 0:
                        if result and result.get("ok"):
                            success_rows.append(result["update"])
                            merge_single_nodes(main_parser, result.get("nodes"))
                        elif result:
                            error_rows.append(result["error"])
                    else:
                        merge_single_nodes(main_parser, result)
                    pbar.update(1)

                if ted == 0:
                    flush_success_updates(lang, success_rows)
                    flush_error_updates(lang, error_rows)

        pbar.close()

    print("[SAVE NODES]", lang)
    save_single_nodes_to_db(lang, main_parser)


# ======================================================
# DRIVER
# ======================================================
if __name__ == "__main__":
    import multiprocessing
    multiprocessing.set_start_method("spawn", force=True)
    print("\n=== PHASE 1 : GENERATE UNIFIED AST ====================================================")
    for lang in languages:
        if lang=='java' or lang=='cs':
            lang_id = languages.index(lang)
            process_db_language(lang, lang_id)
    
    print("\n=== PHASE 2 : COUNT TED  ==============================================================")
    for lang in languages:
        if lang=='java' or lang=='cs':
            lang_id = languages.index(lang)
            process_db_language(lang, lang_id,1)
            
    # lang='cs'        
    # lang_id = languages.index(lang)
    # process_db_language(lang, lang_id,1)
    print("\n=== COMPLETE ===")
