import os
import json
from parserfunc import Myparser
from constant import languages, splits

def flatten_ast_2(ast_dict):
    tokens = []
    def traverse(node):
        node_type = node.get("type", "")
        children = node.get("children", [])
        text = node.get("text", "").strip()
        if not children:
            if text and text not in [";", ")", "(", "{", "}", ","]:
                tokens.append(f"{node_type}:{text}")
            else:
                tokens.append(node_type)
        else:
            tokens.append(node_type)
            for child in children:
                traverse(child)
    traverse(ast_dict)
    return " ".join(tokens)

def flatten_ast(node):
    #return node.get("type", "").replace('\n', ' ').replace('\r', '')
    node_type = node.get("type", "")
    children = node.get("children", [])
    text = node.get("text", "").strip()

    if not children:
        if text and text not in [";", ")", "(", "{", "}", ","]:
            return f"({node_type} {text})"
        return f"({node_type})"
    else:
        children_repr = " ".join([flatten_ast(child) for child in children])
        return f"({node_type} {children_repr})"

def clean_text(text):
    try:
        str = " ".join(text.strip().split())
    except Exception:
        str = " ".join(text)
    return str    

def process_split_jsonl(langid, split_name):
    lang = languages[langid]
    parser = Myparser()
    parser.setparser(langid)

    base_path = f"../../disertasi_datasets/codexglue/{lang}/"
    input_jsonl_path = os.path.join(base_path, f"{split_name}.jsonl")

    output_code_path         = os.path.join(base_path, f"{split_name}.code.original")
    output_docstring_path    = os.path.join(base_path, f"{split_name}.docstring")
    output_ast_original_path = os.path.join(base_path, f"{split_name}.code.ast-original")
    output_ast_unified_path  = os.path.join(base_path, f"{split_name}.code.ast-unified")

    if not os.path.exists(input_jsonl_path):
        print(f"[SKIP] File tidak ditemukan: {input_jsonl_path}")
        return

    # Hitung total baris input
    with open(input_jsonl_path, "r", encoding="utf-8") as f:
        total_lines = sum(1 for _ in f)
    print(f"[INFO] Memproses {lang.upper()} - {split_name}.jsonl")
    print(f"[INFO] Total baris di {split_name}.jsonl: {total_lines}")

    # Hitung jumlah baris yang sudah diproses sebelumnya
    if os.path.exists(output_code_path):
        with open(output_code_path, "r", encoding="utf-8") as f:
            processed_lines = sum(1 for _ in f)
    else:
        processed_lines = 0

    
    print(f"[INFO] Melanjutkan dari baris ke-{processed_lines + 1}")

    buffer_code = []
    buffer_doc = []
    buffer_ast_orig = []
    buffer_ast_unif = []

    total, success, gagal = 0, 0, 0

    with open(input_jsonl_path, "r", encoding="utf-8") as fin:
        for idx, line in enumerate(fin):
            total += 1

            # Skip jika sudah diproses
            if idx < processed_lines:
                continue

            try:
                data = json.loads(line)
                code = clean_text(data["code"])
                docstring = clean_text(data.get("docstring", ""))

                try:
                    tree = parser.parse_code_to_ast(code)
                except Exception:
                    gagal += 1
                    continue

                if tree:
                    try:
                        ast_orig = parser.node_to_dict(tree.root_node, code.encode("utf-8"))
                    except Exception:
                        gagal += 1
                        continue

                if ast_orig:
                    ast_orig_flat = flatten_ast(ast_orig)

                    try:
                        ast_unified = parser.node_to_dict_unified(tree.root_node, code.encode("utf-8"))
                    except Exception:
                        gagal += 1
                        continue

                    if ast_unified:
                        try:
                            ast_unified_flat = flatten_ast(ast_unified)
                        except Exception:
                            gagal += 1
                            continue

                        if all([ast_unified_flat.strip(), ast_orig_flat.strip(), docstring.strip()]):
                            buffer_code.append(code)
                            buffer_doc.append(docstring.strip())
                            buffer_ast_orig.append(ast_orig_flat.strip())
                            buffer_ast_unif.append(ast_unified_flat.strip())
                            success += 1
                            if success % 2000 == 0:
                                print(f"{processed_lines+success}", end="")
                            if success % 5000 == 0:
                                print(f"{lang}/{split_name}-{processed_lines+success} of {total_lines}", end="")
                                # print(ast_unified_flat.strip())
                            if success % 100 == 0:
                                print(".", end="")
                            if success % 10 == 0:
                                #print(f"[INFO] Menyimpan batch ke file (total sukses: {processed_lines+success})")
                                with open(output_code_path, "a", encoding="utf-8") as f:
                                    f.write("\n".join(buffer_code) + "\n")
                                with open(output_docstring_path, "a", encoding="utf-8") as f:
                                    f.write("\n".join(buffer_doc) + "\n")
                                with open(output_ast_original_path, "a", encoding="utf-8") as f:
                                    f.write("\n".join(buffer_ast_orig) + "\n")
                                with open(output_ast_unified_path, "a", encoding="utf-8") as f:
                                    f.write("\n".join(buffer_ast_unif) + "\n")

                                buffer_code.clear()
                                buffer_doc.clear()
                                buffer_ast_orig.clear()
                                buffer_ast_unif.clear()

            except Exception as e:
                gagal += 1
                print(f"[ERROR] {lang}/{split_name} line {idx+1}: {e}")
                continue

    # Simpan sisa buffer terakhir
    if buffer_code:
        print(f"[INFO] Menyimpan sisa akhir ({len(buffer_code)} baris)")
        with open(output_code_path, "a", encoding="utf-8") as f:
            f.write("\n".join(buffer_code) + "\n")
        with open(output_docstring_path, "a", encoding="utf-8") as f:
            f.write("\n".join(buffer_doc) + "\n")
        with open(output_ast_original_path, "a", encoding="utf-8") as f:
            f.write("\n".join(buffer_ast_orig) + "\n")
        with open(output_ast_unified_path, "a", encoding="utf-8") as f:
            f.write("\n".join(buffer_ast_unif) + "\n")

    print(f"[DONE] {success}/{gagal}/{total} baris diproses untuk {lang}/{split_name} (dari baris {processed_lines+1})")


if __name__ == "__main__":
    for langid in range(len(languages)):
        lang = languages[langid]
        print(f"\n====== MEMULAI: {lang.upper()} ======")
        for split_name in splits:
            input_path = f"../../disertasi_datasets/codexglue/{lang}/"
            if not os.path.exists(input_path):
                print(f"[SKIP] {lang}/ tidak ditemukan.")
                continue
            process_split_jsonl(langid, split_name)
