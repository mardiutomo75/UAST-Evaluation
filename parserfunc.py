from __future__ import annotations

from operator import add
from tree_sitter import Language, Parser
import tree_sitter_python as tspython
import tree_sitter_php as tsphp
import tree_sitter_java as tsjava
import tree_sitter_javascript as tsjavascript
import tree_sitter_go as tsgo
import tree_sitter_ruby as tsruby
import tree_sitter_c_sharp as tscs
import tree_sitter_cpp as tscpp
import tree_sitter_rust as tsrust

from constant import *

import json
import re
import os
import math
import nltk

from dataclasses import dataclass
from collections import defaultdict, Counter
from typing import Dict, Any, List, Callable, Tuple, Optional, Sequence, Set

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction


languages = LANGUAGES

PEC_TYPE_TEXTS = {
    "int", "integer", "float", "double", "long", "decimal", "bool",
    "boolean", "char", "byte", "short", "void", "string",
}

_PEC_CATEGORIES_CACHE: Optional[List[str]] = None
_PEC_VALID_CATEGORIES_CACHE: Optional[Set[str]] = None
_PEC_NODE_GROUPS_CACHE: Dict[str, Dict[str, Set[str]]] = {}
_PEC_NODE_TO_CATEGORIES_CACHE: Dict[str, Dict[str, Set[str]]] = {}
_PEC_CATEGORIZED_NODES_CACHE: Dict[str, Set[str]] = {}


def _build_reserved_words_list():
    lst = []
    for lg in languages:
        kws = set(RESERVED_COMMON)
        kws.update(RESERVED_BY_LANG.get(lg, []))
        lst.append(sorted(kws))
    return lst


RESERVED_WORDS = _build_reserved_words_list()


def ast_label_type_only(node: Dict[str, Any]) -> str:
    return str(node.get("type", ""))


def default_cost_delete(label: str) -> int:
    return 1


def default_cost_insert(label: str) -> int:
    return 1


def default_cost_replace(label1: str, label2: str) -> int:
    return 0 if label1 == label2 else 1


class Myparser:
    langid = 5
    lang = languages[langid]
    PY_LANGUAGE = Language(tsjavascript.language())
    parser = Parser(PY_LANGUAGE)

    array_type = {}
    array_var = {}
    array_func = {}
    nodemaps = {}
    noderemoves = {}
    nodeskips = {}

    single_nodes = defaultdict(lambda: defaultdict(int))
    removed_nodes = defaultdict(int)
    standart_nodes = defaultdict(int)

    max_depth = 50

    def normalize_text(self, txt):
        if txt is None:
            return ""

        if not isinstance(txt, str):
            txt = str(txt)

        txt = txt.replace("\r\n", "\n").replace("\r", "\n")
        txt = txt.replace("\t", " ").strip()
        txt = re.sub(r"[ ]{2,}", " ", txt)
        return txt

    def normalize_node_type(self, tipe: str) -> str:
        if not tipe:
            return ""
        tipe = tipe.replace("$", "").strip().lower()
        tipe = OPERATORS_NORMALIZE.get(tipe, tipe)
        return self.nodemaps.get(tipe, tipe)

    def __init__(self):
        self.nodemaps = dict(ALIAS_TO_CANONICAL)
        self.noderemoves = self.expand_node_mapping(NODE_REMOVE)
        self.noderemoves[","] = ""
        self.nodeskips = self.expand_node_mapping(NODE_SKIP)

        self.single_nodes = defaultdict(lambda: defaultdict(int))
        self.removed_nodes = defaultdict(int)
        self.standart_nodes = defaultdict(int)
        self.reserved_set = set(RESERVED_COMMON) | set(RESERVED_BY_LANG.get(self.lang, []))

        self.array_type = {}
        self.array_var = {}
        self.array_func = {}

    def calculate_bleu_score(self, original_code, reconstructed_code):
        original_tokens = nltk.word_tokenize(original_code)
        reconstructed_tokens = nltk.word_tokenize(reconstructed_code)
        smooth = SmoothingFunction().method1
        bleu_score = sentence_bleu([original_tokens], reconstructed_tokens, smoothing_function=smooth)
        return bleu_score

    def setparser(self, langid=5):
        self.langid = langid
        self.single_nodes = defaultdict(lambda: defaultdict(int))
        self.removed_nodes = defaultdict(int)
        self.standart_nodes = defaultdict(int)

        lang = languages[self.langid]
        self.lang = lang

        if lang == "php":
            PY_LANGUAGE = Language(tsphp.language_php_only())
        elif lang == "python":
            PY_LANGUAGE = Language(tspython.language())
        elif lang == "go":
            PY_LANGUAGE = Language(tsgo.language())
        elif lang == "ruby":
            PY_LANGUAGE = Language(tsruby.language())
        elif lang == "java":
            PY_LANGUAGE = Language(tsjava.language())
        elif lang == "javascript":
            PY_LANGUAGE = Language(tsjavascript.language())
        elif lang == "cs":
            PY_LANGUAGE = Language(tscs.language())
        elif lang == "cpp":
            PY_LANGUAGE = Language(tscpp.language())
        elif lang == "rust":
            PY_LANGUAGE = Language(tsrust.language())
        else:
            raise ValueError(f"Unsupported language: {lang}")

        try:
            self.parser = Parser(PY_LANGUAGE)
        except ValueError as exc:
            if "Language version" in str(exc):
                raise ValueError(
                    f"{exc}. Jalankan script dengan Miniconda env codesearchnet-prep: "
                    "$HOME/miniconda3/envs/codesearchnet-prep/bin/python <script.py>"
                ) from exc
            raise
        self.reserved_set = set(RESERVED_COMMON) | set(RESERVED_BY_LANG.get(self.lang, []))
        self.VARIABLE_NODES = VARIABLES_NODES[self.lang]
        self.FUNCTION_NODES = FUNCTIONS_NODES[self.lang]

    def is_valid_string(self, s):
        pattern = r"^[a-zA-Z0-9-_]+$"
        if not re.match(pattern, s):
            return False
        if not re.search(r"[a-zA-Z]", s):
            return False
        return True

    def parse_code_to_ast(self, code):
        try:
            code = code.encode("utf8")
            tree = self.parser.parse(code)
        except Exception:
            tree = None
        return tree

    def flatten_ast(self, ast_dict, level=0):
        line = f"{'  ' * level}- {ast_dict['type']}: {ast_dict['text']}"
        lines = [line]
        for child in ast_dict.get("children", []):
            lines.append(self.flatten_ast(child, level + 1))
        return "\n".join(lines)

    def node_to_dict(self, node, source_code, array_type=None, visited=None, depth=0):
        if visited is None:
            visited = set()
        if id(node) in visited:
            return None
        visited.add(id(node))

        if depth > self.max_depth:
            return None

        if not hasattr(self, "array_type") or self.array_type is None:
            self.array_type = {}

        tipe = node.type

        if self.is_valid_string(tipe):
            self.array_type[tipe] = self.array_type.get(tipe, 0) + 1

        children_list = []
        for child in getattr(node, "children", []):
            ch_dict = self.node_to_dict(child, source_code, array_type, visited, depth + 1)
            if ch_dict is not None:
                children_list.append(ch_dict)

        try:
            teks = source_code[node.start_byte:node.end_byte].decode("utf8")
            teks = self.normalize_text(teks)
        except Exception:
            teks = ""

        return {
            "type": tipe,
            "text": teks,
            "children": children_list,
        }

    def node_to_dict_unified(self, node, source_code, visited=None, depth=0):
        if node is None:
            return None

        if visited is None:
            visited = set()

        key = (id(node), depth)
        if key in visited:
            return None
        visited.add(key)

        if depth > self.max_depth:
            return None

        if hasattr(node, "children") and len(node.children) > 500:
            return None

        raw_type = (node.type or "").strip()
        raw_type_l = raw_type.lower()

        try:
            raw_text = source_code[node.start_byte:node.end_byte].decode("utf8")
        except Exception:
            raw_text = ""

        raw_text = raw_text.replace("$", "").replace("@", "")
        raw_text = raw_text.strip(";")
        text = self.normalize_text(raw_text)

        canonical_type = self.normalize_node_type(raw_type_l)
        is_type_node = canonical_type == "type"
        
        if text.lower().strip() in self.noderemoves and not is_type_node:
            return None
        if canonical_type.lower().strip() in self.noderemoves and not is_type_node:
            return None

        raw_children = []
        max_child = 300

        for i, child in enumerate(getattr(node, "children", [])):
            if i >= max_child:
                break
            child_dict = self.node_to_dict_unified(child, source_code, visited, depth + 1)
            if child_dict is not None:
                raw_children.append(child_dict)

        valid_children = [
            ch for ch in raw_children
            if isinstance(ch, dict) and (
                (ch.get("type") or "").strip() != "" or
                (ch.get("text") or "").strip() != "" or
                len(ch.get("children", [])) > 0
            )
        ]

        if len(valid_children) == 1 and canonical_type not in {"module", "program", "source_file"}:
            only_child = valid_children[0]

            def normalize_cmp(s):
                if not s:
                    return ""
                return (
                    s.replace(" ", "")
                    .replace("\t", "")
                    .replace("\n", "")
                    .replace("(", "")
                    .replace(")", "")
                    .rstrip(";")
                )

            if normalize_cmp(text) == normalize_cmp(only_child.get("text", "")):
                return only_child

        punctuation_like = {'"', "'","<",">", "(", ")", "{", "}", "[", "]", ",", ".", ":", ";", "...", "=","."}
        if raw_type_l in punctuation_like and (text == "" or  text == raw_type_l) and not valid_children:
            return None
            
        if canonical_type == "" and text == "" and not valid_children:
            return None

        if raw_type_l in self.nodeskips and valid_children:
            if len(valid_children) == 1:
                return valid_children[0]
            return {
                "type": "expression",
                "text": text,
                "children": valid_children,
            }

        

        final_type = canonical_type if canonical_type else raw_type_l

        return {
            "type": final_type,
            "text": text,
            "children": valid_children,
        }

    def save_ast_to_json(self, code, filename=""):
        tree = self.parse_code_to_ast(code)
        ast_dict = self.node_to_dict(tree.root_node, code.encode("utf8"))
        if filename != "":
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(ast_dict, f, indent=4)
        return ast_dict

    def save_ast_to_json_unified(self, code, filename=""):
        tree = self.parse_code_to_ast(code)
        ast_dict = self.node_to_dict_unified(tree.root_node, code.encode("utf8"))
        if filename != "":
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(ast_dict, f, indent=4)
        return ast_dict

    def reconstruct_code_from_ast(self, ast_dict):
        if not ast_dict:
            return ""
        if "text" in ast_dict and ast_dict["text"]:
            return ast_dict["text"].strip()
        return "".join(self.reconstruct_code_from_ast(child) for child in ast_dict.get("children", []))

    def calculate_cosine_similarity(self, text1, text2):
        vectorizer = TfidfVectorizer()
        tfidf_matrix = vectorizer.fit_transform([text1, text2])
        cosine_sim = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])
        return cosine_sim[0][0]

    def validate_var(self, var_name, functions):
        if not re.search(r"[a-zA-Z]", var_name):
            return False
        return (
            var_name not in functions
            and var_name not in self.FUNCTION_NODES
            and var_name not in KEY_NODES
        )

    def validate_func(self, func_name):
        return (
            self.is_valid_string(func_name)
            and func_name not in self.FUNCTION_NODES
            and func_name not in KEY_NODES
        )

    def extract_identifiers(self, ast_dict, variables=None, functions=None, type_before="", visited=None, depth=0):
        if ast_dict is None:
            return variables, functions

        if variables is None:
            variables = set()
        if functions is None:
            functions = set()
        if visited is None:
            visited = set()

        key = id(ast_dict)
        if key in visited:
            return variables, functions
        visited.add(key)

        if depth > self.max_depth:
            return variables, functions

        node_type = ast_dict.get("type", "")
        teks = ast_dict.get("text", "")
        children = ast_dict.get("children", [])

        CLEAN_NAME_RE = re.compile(r"\s+|[^A-Za-z0-9_:-]")
        VALID_VAR_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_-]*$")

        def clean_name(s):
            if not isinstance(s, str):
                return ""
            if '<' in s and '>' in s  and self.lang=='cs':
                return ""
            if self.lang=='php':
                return s
            return CLEAN_NAME_RE.sub("", s)

        def add_column(var_name):
            if var_name and VALID_VAR_RE.fullmatch(var_name):
                cek = var_name.lower()
                if (
                    cek not in IGNORE_NODES
                    and cek not in RESERVED_BY_LANG[self.lang]
                    and cek not in WRAPPER_CANDIDATES
                    and cek not in self.noderemoves
                    and cek not in reserved_set
                    and validate_var(var_name, functions)
                ):
                    variables.add(var_name)
                    array_var[var_name] = array_var.get(var_name, 0) + 1

        validate_var = self.validate_var
        reserved_set = self.reserved_set
        array_var = self.array_var

        if node_type in self.VARIABLE_NODES and not children:
            var_name = clean_name(ast_dict.get("text", ""))
            add_column(var_name)

        elif node_type in self.VARIABLE_NODES and children:
            for ch in children:
                chtype = ch.get("type", "")
                var_name = clean_name(ch.get("text", ""))

                if chtype not in self.VARIABLE_NODES:
                    add_column(var_name)
                    continue

                if not var_name or not VALID_VAR_RE.fullmatch(var_name):
                    continue

        elif (node_type in self.FUNCTION_NODES or node_type in CALL_NODES) and not any(
            x in teks.lower() for x in ["public", "private", "new"]
        ):
            fnvalid = 1;
            for ch in children:
                chtype = ch.get("type", "")
                if not isinstance(chtype, str) or chtype.strip().lower() not in self.VARIABLE_NODES:
                    continue

                if chtype=='parameter':
                    fnvalid = 0
                    continue

                fn = clean_name(ch.get("text", ""))
                if not fn or ":" in fn or not VALID_VAR_RE.fullmatch(fn):
                    continue

                cek = fn.lower()
                if (
                    cek not in IGNORE_NODES
                    and fnvalid == 1
                    and cek not in self.noderemoves
                    and cek not in reserved_set
                    and validate_var(fn, variables)
                ):
                    functions.add(fn)

        for ch in children:
            self.extract_identifiers(
                ch,
                variables=variables,
                functions=functions,
                type_before=node_type,
                visited=visited,
                depth=depth + 1,
            )

        return variables, functions

    def validate_ast_roundtrip(self, code, filename=""):
        if filename != "" and os.path.exists(filename):
            with open(filename, "r", encoding="utf-8") as f:
                ast_dict = json.load(f)
        else:
            ast_dict = self.save_ast_to_json_unified(code, filename)

        reconstructed_code = self.reconstruct_code_from_ast(ast_dict).strip()
        similarity_score = 1
        bleu_score = 1
        return ast_dict, similarity_score, reconstructed_code, bleu_score

    def analyze_code_variables_and_functions(self, ast_dict):
        variables, functions = self.extract_identifiers(ast_dict)
        return variables, functions

    def expand_node_mapping(self, node_mapping):
        expanded = {}
        for keys, value in node_mapping.items():
            for key in keys.split(","):
                expanded[key.strip()] = value.strip()
        return expanded

    def ast_to_bracketed(self, ast: dict) -> str:
        def traverse(node):
            if not node:
                return ""

            node_type = node.get("type", "")
            text = node.get("text", "").strip()
            children = node.get("children", [])

            if children:
                label = node_type
            else:
                if node_type in ["variable", "integer", "number"]:
                    label = f"{node_type}:{text}"
                else:
                    label = text if text else node_type

            if children:
                return "(" + label + " " + " ".join(traverse(c) for c in children if c) + ")"
            return label

        return traverse(ast)

    def get_deepest_root(self, ast: dict, wrapper_candidates: set = None, depth=0) -> dict:
        if not isinstance(ast, dict):
            raise TypeError("AST harus berupa dict.")
        if "children" not in ast:
            ast["children"] = []

        wrappers = wrapper_candidates or WRAPPER_CANDIDATES

        cur = ast
        path = [cur.get("type", "?")]
        visited = set()
        while True:
            children = cur.get("children") or []
            if (cur.get("type") not in wrappers) or (len(children) != 1):
                break
            cur = children[0]
            if id(cur) in visited:
                break
            visited.add(id(cur))
            path.append(cur.get("type", "?"))

        cur.setdefault("meta", {})
        cur["meta"].setdefault("deepest_root_from", path)
        return cur

    def simplify_ast_use_deepest_root(self, ast: dict, wrapper_candidates: set = None) -> dict:
        deepest = self.get_deepest_root(ast, wrapper_candidates)
        return deepest

    def norm(self, s: str) -> str:
        return (s or "").strip().lower().replace("$", "")

    def precision_recall(self, truth: set, pred: set):
        truth = {self.norm(x) for x in truth}
        pred = {self.norm(x) for x in pred}

        if len(truth) == 0 and len(pred) == 0:
            precision = 1
            recall = 1
            f1 = 1
            tp = 1
            fp = 1
            fn = 1
            tp_items = truth & pred
            fp_items = pred - truth
            fn_items = truth - pred
        else:
            tp_items = truth & pred
            fp_items = pred - truth
            fn_items = truth - pred

            tp = len(tp_items)
            fp = len(fp_items)
            fn = len(fn_items)

            precision = tp / (tp + fp) if (tp + fp) else 0.0
            recall = tp / (tp + fn) if (tp + fn) else 0.0
            f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) else 0.0

        matrix = {
            "Truth +, Pred + (TP)": tp,
            "Truth -, Pred + (FP)": fp,
            "Truth +, Pred - (FN)": fn,
            "Truth -, Pred - (TN)": None,
        }

        return {
            "tp": tp,
            "fp": fp,
            "fn": fn,
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "tp_items": tp_items,
            "fp_items": fp_items,
            "fn_items": fn_items,
            "matrix": matrix,
        }

    def _postorder_info_fast(self, root: Dict[str, Any], label_fn: Callable[[Dict[str, Any]], str]):
        labels: List[str] = []
        llds: List[int] = []

        stack = [(root, False)]
        post_index = {}

        while stack:
            node, visited = stack.pop()
            children = node.get("children") or []
            if not visited:
                stack.append((node, True))
                for ch in reversed(children):
                    stack.append((ch, False))
            else:
                idx = len(labels)
                labels.append(label_fn(node))
                if not children:
                    llds.append(idx)
                post_index[id(node)] = idx

        last_for_lld = {}
        for i, l in enumerate(llds):
            last_for_lld[l] = i
        keyroots = sorted(last_for_lld.values())
        return labels, llds, keyroots

    def tree_edit_distance(
        self,
        ast_ori: Dict[str, Any],
        ast_std: Dict[str, Any],
        label_fn: Callable[[Dict[str, Any]], str] = ast_label_type_only,
        cost_del: Callable[[str], int] = default_cost_delete,
        cost_ins: Callable[[str], int] = default_cost_insert,
        cost_rep: Callable[[str, str], int] = default_cost_replace,
    ) -> int:
        labels1, llds1, keyroots1 = self._postorder_info_fast(ast_ori, label_fn)
        labels2, llds2, keyroots2 = self._postorder_info_fast(ast_std, label_fn)
        n1, n2 = len(labels1), len(labels2)

        subtree_dist = [[0] * n2 for _ in range(n1)]

        l1 = labels1
        l2 = labels2
        L1 = llds1
        L2 = llds2
        cd = cost_del
        ci = cost_ins
        cr = cost_rep

        memo = {}

        def forest_dist(i_start: int, j_start: int, i_end: int, j_end: int) -> int:
            key = (i_start, j_start, i_end, j_end)
            if key in memo:
                return memo[key]

            m = i_end - i_start + 1
            n = j_end - j_start + 1

            del_cost = [0] * m
            for ii in range(m):
                del_cost[ii] = cd(l1[i_start + ii])

            ins_cost = [0] * n
            for jj in range(n):
                ins_cost[jj] = ci(l2[j_start + jj])

            width = n + 1
            size = (m + 1) * (n + 1)
            fd = [0] * size

            acc = 0
            for i in range(1, m + 1):
                acc += del_cost[i - 1]
                fd[i * width + 0] = acc

            acc = 0
            for j in range(1, n + 1):
                acc += ins_cost[j - 1]
                fd[0 * width + j] = acc

            def get(i, j):
                return fd[i * width + j]

            def set_(i, j, v):
                fd[i * width + j] = v

            for i in range(1, m + 1):
                i_idx = i_start + i - 1
                lld_i = L1[i_idx]
                li = l1[i_idx]

                for j in range(1, n + 1):
                    j_idx = j_start + j - 1
                    lld_j = L2[j_idx]
                    lj = l2[j_idx]

                    best = get(i - 1, j) + del_cost[i - 1]
                    tmp = get(i, j - 1) + ins_cost[j - 1]
                    if tmp < best:
                        best = tmp

                    if (lld_i == i_start) and (lld_j == j_start):
                        rep_cost = 0 if li == lj else cr(li, lj)
                        tmp = get(i - 1, j - 1) + rep_cost
                        if tmp < best:
                            best = tmp
                    else:
                        tmp = get(lld_i - i_start, lld_j - j_start) + subtree_dist[i_idx][j_idx]
                        if tmp < best:
                            best = tmp

                    set_(i, j, best)

            res = get(m, n)
            memo[key] = res
            return res

        for i in keyroots1:
            is_ = L1[i]
            for j in keyroots2:
                js_ = L2[j]
                subtree_dist[i][j] = forest_dist(is_, js_, i, j)

        return subtree_dist[n1 - 1][n2 - 1]

    def count_nodes(self, ast) -> int:
        if not ast:
            return 0
        cnt = 0
        stack = [ast]
        while stack:
            n = stack.pop()
            cnt += 1
            ch = n.get("children") or []
            if ch:
                stack.extend(ch)
        return cnt

    def normalized_tree_edit_distance(self, ast_ori, ast_std):
        ted = self.tree_edit_distance(ast_ori, ast_std)
        n1 = self.count_nodes(ast_ori)
        n2 = self.count_nodes(ast_std)
        total_nodes = n1 + n2
        if total_nodes == 0:
            return 0, 0.0, 1.0
        normalized = ted / total_nodes
        similarity = 1.0 - normalized
        return ted, normalized, similarity

    def fast_similarity(self, ast1, ast2, max_nodes=500):
        n1 = self.count_nodes(ast1)
        n2 = self.count_nodes(ast2)
        total = n1 + n2
        if total == 0:
            return 0, 0.0, 1.0
        if total > max_nodes:
            def bag_labels(ast):
                bag = Counter()
                stack = [ast]
                while stack:
                    n = stack.pop()
                    bag[n.get("type", "")] += 1
                    ch = n.get("children") or []
                    if ch:
                        stack.extend(ch)
                return bag

            b1, b2 = bag_labels(ast1), bag_labels(ast2)
            inter = sum((b1 & b2).values())
            union = sum((b1 | b2).values()) or 1
            sim = inter / union
            norm = 1.0 - sim
            ted_approx = int(norm * total)
            return ted_approx, norm, sim
        return self.normalized_tree_edit_distance(ast1, ast2)

    def collect_original_types(self, node, out_list):
        if not node or not isinstance(node, dict):
            return
        tipe = node.get("type")
        if tipe:
            out_list.append(tipe)
        for ch in node.get("children", []):
            self.collect_original_types(ch, out_list)

    def collect_standart_types(self, node, out_list):
        if not node or not isinstance(node, dict):
            return
        tipe = node.get("type")
        if tipe:
            out_list.append(tipe)
        for ch in node.get("children", []):
            self.collect_standart_types(ch, out_list)

    def collect_removed_types(self, ori, uni, out_list):
        if not ori:
            return

        ori_type = ori.get("type")
        uni_type = uni.get("type") if uni else None

        if ori_type and (ori_type != uni_type):
            out_list.append(ori_type)

        ori_children = ori.get("children", [])
        uni_children = uni.get("children", []) if uni else []

        for i, ch in enumerate(ori_children):
            uni_child = uni_children[i] if i < len(uni_children) else None
            self.collect_removed_types(ch, uni_child, out_list)

    def collect_single_child_types(self, node, out_list):
        if not node or not isinstance(node, dict):
            return
        children = node.get("children", [])
        if len(children) == 1:
            tipe = node.get("type")
            if tipe:
                out_list.append(tipe)
        for ch in children:
            self.collect_single_child_types(ch, out_list)

    def calculate_pec(self, ast_ori, ast_u):
        result = programming_element_completeness(ast_ori, ast_u)
        result["language"] = self.lang
        return result

def collect_node_types_in_ast(ast):
    node_types = set()

    if not isinstance(ast, dict):
        return node_types

    stack = [ast]

    while stack:
        node = stack.pop()

        if not isinstance(node, dict):
            continue

        node_type = str(node.get("type", "") or "").strip()
        if node_type:
            node_types.add(node_type)

        children = node.get("children", []) or []
        stack.extend(children)

    return node_types

def _pec_cache_key(language: Optional[str] = None) -> str:
    return str(language or "__default__").strip().lower()


def _get_pec_categorized_nodes(language: Optional[str] = None) -> Set[str]:
    key = _pec_cache_key(language)
    if key in _PEC_CATEGORIZED_NODES_CACHE:
        return _PEC_CATEGORIZED_NODES_CACHE[key]

    categorized_nodes = set()
    for nodes in _get_pec_node_groups(language).values():
        categorized_nodes.update(nodes)

    _PEC_CATEGORIZED_NODES_CACHE[key] = categorized_nodes
    return _PEC_CATEGORIZED_NODES_CACHE[key]


def uncategorized_canonical_nodes_from_types(node_types: Set[str], language: Optional[str] = None):
    canonical_nodes = set(CANONICAL_NODE_TYPES)
    uncategorized = node_types & canonical_nodes - _get_pec_categorized_nodes(language)
    return sorted(uncategorized)


def uncategorized_canonical_nodes(ast, language: Optional[str] = None):
    return uncategorized_canonical_nodes_from_types(collect_node_types_in_ast(ast), language)


def node_label(node: Any) -> str:
    if isinstance(node, dict):
        return str(node.get("type", ""))
    if hasattr(node, "type"):
        return str(getattr(node, "type"))
    if hasattr(node, "label"):
        return str(getattr(node, "label"))
    return str(node)


def node_children(node: Any) -> List[Any]:
    if isinstance(node, dict):
        ch = node.get("children", [])
        return list(ch) if ch else []
    if hasattr(node, "children"):
        ch = getattr(node, "children")
        return list(ch) if ch else []
    return []


@dataclass
class IndexedTree:
    size: int
    labels: List[str]
    lmd: List[int]
    keyroots: List[int]


def index_tree_postorder(root: Any) -> IndexedTree:
    nodes: List[Any] = []
    labels: List[str] = [""]
    lmd: List[int] = [0]

    def postorder(node: Any) -> None:
        for c in node_children(node):
            postorder(c)
        nodes.append(node)

    postorder(root)
    n = len(nodes)

    labels = [""] * (n + 1)
    lmd = [0] * (n + 1)

    idx_of: Dict[int, int] = {}
    for i, node in enumerate(nodes, start=1):
        idx_of[id(node)] = i
        labels[i] = node_label(node)

    def compute_lmd(node: Any) -> int:
        kids = node_children(node)
        if not kids:
            return idx_of[id(node)]
        return compute_lmd(kids[0])

    for i in range(1, n + 1):
        lmd[i] = compute_lmd(nodes[i - 1])

    last_for_lmd: Dict[int, int] = {}
    for i in range(1, n + 1):
        last_for_lmd[lmd[i]] = i
    keyroots = sorted(last_for_lmd.values())

    return IndexedTree(size=n, labels=labels, lmd=lmd, keyroots=keyroots)


def tree_edit_distance(rootA: Any, rootB: Any) -> int:
    A = index_tree_postorder(rootA)
    B = index_tree_postorder(rootB)

    n, m = A.size, B.size
    treedist = [[0] * (m + 1) for _ in range(n + 1)]

    def compute_forest_dist(i: int, j: int) -> None:
        iL, jL = A.lmd[i], B.lmd[j]
        rows = i - iL + 2
        cols = j - jL + 2

        fd = [[0] * cols for _ in range(rows)]

        for di in range(1, rows):
            fd[di][0] = fd[di - 1][0] + 1
        for dj in range(1, cols):
            fd[0][dj] = fd[0][dj - 1] + 1

        for di in range(1, rows):
            aIdx = iL + di - 1
            for dj in range(1, cols):
                bIdx = jL + dj - 1

                delCost = fd[di - 1][dj] + 1
                insCost = fd[di][dj - 1] + 1

                if A.lmd[aIdx] == iL and B.lmd[bIdx] == jL:
                    relabel = 0 if A.labels[aIdx] == B.labels[bIdx] else 1
                    repCost = fd[di - 1][dj - 1] + relabel
                    fd[di][dj] = min(delCost, insCost, repCost)
                    treedist[aIdx][bIdx] = fd[di][dj]
                else:
                    aSub = A.lmd[aIdx] - iL
                    bSub = B.lmd[bIdx] - jL
                    repCost = fd[aSub][bSub] + treedist[aIdx][bIdx]
                    fd[di][dj] = min(delCost, insCost, repCost)

    for i in A.keyroots:
        for j in B.keyroots:
            compute_forest_dist(i, j)

    return treedist[n][m]


def ted_similarity(rootA, rootB):
    A = index_tree_postorder(rootA)
    B = index_tree_postorder(rootB)
    dist = tree_edit_distance(rootA, rootB)

    denom = (A.size + B.size) or 1
    sim = 1.0 - dist / denom
    sim = max(0.0, min(1.0, sim))

    return {"distance": float(dist), "similarity": float(sim)}


def extract_root_to_leaf_paths(root: Any, sep: str = ">") -> List[str]:
    paths: List[str] = []

    def dfs(node: Any, acc: str) -> None:
        t = node_label(node)
        nxt = f"{acc}{sep}{t}" if acc else t
        kids = node_children(node)
        if not kids:
            paths.append(nxt)
        else:
            for k in kids:
                dfs(k, nxt)

    dfs(root, "")
    return paths


def path_jaccard_similarity(rootA: Any, rootB: Any) -> Dict[str, float]:
    setA: Set[str] = set(extract_root_to_leaf_paths(rootA))
    setB: Set[str] = set(extract_root_to_leaf_paths(rootB))

    inter = len(setA & setB)
    union = len(setA) + len(setB) - inter
    sim = 1.0 if union == 0 else inter / union

    return {
        "similarity": float(sim),
        "pathsA": float(len(setA)),
        "pathsB": float(len(setB)),
        "intersection": float(inter),
        "union": float(union),
    }


def preprocess(
    text: Any,
    lowercase: bool = True,
    remove_punctuation: bool = True,
    collapse_whitespace: bool = True,
    stopwords: Optional[Set[str]] = None,
    ngram: int = 1,
) -> List[str]:
    s = "" if text is None else str(text)
    if lowercase:
        s = s.lower()

    if remove_punctuation:
        s = re.sub(r"[^a-z0-9_\s]", " ", s)

    if collapse_whitespace:
        s = re.sub(r"\s+", " ", s).strip()

    tokens = s.split(" ") if s else []
    tokens = [t for t in tokens if t]

    if isinstance(stopwords, set):
        tokens = [t for t in tokens if t not in stopwords]

    if ngram > 1:
        grams = []
        for i in range(0, len(tokens) - ngram + 1):
            grams.append("_".join(tokens[i:i + ngram]))
        tokens = grams

    return tokens


def term_frequency(tokens: Sequence[str]) -> Counter:
    return Counter(tokens)


def cosine_similarity_from_tf(tfA: Counter, tfB: Counter) -> float:
    normA = sum(v * v for v in tfA.values())
    normB = sum(v * v for v in tfB.values())

    if normA == 0 and normB == 0:
        return 1.0
    if normA == 0 or normB == 0:
        return 0.0

    small, big = (tfA, tfB) if len(tfA) <= len(tfB) else (tfB, tfA)
    dot = 0.0
    for k, v in small.items():
        if k in big:
            dot += v * big[k]

    return dot / (math.sqrt(normA) * math.sqrt(normB))


def cosine_similarity_strings(strA: Any, strB: Any, **options) -> Dict[str, Any]:
    tokensA = preprocess(strA, **options)
    tokensB = preprocess(strB, **options)

    tfA = term_frequency(tokensA)
    tfB = term_frequency(tokensB)

    return {
        "similarity": float(cosine_similarity_from_tf(tfA, tfB)),
        "tokensA": tokensA,
        "tokensB": tokensB,
        "uniqueA": float(len(tfA)),
        "uniqueB": float(len(tfB)),
    }


def count_ast_nodes(ast: dict) -> int:
    if not isinstance(ast, dict):
        return 0

    count = 1
    children = ast.get("children", [])
    if isinstance(children, list):
        for child in children:
            count += count_ast_nodes(child)

    return count


def ast_compression_ratio(ast_original: dict, ast_unified: dict) -> dict:
    n_original = count_ast_nodes(ast_original)
    n_unified = count_ast_nodes(ast_unified)

    if n_original == 0:
        raise ValueError("AST original kosong")

    ratio = n_unified / n_original
    gain = 1.0 - ratio

    return {
        "nodes_original": n_original,
        "nodes_unified": n_unified,
        "compression_ratio": round(ratio, 4),
        "compression_gain": round(gain, 4),
    }

def count_text_attributes(ast: dict) -> int:
    if not isinstance(ast, dict):
        return 0

    total = 0
    stack = [ast]

    while stack:
        node = stack.pop()

        text = str(node.get("text", "") or "").strip()
        if text:
            # hitung token sederhana berbasis spasi
            tokens = [t for t in re.split(r"\s+", text) if t]
            total += len(tokens)

        children = node.get("children", [])
        if children:
            stack.extend(children)

    return total


def attribute_loss(ast_original: dict, ast_unified: dict, eps: float = 1e-9) -> dict:
    a_original = count_text_attributes(ast_original)
    a_unified = count_text_attributes(ast_unified)

    loss = 1.0 - (a_unified / (a_original + eps)) if a_original > 0 else 0.0

    return {
        "attributes_original": a_original,
        "attributes_unified": a_unified,
        "attribute_loss": round(loss, 4),
    }

# ---------------------------------------------------------------------------
# Programming Element Completeness (PEC)
# ---------------------------------------------------------------------------

_FALLBACK_PEC_CATEGORIES = ["VAR", "TYPE", "EXPR", "ASSIGN", "CTRL", "SUBP", "OOP"]

_FALLBACK_PEC_NODE_GROUPS = {
    "VAR": {
        "variable", "identifier", "name", "variable_name", "qualified_name",
        "field_identifier", "property_identifier", "package_identifier",
        "scoped_identifier", "statement_identifier", "instance_variable",
        "class_variable", "global_variable", "dynamic_variable_name", "label_name",
    },
    "TYPE": {
        "type", "type_identifier", "primitive_type", "predefined_type",
        "void_type", "integral_type", "array_type", "generic_type",
        "named_type", "qualified_type", "scoped_type_identifier", "int",
        "integer", "float", "double", "long", "decimal", "bool", "boolean",
        "char", "byte", "short", "void", "string", "number", "null",
        "array", "list", "set", "dictionary", "object",
    },
    "EXPR": {
        "expression", "expression_statement", "binary_expression",
        "unary_expression", "assignment_expression", "call", "call_expression",
        "function_call_expression", "method_invocation", "invocation_expression",
        "member_expression", "member_access_expression", "selector_expression",
        "field_expression", "parenthesized_expression", "conditional_expression",
        "ternary_expression", "await_expression", "yield_expression", "argument",
        "argument_list", "arguments", "literal", "number", "string", "boolean",
        "array", "list", "set", "dictionary", "object", "return", "return_statement",
    },
    "ASSIGN": {
        "assignment", "assignment_statement", "assignment_expression",
        "augmented_assignment", "augmented_assignment_expression",
        "compound_assignment_expr", "operator_assignment", "declaration",
        "variable_declaration", "variable_declarator", "local_variable_declaration",
        "lexical_declaration", "let_declaration", "var_declaration",
        "short_var_declaration", "const_declaration", "const_spec", "init_declarator",
        "=",
    },
    "CTRL": {
        "if", "if_statement", "if_expression", "else", "else_clause",
        "else_if_clause", "elif", "elseif", "elsif", "switch", "switch_statement",
        "switch_expression", "case", "case_statement", "default", "default_statement",
        "for", "for_statement", "for_in_statement", "foreach_statement",
        "enhanced_for_statement", "while", "while_statement", "do_statement",
        "break", "break_statement", "continue", "continue_statement", "try",
        "try_statement", "catch", "catch_clause", "except_clause", "finally",
        "finally_clause", "with", "with_statement", "throw", "throw_statement",
        "raise", "raise_statement", "return", "return_statement", "exit",
        "exit_statement", "match", "match_expression",
    },
    "SUBP": {
        "function", "function_declaration", "function_definition",
        "function_expression", "method", "method_declaration",
        "constructor_declaration", "lambda", "lambda_expression",
        "anonymous_function", "arrow_function", "generator_function",
        "generator_function_declaration", "parameter", "parameters",
        "parameter_list", "formal_parameter", "formal_parameters",
        "method_parameters",
    },
    "OOP": {
        "class", "class_declaration", "class_definition",
        "interface_declaration", "struct_declaration", "struct_item",
        "enum_declaration", "enum_item", "trait_item", "impl_item",
        "implementation_item", "anonymous_class", "extends", "implements",
    },
}


def _get_pec_categories() -> List[str]:
    global _PEC_CATEGORIES_CACHE
    if _PEC_CATEGORIES_CACHE is None:
        _PEC_CATEGORIES_CACHE = list(globals().get("PEC_CATEGORIES", _FALLBACK_PEC_CATEGORIES))
    return _PEC_CATEGORIES_CACHE


def _get_pec_valid_categories() -> Set[str]:
    global _PEC_VALID_CATEGORIES_CACHE
    if _PEC_VALID_CATEGORIES_CACHE is None:
        _PEC_VALID_CATEGORIES_CACHE = set(_get_pec_categories())
    return _PEC_VALID_CATEGORIES_CACHE


def _get_pec_node_groups(language: Optional[str] = None) -> Dict[str, Set[str]]:
    key = _pec_cache_key(language)
    if key in _PEC_NODE_GROUPS_CACHE:
        return _PEC_NODE_GROUPS_CACHE[key]

    source = globals().get("PEC_NODE_GROUPS", _FALLBACK_PEC_NODE_GROUPS)
    by_language = globals().get("PEC_NODE_GROUPS_BY_LANGUAGE", {})
    if language and str(language).strip().lower() in by_language:
        source = by_language[str(language).strip().lower()]

    groups: Dict[str, Set[str]] = {}
    for category, nodes in source.items():
        groups[str(category)] = {str(node).strip().lower() for node in nodes if str(node).strip()}

    _PEC_NODE_GROUPS_CACHE[key] = groups
    return _PEC_NODE_GROUPS_CACHE[key]


def _get_pec_node_to_categories(language: Optional[str] = None) -> Dict[str, Set[str]]:
    key = _pec_cache_key(language)
    if key in _PEC_NODE_TO_CATEGORIES_CACHE:
        return _PEC_NODE_TO_CATEGORIES_CACHE[key]

    if key == "__default__" and "PEC_NODE_TO_CATEGORIES" in globals():
        _PEC_NODE_TO_CATEGORIES_CACHE[key] = {
            str(node).strip().lower(): {str(cat) for cat in cats}
            for node, cats in globals()["PEC_NODE_TO_CATEGORIES"].items()
        }
        return _PEC_NODE_TO_CATEGORIES_CACHE[key]

    reverse: Dict[str, Set[str]] = {}
    for category, nodes in _get_pec_node_groups(language).items():
        for node in nodes:
            reverse.setdefault(node, set()).add(category)

    _PEC_NODE_TO_CATEGORIES_CACHE[key] = reverse
    return _PEC_NODE_TO_CATEGORIES_CACHE[key]


def pec_categories_for_node(
    node_type: Any,
    text: Any = "",
    reverse: Optional[Dict[str, Set[str]]] = None,
    language: Optional[str] = None,
) -> Set[str]:
    """Return PEC categories represented by one AST/UAST node."""
    raw = str(node_type or "").replace("$", "").strip().lower()
    raw = OPERATORS_NORMALIZE.get(raw, raw)

    categories: Set[str] = set()
    if reverse is None:
        reverse = _get_pec_node_to_categories(language)

    if raw in reverse:
        categories.update(reverse[raw])

    canonical = ALIAS_TO_CANONICAL.get(raw, raw)
    if canonical == "program":
        canonical = "module"
    if canonical in reverse:
        categories.update(reverse[canonical])

    txt = str(text or "").replace("$", "").strip().lower()
    if txt in PEC_TYPE_TEXTS and (canonical == "type" or raw in PEC_TYPE_TEXTS or raw.endswith("_type")):
        categories.add("TYPE")

    return categories


def pec_categories_and_node_types_in_ast(ast: Any, language: Optional[str] = None) -> Tuple[Set[str], Set[str]]:
    """Collect PEC categories and node types with one AST traversal."""
    categories: Set[str] = set()
    node_types: Set[str] = set()
    if not isinstance(ast, dict):
        return categories, node_types

    stack = [ast]
    reverse = _get_pec_node_to_categories(language)
    while stack:
        node = stack.pop()
        if not isinstance(node, dict):
            continue

        node_type = str(node.get("type", "") or "").strip()
        if node_type:
            node_types.add(node_type)

        categories.update(
            pec_categories_for_node(
                node_type,
                node.get("text", ""),
                reverse,
                language,
            )
        )

        stack.extend(node.get("children", []) or [])

    return categories & _get_pec_valid_categories(), node_types


def pec_categories_in_ast(ast: Any, language: Optional[str] = None) -> Set[str]:
    """Collect PEC categories found in an AST dictionary."""
    categories, _ = pec_categories_and_node_types_in_ast(ast, language)
    return categories


def programming_element_completeness(ast_original, ast_unified, language: Optional[str] = None):
    original_categories, original_node_types_set = pec_categories_and_node_types_in_ast(ast_original, language)
    unified_categories, unified_node_types_set = pec_categories_and_node_types_in_ast(ast_unified, language)

    # Pakai getter agar fallback OOP ikut aktif kalau constant belum lengkap
    all_categories = set(_get_pec_valid_categories())
    all_categories.add("OOP")  # paksa OOP tetap dikenali sebagai kategori valid

    code_categories = all_categories - {"OOP"}
    oop_categories = {"OOP"}

    # =========================
    # PEC ALL: termasuk OOP
    # =========================
    original_all_categories = original_categories & all_categories
    unified_all_categories = unified_categories & all_categories

    preserved_all_categories = original_all_categories & unified_all_categories
    loss_all_categories = original_all_categories - unified_all_categories
    extra_all_categories = unified_all_categories - original_all_categories

    available_all_count = len(original_all_categories)
    preserved_all_count = len(preserved_all_categories)
    loss_all_count = len(loss_all_categories)

    if available_all_count == 0:
        pec_all = 1.0
        pec_all_loss = 0.0
    else:
        pec_all = preserved_all_count / available_all_count
        pec_all_loss = loss_all_count / available_all_count

    # =========================
    # PEC CODE: tanpa OOP
    # Skor ini tidak menghitung OOP,
    # tetapi informasi OOP tetap disimpan di field oop_*
    # =========================
    original_code_categories = original_categories & code_categories
    unified_code_categories = unified_categories & code_categories

    preserved_code_categories = original_code_categories & unified_code_categories
    loss_code_categories = original_code_categories - unified_code_categories
    extra_code_categories = unified_code_categories - original_code_categories

    available_code_count = len(original_code_categories)
    preserved_code_count = len(preserved_code_categories)
    loss_code_count = len(loss_code_categories)

    if available_code_count == 0:
        pec_code = 1.0
        pec_code_loss = 0.0
    else:
        pec_code = preserved_code_count / available_code_count
        pec_code_loss = loss_code_count / available_code_count

    # =========================
    # OOP INFO: jangan hilang
    # =========================
    original_oop_categories = original_categories & oop_categories
    unified_oop_categories = unified_categories & oop_categories

    preserved_oop_categories = original_oop_categories & unified_oop_categories
    loss_oop_categories = original_oop_categories - unified_oop_categories
    extra_oop_categories = unified_oop_categories - original_oop_categories

    available_oop_count = len(original_oop_categories)
    preserved_oop_count = len(preserved_oop_categories)
    loss_oop_count = len(loss_oop_categories)

    if available_oop_count == 0:
        pec_oop = 1.0
        pec_oop_loss = 0.0
    else:
        pec_oop = preserved_oop_count / available_oop_count
        pec_oop_loss = loss_oop_count / available_oop_count

    original_node_types = sorted(original_node_types_set)
    unified_node_types = sorted(unified_node_types_set)

    return {
        # backward compatibility untuk kolom database lama
        # pec_score = pec_result["pec"]      -> tanpa OOP
        # pec_score_all = pec_result["pec_all"] -> termasuk OOP
        "pec": round(pec_code, 4),
        "pec_loss": round(pec_code_loss, 4),
    
        # key eksplisit untuk kolom database baru
        "pec_score": round(pec_code, 4),
        "pec_score_all": round(pec_all, 4),
    
        # nilai utama
        "pec_all": round(pec_all, 4),
        "pec_all_loss": round(pec_all_loss, 4),
    
        "pec_code": round(pec_code, 4),
        "pec_code_loss": round(pec_code_loss, 4),
    
        # nilai khusus OOP
        "pec_oop": round(pec_oop, 4),
        "pec_oop_loss": round(pec_oop_loss, 4),
    
        # count all
        "available_all_count": available_all_count,
        "preserved_all_count": preserved_all_count,
        "loss_all_count": loss_all_count,
    
        # count code tanpa OOP
        "available_code_count": available_code_count,
        "preserved_code_count": preserved_code_count,
        "loss_code_count": loss_code_count,
    
        # count OOP
        "available_oop_count": available_oop_count,
        "preserved_oop_count": preserved_oop_count,
        "loss_oop_count": loss_oop_count,
    
        # backward compatibility
        # ini sebaiknya ikut pec tanpa OOP agar konsisten dengan pec
        "available_count": available_code_count,
        "preserved_count": preserved_code_count,
        "loss_count": loss_code_count,
    
        # kategori ALL: termasuk OOP
        "original_all_categories": sorted(original_all_categories),
        "unified_all_categories": sorted(unified_all_categories),
        "preserved_all_categories": sorted(preserved_all_categories),
        "loss_all_categories": sorted(loss_all_categories),
        "missing_all_categories": sorted(loss_all_categories),
        "extra_all_categories": sorted(extra_all_categories),
    
        # kategori CODE: tanpa OOP
        "original_code_categories": sorted(original_code_categories),
        "unified_code_categories": sorted(unified_code_categories),
        "preserved_code_categories": sorted(preserved_code_categories),
        "loss_code_categories": sorted(loss_code_categories),
        "missing_code_categories": sorted(loss_code_categories),
        "extra_code_categories": sorted(extra_code_categories),
    
        # kategori OOP
        "original_oop_categories": sorted(original_oop_categories),
        "unified_oop_categories": sorted(unified_oop_categories),
        "preserved_oop_categories": sorted(preserved_oop_categories),
        "loss_oop_categories": sorted(loss_oop_categories),
        "missing_oop_categories": sorted(loss_oop_categories),
        "extra_oop_categories": sorted(extra_oop_categories),
    
        # backward compatibility kategori
        # tetap ALL agar info OOP tidak hilang dari pec_data
        "original_categories": sorted(original_all_categories),
        "unified_categories": sorted(unified_all_categories),
        "preserved_categories": sorted(preserved_all_categories),
        "loss_categories": sorted(loss_all_categories),
        "missing_categories": sorted(loss_all_categories),
        "extra_categories": sorted(extra_all_categories),
    
        # tambahan analisis node type
        "original_node_types": original_node_types,
        "unified_node_types": unified_node_types,
    
        "original_uncategorized_canonical_nodes": uncategorized_canonical_nodes_from_types(original_node_types_set, language),
        "unified_uncategorized_canonical_nodes": uncategorized_canonical_nodes_from_types(unified_node_types_set, language),
    }


def calculate_pec(ast_original: Any, ast_unified: Any, language: Optional[str] = None) -> Dict[str, Any]:
    """Alias for programming_element_completeness()."""
    return programming_element_completeness(ast_original, ast_unified, language)



    def pec_categories_in_ast(self, ast_dict: Dict[str, Any]) -> Set[str]:
        return pec_categories_in_ast(ast_dict, self.lang)

    def calculate_pec(self, ast_original: Dict[str, Any], ast_unified: Dict[str, Any]) -> Dict[str, Any]:
        result = programming_element_completeness(ast_original, ast_unified, self.lang)
        result["language"] = self.lang
        return result

    def calculate_pec_from_code(self, code: Any) -> Dict[str, Any]:
        tree = self.parse_code_to_ast(code)
        if tree is None:
            raise ValueError("Parsing failed")
        source = code if isinstance(code, bytes) else str(code).encode("utf-8")
        ast_original = self.node_to_dict(tree.root_node, source)
        ast_unified = self.node_to_dict_unified(tree.root_node, source)
        return self.calculate_pec(ast_original, ast_unified)
