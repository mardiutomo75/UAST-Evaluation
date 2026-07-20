from fastapi import FastAPI
from pydantic import BaseModel
from parserfunc import Myparser
import json
from constant import *
from fastapi.middleware.cors import CORSMiddleware
import traceback


app = FastAPI(title="AST Extraction API", version="1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      # Bisa dibatasi menjadi ["http://localhost:8080"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

parser = Myparser()


class ASTRequest(BaseModel):
    code: str
    language: str  # 0–5 sesuai indeks parser Anda


@app.post("/extract_ast")
def extract_ast(data: ASTRequest):
    lang_id = languages.index(data.language)
    parser.setparser(lang_id)
    code = data.code

    # Parse code → AST
    ast_tree = parser.parse_code_to_ast(code)
    ast_dict = parser.node_to_dict(ast_tree.root_node, code.encode("utf-8"))

    return {
        "language": parser.lang,
        "ast_original": ast_dict
    }


@app.post("/extract_unified_ast")
def extract_unified_ast(data: ASTRequest):
    try:
        lang_id = languages.index(data.language)
        parser.setparser(lang_id)
        code = data.code

        ast_tree = parser.parse_code_to_ast(code)
        ast_unified = parser.node_to_dict_unified(ast_tree.root_node, code.encode("utf-8"))
        ast_unified = parser.simplify_ast_use_deepest_root(ast_unified)

        return {
            "language": parser.lang,
            "ast_unified": json.dumps(ast_unified,indent=2, ensure_ascii=False)
        }
    except Exception as e:
        print("ERROR:", e)
        traceback.print_exc()
        return {"error": str(e)}


@app.post("/extract_both")
def extract_both(data: ASTRequest):
    
    lang_id = languages.index(data.language)
    parser.setparser(lang_id)
    code = data.code

    ast_tree = parser.parse_code_to_ast(code)

    # AST biasa
    ast_normal = parser.node_to_dict(ast_tree.root_node, code.encode("utf-8"))

    # Unified AST
    ast_unified = parser.node_to_dict_unified(ast_tree.root_node, code.encode("utf-8"))
    ast_unified = parser.simplify_ast_use_deepest_root(ast_unified)

    # extract variables/functions
    vars1, funcs1 = set(), set()
    vars2, funcs2 = set(), set()

    parser.extract_identifiers(ast_normal, vars1, funcs1)
    parser.extract_identifiers(ast_unified, vars2, funcs2)

    pr = parser.precision_recall(vars1, vars2)
   
    return {
        "language": parser.lang,
        "ast_original": ast_normal,
        "ast_unified": ast_unified,
        "var_original":list(vars1),
        "func_original":list(funcs1),
        "var_unified":list(vars2),
        "func_unified":list(funcs2),
        "dfg_f1": pr["f1"],
        "dfg_recall": pr["recall"],
        "dfg_precision": pr["precision"]
    }
