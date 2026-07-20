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

start_time = 0
baseline_time = 0
end_time = 0
baseline_memory =0
full_memory = 0
BATCH_SIZE = 500
MAX_WORKERS = 4

# ======================================================
# GET TABLE NAME PER BAHASA
# ======================================================
def get_table(lang):
    return f"c2t_{lang}"

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
def fetch_batch(lang, split, batch_size=200):
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
        RETURNING t.id, t.code, t.docstring;
    """

    cur.execute(query, (split, batch_size))
    rows = cur.fetchall()
    conn.commit()
    conn.close()
    return rows

# ======================================================
# PROCESS 1 ROW (WORKER)
# ======================================================
def process_one(row, lang):
    rid, code, docstring = row
    global myparser

    try:
        code = code.strip()
        source = code.encode("utf8")

        # start extract AST
        tracemalloc.start()
        start_time = time.perf_counter()        
        ast_tree = myparser.parse_code_to_ast(code)
        ast_ori = myparser.node_to_dict(ast_tree.root_node, source)
        # stop extract AST
        
        baseline_time = time.perf_counter() - start_time
        current, peak = tracemalloc.get_traced_memory()
        baseline_memory = peak
        start_time = time.perf_counter()  
        # start konversi UAST
        ast_uni = myparser.node_to_dict_unified(ast_tree.root_node, source)
        ast_uni = myparser.simplify_ast_use_deepest_root(ast_uni)
        # end konversi ast
        
        full_time = baseline_time+(time.perf_counter() - start_time)
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
        loss = attribute_loss(ast_ori, ast_uni)
        myparser.extract_identifiers(ast_ori, vars1, funcs1)
        myparser.extract_identifiers(ast_uni, vars2, funcs2)

        pr = myparser.precision_recall(vars1 | funcs1, vars2 | funcs2)

        # === Node type extraction ===
        node_ori = []
        node_std = []
        node_removed = []
        node_single = []

        myparser.collect_original_types(ast_ori, node_ori)
        myparser.collect_standart_types(ast_uni, node_std)
        comp_ratio1 = ast_compression_ratio(ast_ori,ast_uni)
        myparser.collect_removed_types(ast_ori, ast_uni, node_removed)
        myparser.collect_single_child_types(ast_ori, node_single)
        pec_result = myparser.calculate_pec(ast_ori, ast_uni)
    
   
    # print("Language:", myparser.lang)
    # print("PEC:", pec_result["pec"])

        return {
            "ok": True,
            "update": (
                baseline_time, baseline_memory,
                full_time, full_memory,
                time_overhead, memory_overhead,
                time_overhead_percent, memory_overhead_percent,
                loss['attributes_original'], loss['attributes_unified'], loss['attribute_loss'],
                comp_ratio1['compression_ratio'],
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

# ======================================================
# MAIN PER LANGUAGE
# ======================================================
def process_db_language(lang, lang_id):

    print(f"\n==================== LANGUAGE {lang.upper()} ====================")

    main_parser = Myparser()
    main_parser.setparser(lang_id)

    for split in splits:
        print(f"\n=== PROCESSING SPLIT: {split} ===")

        total = count_pending(lang, split)
        if total == 0:
            print("No pending rows.")
            continue

        pbar = tqdm(total=total, desc=f"{lang}-{split}", unit="row")

        with ProcessPoolExecutor(
            max_workers=4,
            initializer=init_worker,
            initargs=(lang_id,)
        ) as ex:
            while True:
                batch = fetch_batch(lang, split, BATCH_SIZE)
                if not batch:
                    break

                futures = [ex.submit(process_one, row, lang) for row in batch]
                success_rows = []
                error_rows = []
                for future in as_completed(futures):
                    result = future.result()
                    if result and result.get("ok"):
                        success_rows.append(result["update"])
                        merge_single_nodes(main_parser, result.get("nodes"))
                    elif result:
                        error_rows.append(result["error"])
                    pbar.update(1)

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

    for lang in languages:
        lang_id = languages.index(lang)
        process_db_language(lang, lang_id)

    print("\n=== COMPLETE ===")
