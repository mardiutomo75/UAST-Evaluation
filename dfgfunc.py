from collections import defaultdict
from typing import Dict, List, Set
import re


class DFGExtractor:
    def __init__(self):
        self.dfg = defaultdict(set)
        self.defined_vars = set()
        self.clean_var_cache = {}

    def reset(self):
        self.dfg.clear()
        self.defined_vars.clear()
        self.clean_var_cache.clear()

    def clean_var_name(self, name):
        """Membersihkan nama variabel lintas bahasa secara cepat."""
        if name in self.clean_var_cache:
            return self.clean_var_cache[name]
        clean = name.strip().split()[0]
        if clean.lower() in {"int", "float", "string", "bool", "var"}:
            self.clean_var_cache[name] = None
            return None
        if re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", clean):
            self.clean_var_cache[name] = clean
            return clean
        self.clean_var_cache[name] = None
        return None

    def extract_dfg(self, ast_root):
        """Langsung traversal ke node penting tanpa peduli block atau parent-type."""
        self.reset()
        queue = [ast_root]
        last_vars = set()

        while queue:
            node = queue.pop()
            if node is None:
                continue
            node_type = node.get("type", "")
            text = node.get("text", "").strip()
            children = node.get("children", [])

            # Jika node berisi ekspresi, kumpulkan semua identifier di dalamnya
            # if node_type in ("expression", "binary_expression", "expression_list"):
            #     vars_in_expr = self.collect_identifiers(node)
            #     if vars_in_expr:
            #         for src in self.defined_vars:
            #             self.dfg[src].update(vars_in_expr)
            #         # Simpan variabel hasil ekspresi terakhir
            #         last_vars = vars_in_expr

            # Jika node mendefinisikan variabel (parameter, variable, identifier)
            if node_type in ("parameter", "variable", "identifier","parameters"):
                var_name = self.clean_var_name(text)
                if var_name:
                    self.defined_vars.add(var_name)

            # Jika node “return”, anggap ekspresi di dalamnya pakai semua variabel terakhir
            elif node_type == "return":
                all_vars = self.collect_identifiers(node)
                for src in self.defined_vars:
                    for tgt in all_vars:
                        self.dfg[src].add(tgt)

            queue.extend(children)

        return self.dfg

    def collect_identifiers(self, node):
        """Ambil semua identifier unik di subtree ini."""
        vars_found = set()
        stack = [node]
        while stack:
            cur = stack.pop()
            if cur.get("type") in ("identifier", "variable"):
                var = self.clean_var_name(cur.get("text", "").strip())
                if var:
                    vars_found.add(var)
            stack.extend(cur.get("children", []))
        return vars_found



class DFGExtractorUnified:
    def __init__(self):
        self.reset()
        self.clean_var_cache = {}

    def reset(self):
        self.dfg = defaultdict(set)
        self.defined_vars = set()

    def clean_var_name(self, name):
        if name in self.clean_var_cache:
            return self.clean_var_cache[name]
        clean_name = name.strip().split()[0] if ' ' in name else name.strip()
        if clean_name in ['int', 'string', 'float']:
            self.clean_var_cache[name] = None
            return None
        if re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', clean_name):
            self.clean_var_cache[name] = clean_name
            return clean_name
        self.clean_var_cache[name] = None
        return None

    def extract_dfg(self, node):
        self.reset()
        stack = [(node, set())]  # (node, live_vars)
        while stack:
            curr_node, live_vars = stack.pop()
            if curr_node is None:
                continue
            node_type = curr_node.get('type', '')
            text = curr_node.get('text', '').strip()
            children = curr_node.get('children', [])

            if node_type in ('parameter', 'variable'):
                var = self.clean_var_name(text)
                if var:
                    self.defined_vars.add(var)
                    live_vars = live_vars.union({var})

            if node_type == 'expression' or node_type == 'return':
                vars_in_expr = self.collect_identifiers(curr_node)
                clean_live_vars = {v for v in live_vars if self.clean_var_name(v)}
                clean_vars_in_expr = {v for v in vars_in_expr if self.clean_var_name(v)}
                for src in clean_live_vars:
                    for tgt in clean_vars_in_expr:
                        self.dfg[src].add(tgt)

            for child in children:
                stack.append((child, live_vars.union(self.defined_vars)))

        return self.dfg

    def collect_identifiers(self, node):
        ids = set()
        stack = [node]
        while stack:
            n = stack.pop()
            if n.get('type') == 'variable':
                v = self.clean_var_name(n.get('text', ''))
                if v:
                    ids.add(v)
            children = n.get('children', [])
            stack.extend(children)
        return ids



def evaluate_dfg_metrics(truth_dfg, pred_dfg):
    """
    Menghitung Precision, Recall, dan F1-score dari DFG prediksi dibanding DFG kebenaran.
    Both input: dict[str, set[str]] (node -> dependents)
    """
    truth_edges = set()
    pred_edges = set()

    # Buat himpunan edge berbentuk tuple (source, target)
    for src, targets in truth_dfg.items():
        for tgt in targets:
            truth_edges.add((src, tgt))

    for src, targets in pred_dfg.items():
        for tgt in targets:
            pred_edges.add((src, tgt))

    true_positives = truth_edges.intersection(pred_edges)
    false_positives = pred_edges - truth_edges
    false_negatives = truth_edges - pred_edges

    precision = len(true_positives) / (len(true_positives) + len(false_positives)) if (len(true_positives) + len(false_positives)) > 0 else 0.0
    recall = len(true_positives) / (len(true_positives) + len(false_negatives)) if (len(true_positives) + len(false_negatives)) > 0 else 0.0
    f1_score = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

    return {
        'precision': precision,
        'recall': recall,
        'f1_score': f1_score,
        'true_positives': len(true_positives),
        'false_positives': len(false_positives),
        'false_negatives': len(false_negatives)
    }



