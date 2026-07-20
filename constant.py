# normalized constant.py
# NOTE: pure constants only (no executable demo code)

from __future__ import annotations

LANGUAGES = ["go", "python", "ruby", "php", "java", "javascript", "cs", "cpp", "rust"]
languages = LANGUAGES

SPLITS = ["test", "valid", "train"]
splits = SPLITS


# =========================================================
# Reserved words
# =========================================================

RESERVED_COMMON = [
    "break",
    "continue",
    "else",
    "for",
    "if",
    "return",
    "switch",
    "try",
    "catch",
    "finally",
    "while",
]

RESERVED_BY_LANG = {
    "go": [
        "break", "case", "chan", "const", "continue", "default", "defer", "loop",
        "else", "fallthrough", "for", "func", "go", "goto", "if", "import",
        "interface", "map", "package", "range", "return", "select", "struct",
        "switch", "type", "var",
    ],
    "python": [
        "and", "as", "assert", "async", "await", "break", "case", "class",
        "continue", "def", "del", "elif", "else", "except", "false", "finally",
        "for", "from", "global", "if", "import", "in", "is", "lambda", "match",
        "none", "nonlocal", "not", "or", "pass", "raise", "return", "true",
        "try", "while", "with", "yield",
    ],
    "ruby": [
        "alias", "and", "begin", "break", "case", "class", "def", "defined?",
        "do", "else", "elsif", "end", "ensure", "false", "for", "if", "in",
        "module", "next", "nil", "not", "or", "redo", "rescue", "retry",
        "return", "self", "super", "then", "true", "undef", "unless", "until",
        "when", "while", "yield",
    ],
    "php": [
        "abstract", "and", "array", "as", "break", "callable", "case", "catch",
        "class", "clone", "const", "continue", "declare", "default", "die", "do",
        "echo", "elseif", "else", "empty", "enddeclare", "endfor", "endforeach",
        "endif", "endswitch", "endwhile", "eval", "exit", "extends", "final",
        "finally", "for", "foreach", "function", "global", "goto", "if",
        "implements", "include", "include_once", "instanceof", "insteadof",
        "interface", "isset", "list", "match", "namespace", "new", "or", "print",
        "private", "protected", "public", "readonly", "require", "require_once",
        "return", "static", "switch", "throw", "trait", "try", "unset", "use",
        "var", "while", "xor", "yield",
    ],
    "java": [
        "abstract", "assert", "boolean", "break", "byte", "case", "catch",
        "char", "class", "const", "continue", "default", "do", "double", "else",
        "enum", "extends", "final", "finally", "float", "for", "goto", "if",
        "implements", "import", "instanceof", "int", "interface", "long",
        "native", "new", "package", "private", "protected", "public", "return",
        "short", "static", "strictfp", "super", "switch", "synchronized", "this",
        "throw", "throws", "transient", "try", "void", "volatile", "while",
    ],
    "javascript": [
        "await", "break", "case", "catch", "class", "const", "continue",
        "debugger", "default", "delete", "do", "else", "enum", "export",
        "extends", "false", "finally", "for", "function", "if", "implements",
        "import", "in", "instanceof", "interface", "let", "new", "null",
        "package", "private", "protected", "public", "return", "static", "super",
        "switch", "this", "throw", "true", "try", "typeof", "var", "void",
        "while", "with", "yield",
    ],
    "cs": [
        "abstract", "as", "base", "bool", "break", "byte", "case", "catch",
        "char", "checked", "class", "const", "continue", "decimal", "default",
        "delegate", "do", "double", "else", "enum", "event", "explicit", "extern",
        "false", "finally", "fixed", "float", "for", "foreach", "goto", "if",
        "implicit", "in", "int", "interface", "internal", "is", "lock", "long",
        "namespace", "new", "null", "object", "operator", "out", "override",
        "params", "private", "protected", "public", "readonly", "ref", "return",
        "sbyte", "sealed", "short", "sizeof", "stackalloc", "static", "string",
        "struct", "switch", "this", "throw", "true", "try", "typeof", "uint",
        "ulong", "unchecked", "unsafe", "ushort", "using", "virtual", "void",
        "volatile", "while",
    ],
    "cpp": [
        "alignas", "alignof", "and", "asm", "auto", "bool", "break", "case",
        "catch", "char", "class", "const", "constexpr", "continue", "default",
        "delete", "do", "double", "else", "enum", "explicit", "export", "extern",
        "false", "float", "for", "friend", "goto", "if", "inline", "int", "long",
        "mutable", "namespace", "new", "noexcept", "not", "nullptr", "operator",
        "or", "private", "protected", "public", "register", "return", "short",
        "signed", "sizeof", "static", "struct", "switch", "template", "this",
        "throw", "true", "try", "typedef", "typename", "union", "unsigned",
        "using", "virtual", "void", "volatile", "while",
    ],
    "rust": [
        "as", "async", "await", "break", "const", "continue", "crate", "else",
        "enum", "extern", "false", "fn", "for", "if", "impl", "in", "let",
        "loop", "match", "mod", "move", "mut", "pub", "ref", "return", "self",
        "Self", "static", "struct", "super", "trait", "true", "type", "unsafe",
        "use", "where", "while",
    ],
}


# =========================================================
# Operator normalization
# =========================================================

OPERATORS_NORMALIZE = {
    ":=": "=",
}


# =========================================================
# Canonical node types
# Small and stable for cross-language UAST / LA-UAST
# =========================================================

CANONICAL_NODE_TYPES = [
    "module",
    "function",
    "class",
    "variable",
    "identifier",
    "parameter",
    "argument",
    "assignment",
    "expression",
    "call",
    "return",
    "if",
    "else",
    "switch",
    "case",
    "default",
    "for",
    "while",
    "break",
    "continue",
    "try",
    "catch",
    "finally",
    "with",
    "throw",
    "raise",
    "exit",
    "end",
    "string",
    "literal",
    "number",
    "null",
    "boolean",
    "regex",
    "array",
    "list",
    "set",
    "dictionary",
    "object",
    "pattern",
    "type",
    "block",
    "comment",
    "error",
    "=",
]


# =========================================================
# Alias -> canonical grouping
# Canonical output should stay uniform.
# Parser-specific raw types are normalized here.
# =========================================================

ALIASES_BY_CANONICAL = {
    "program": [
        "module",
        "program",
        "source_file",
        "compilation_unit",
        "translation_unit",
    ],

    "function": [
        "anonymous_function",
        "arrow_function",
        "constructor_declaration",
        "def",
        "fn",
        "func_literal",
        "function",
        "function_declaration",
        "function_definition",
        "function_expression",
        "generator_function",
        "generator_function_declaration",
        "lambda",
        "local_function_statement",
        "method",
        "method_declaration",
    ],

    "class": [
        "anonymous_class",
        "class",
        "class_declaration",
        "class_definition",
        "interface_declaration",
    ],

    "variable": [
        "class_variable",
        "dynamic_variable_name",
        "global_variable",
        "instance_variable",
        "label_name",
        "name",
        "qualified_name",
        "variable",
        "variable_name",
    ],

    "identifier": [
        "field_identifier",
        "identifier",
        "package_identifier",
        "property_identifier",
        "scoped_identifier",
        "statement_identifier",
    ],

    "parameter": [
        "block_parameter",
        "block_parameters",
        "default_parameter",
        "formal_parameter",
        "formal_parameters",
        "lambda_parameters",
        "method_parameters",
        "optional_parameter",
        "parameter",
        "parameter_declaration",
        "parameter_list",
        "parameters",
        "simple_parameter",
        "simple_parameters",
        "splat_parameter",
        "spread_parameter",
        "typed_default_parameter",
        "typed_parameter",
        "variadic_parameter",
        "variadic_parameter_declaration",
    ],

    "argument": [
        "argument",
        "argument_list",
        "arguments",
        "block_argument",
        "keyword_argument",
        "splat_argument",
        "spread_element",
        "subscript_argument_list",
        "variadic_argument",
        "variadic_unpacking",
        "generic_name"
    ],

    "assignment": [
        "assignment",
        "assignment_expression",
        "assignment_statement",
        "augmented_assignment",
        "augmented_assignment_expression",
        "compound_assignment_expr",
        "declaration",
        "function_static_declaration",
        "init_declarator",
        "left_assignment_list",
        "let_declaration",
        "lexical_declaration",
        "local_variable_declaration",
        "operator_assignment",
        "reference_assignment_expression",
        "rest_assignment",
        "right_assignment_list",
        "short_var_declaration",
        "static_variable_declaration",
        "variable_declaration",
        "variable_declarator",
        "var_declaration",
        "var_spec",
        "const_declaration",
        "const_spec",
    ],

    "expression": [
        "assert_statement",
        "await_expression",
        "binary",
        "binary_expression",
        "binary_operator",
        "bracketed_argument_list",
        "class_constant_access_expression",
        "clone_expression",
        "comparison_operator",
        "conditional_expression",
        "element_access_expression",
        "expression_list",
        "expression_statement",
        "field_access",
        "field_expression",
        "generator_expression",
        "instanceof_expression",
        "is_pattern_expression",
        "list_comprehension",
        "local_declaration_statement",
        "member_access_expression",
        "member_expression",
        "parenthesized_expression",
        "postfix_unary_expression",
        "prefix_unary_expression",
        "print_intrinsic",
        "scoped_property_access_expression",
        "selector_expression",
        "sequence_expression",
        "shell_command_expression",
        "statement_list",
        "ternary_expression",
        "unary",
        "unary_expression",
        "unary_op_expression",
        "unary_operator",
        "update_expression",
        "yield",
        "yield_expression",
    ],

    "call": [
        "call",
        "call_expression",
        "function_call_expression",
        "invocation_expression",
        "member_call_expression",
        "method_invocation",
        "new_expression",
        "object_creation_expression",
        "scoped_call_expression",
        "subscript",
    ],

    "return": [
        "return",
        "return_statement",
    ],

    "if": [
        "else_if_clause",
        "elseif",
        "elsif",
        "if",
        "if_clause",
        "if_expression",
        "if_modifier",
        "if_statement",
    ],

    "else": [
        "else",
        "else_clause",
    ],

    "switch": [
        "expression_switch_statement",
        "match",
        "match_expression",
        "switch",
        "switch_expression",
        "switch_statement",
        "type_switch_statement",
    ],

    "case": [
        "case",
        "case_statement",
        "default_case",
        "expression_case",
        "switch_case",
    ],

    "default": [
        "default",
        "default_statement",
        "switch_default",
    ],

    "for": [
        "enhanced_for_statement",
        "for",
        "for_clause",
        "for_expression",
        "for_in_clause",
        "for_in_statement",
        "for_statement",
        "foreach",
        "foreach_statement",
    ],

    "while": [
        "do_statement",
        "while",
        "while_modifier",
        "while_statement",
    ],

    "break": [
        "break",
        "break_statement",
    ],

    "continue": [
        "continue",
        "continue_statement",
    ],

    "try": [
        "try",
        "try_statement",
        "try_with_resources_statement",
    ],

    "catch": [
        "catch",
        "catch_clause",
        "catch_formal_parameter",
        "catch_type",
        "except_clause",
    ],

    "finally": [
        "finally",
        "finally_clause",
    ],

    "with": [
        "with_clause",
        "with_item",
        "with_statement",
    ],

    "throw": [
        "throw",
        "throw_expression",
        "throw_statement",
    ],

    "raise": [
        "raise",
        "raise_statement",
    ],

    "exit": [
        "exit",
        "exit_statement",
    ],

    "end": [
        "endfor",
        "endswitch",
        "endwhile",
    ],

    "string": [
        "bare_string",
        "chained_string",
        "concatenated_string",
        "encapsed_string",
        "escape_sequence",
        "heredoc",
        "heredoc_beginning",
        "heredoc_body",
        "heredoc_content",
        "heredoc_end",
        "heredoc_start",
        "interpreted_string_literal",
        "interpreted_string_literal_content",
        "nowdoc",
        "nowdoc_body",
        "nowdoc_string",
        "raw_string_literal",
        "raw_string_literal_content",
        "string",
        "string_array",
        "string_content",
        "string_end",
        "string_fragment",
        "string_literal",
        "string_start",
        "template_string",
    ],

    "literal": [
        "attribute",
        "binary_integer_literal",
        "character_literal",
        "decimal_floating_point_literal",
        "decimal_integer_literal",
        "float_literal",
        "hex_integer_literal",
        "imaginary_literal",
        "int_literal",
        "integer",
        "integer_literal",
        "literal",
        "long",
        "number_literal",
        "octal_integer_literal",
        "rune_literal",
    ],

    "number": [
        "number",
        "int",
        "float",
        "double",
        "long",
        "decimal",
    ],

    "null": [
        "none",
        "null",
        "null_literal",
    ],

    "boolean": [
        "boolean",
        "boolean_type",
        "false",
        "true",
    ],

    "regex": [
        "regex",
        "regex_flags",
        "regex_pattern",
    ],

    "array": [
        "array",
        "array_access",
        "array_creation_expression",
        "array_element_initializer",
        "array_initializer",
        "array_pattern",
        "array_rank_specifier",
        "dimensions",
        "implicit_length_array_type",
        "subscript_expression",
    ],

    "list": [
        "list",
        "list_literal",
        "list_pattern",
        "list_splat",
        "list_splat_pattern",
        "tuple",
        "tuple_pattern",
    ],

    "set": [
        "set",
        "set_comprehension",
    ],

    "dictionary": [
        "dictionary",
        "dictionary_comprehension",
        "dictionary_splat",
        "dictionary_splat_pattern",
        "hash",
        "hash_key_symbol",
        "hash_splat_argument",
        "hash_splat_parameter",
    ],

    "object": [
        "object",
        "object_assignment_pattern",
        "object_pattern",
        "pair",
        "pair_pattern",
        "shorthand_property_identifier",
        "shorthand_property_identifier_pattern",
    ],

    "pattern": [
        "as_pattern",
        "as_pattern_target",
        "pattern",
        "pattern_list",
        "underscore_pattern",
    ],

    "type": [
        "annotated_type",
        "array_type",
        "cast_type",
        "channel_type",
        "disjunctive_normal_form_type",
        "function_type",
        "generic_type",
        "integral_type",
        "intersection_type",
        "interface_type",
        "map_type",
        "named_type",
        "optional_type",
        "pointer_type",
        "predefined_type",
        "primitive_type",
        "qualified_type",
        "scoped_type_identifier",
        "slice_type",
        "struct_type",
        "template_type",
        "type",
        "type_arguments",
        "type_bound",
        "type_case",
        "type_declaration",
        "type_elem",
        "type_identifier",
        "type_instantiation_expression",
        "type_list",
        "type_parameter",
        "type_parameters",
        "type_spec",
        "void_type",
    ],

    "block": [
        "begin",
        "block",
        "block_body",
        "body_statement",
        "colon_block",
        "compound_statement",
        "do_block",
        "statement_block",
        "switch_block",
    ],

    "comment": [
        "block_comment",
        "comment",
        "line_comment",
    ],

    "error": [
        "error",
        "error_suppression_expression",
    ],

    "=": [
        "=",
    ],
}


# =========================================================
# Fast lookup: alias -> canonical
# =========================================================

ALIAS_TO_CANONICAL = {
    alias: canonical
    for canonical, aliases in ALIASES_BY_CANONICAL.items()
    for alias in aliases
}




# =========================================================
# Programming Element Completeness (PEC)
# =========================================================
# PEC categories follow:
# P = {VAR, TYPE, EXPR, ASSIGN, CTRL, SUBP, OOP}
#
# These groups contain canonical UAST node names and raw Tree-sitter aliases.
# Therefore they can be used for both original AST and Unified AST.

PEC_CATEGORIES = ["VAR", "TYPE", "EXPR", "ASSIGN", "CTRL", "SUBP", "OOP"]


def _pec_unique(*items):
    seen = set()
    out = []
    for item in items:
        if isinstance(item, (list, tuple, set)):
            iterable = item
        else:
            iterable = [item]
        for x in iterable:
            if x is None:
                continue
            s = str(x).strip().lower()
            if s and s not in seen:
                seen.add(s)
                out.append(s)
    return out


PEC_NODE_GROUPS = {
    "VAR": _pec_unique(
        "variable", "identifier",
        ALIASES_BY_CANONICAL.get("variable", []),
        ALIASES_BY_CANONICAL.get("identifier", []),
        "field_identifier", "property_identifier", "package_identifier",
        "scoped_identifier", "statement_identifier", "name", "variable_name",
        "qualified_name", "instance_variable", "class_variable", "global_variable",
        "dynamic_variable_name", "label_name",
    ),

    "TYPE": _pec_unique(
        "type", "number", "string", "boolean", "null", "literal",
        ALIASES_BY_CANONICAL.get("type", []),
        ALIASES_BY_CANONICAL.get("number", []),
        ALIASES_BY_CANONICAL.get("string", []),
        ALIASES_BY_CANONICAL.get("boolean", []),
        ALIASES_BY_CANONICAL.get("null", []),
        "int", "integer", "float", "double", "long", "decimal",
        "bool", "char", "byte", "short", "void",
        "array", "list", "set", "dictionary", "object",
        ALIASES_BY_CANONICAL.get("array", []),
        ALIASES_BY_CANONICAL.get("list", []),
        ALIASES_BY_CANONICAL.get("set", []),
        ALIASES_BY_CANONICAL.get("dictionary", []),
        ALIASES_BY_CANONICAL.get("object", []),
    ),

    "EXPR": _pec_unique(
        "expression", "call", "argument", "return", "literal",
        "number", "string", "boolean", "null", "array", "list", "set",
        "dictionary", "object", "pattern", "regex",
        ALIASES_BY_CANONICAL.get("expression", []),
        ALIASES_BY_CANONICAL.get("call", []),
        ALIASES_BY_CANONICAL.get("argument", []),
        ALIASES_BY_CANONICAL.get("return", []),
        ALIASES_BY_CANONICAL.get("literal", []),
        ALIASES_BY_CANONICAL.get("number", []),
        ALIASES_BY_CANONICAL.get("string", []),
        ALIASES_BY_CANONICAL.get("boolean", []),
        ALIASES_BY_CANONICAL.get("array", []),
        ALIASES_BY_CANONICAL.get("list", []),
        ALIASES_BY_CANONICAL.get("set", []),
        ALIASES_BY_CANONICAL.get("dictionary", []),
        "binary_expression", "unary_expression", "assignment_expression",
        "member_expression", "selector_expression", "field_expression",
        "parenthesized_expression", "conditional_expression",
        "ternary_expression", "await_expression", "yield_expression",
    ),

    "ASSIGN": _pec_unique(
        "assignment", "=",
        ALIASES_BY_CANONICAL.get("assignment", []),
        "assignment_statement", "assignment_expression",
        "augmented_assignment", "augmented_assignment_expression",
        "compound_assignment_expr", "operator_assignment",
        "variable_declaration", "variable_declarator", "local_variable_declaration",
        "lexical_declaration", "let_declaration", "var_declaration",
        "short_var_declaration", "const_declaration", "const_spec",
        "init_declarator", "declaration",
    ),

    "CTRL": _pec_unique(
        "if", "else", "switch", "case", "default", "for", "while",
        "break", "continue", "try", "catch", "finally", "with",
        "throw", "raise", "return", "exit",
        ALIASES_BY_CANONICAL.get("if", []),
        ALIASES_BY_CANONICAL.get("else", []),
        ALIASES_BY_CANONICAL.get("switch", []),
        ALIASES_BY_CANONICAL.get("case", []),
        ALIASES_BY_CANONICAL.get("default", []),
        ALIASES_BY_CANONICAL.get("for", []),
        ALIASES_BY_CANONICAL.get("while", []),
        ALIASES_BY_CANONICAL.get("break", []),
        ALIASES_BY_CANONICAL.get("continue", []),
        ALIASES_BY_CANONICAL.get("try", []),
        ALIASES_BY_CANONICAL.get("catch", []),
        ALIASES_BY_CANONICAL.get("finally", []),
        ALIASES_BY_CANONICAL.get("with", []),
        ALIASES_BY_CANONICAL.get("throw", []),
        ALIASES_BY_CANONICAL.get("raise", []),
        ALIASES_BY_CANONICAL.get("return", []),
        ALIASES_BY_CANONICAL.get("exit", []),
        "elif", "elseif", "elsif", "do_statement",
        "foreach_statement", "enhanced_for_statement",
        "match_expression", "match",
    ),

    "SUBP": _pec_unique(
        "function", "parameter",
        ALIASES_BY_CANONICAL.get("function", []),
        ALIASES_BY_CANONICAL.get("parameter", []),
        "method", "method_declaration", "function_declaration",
        "function_definition", "constructor_declaration", "lambda",
        "lambda_expression", "anonymous_function", "arrow_function",
        "generator_function", "generator_function_declaration",
        "formal_parameter", "formal_parameters", "parameter_list",
        "parameters", "method_parameters",
    ),

    "OOP": _pec_unique(
        "class",
        ALIASES_BY_CANONICAL.get("class", []),
        "class_declaration", "class_definition", "interface_declaration",
        "struct_declaration", "struct_item", "enum_declaration", "enum_item",
        "trait_item", "impl_item", "implementation_item",
        "anonymous_class",
        "extends", "implements",
    ),
}

PEC_NODE_TO_CATEGORIES = {}
for _pec_category, _pec_nodes in PEC_NODE_GROUPS.items():
    for _pec_node in _pec_nodes:
        PEC_NODE_TO_CATEGORIES.setdefault(_pec_node, set()).add(_pec_category)

PEC_NODE_GROUPS_BY_LANGUAGE = {
    "cs": {
        **PEC_NODE_GROUPS,
        "TYPE": _pec_unique(
            "type",
            ALIASES_BY_CANONICAL.get("type", []),
            "int", "integer", "float", "double", "long", "decimal",
            "bool", "boolean", "char", "byte", "short", "void", "string",
        ),
    },
}


# =========================================================
# Heuristic groups for annotator / filtering
# Keep these aligned with canonical vocabulary
# =========================================================


FUNCTIONS_NODES = {
    "go" :  [
        "function", "method_declaration",
    ],
    "python" : [
       "function",
    ],
    "ruby" : [
       "function",
    ],
    "php" : [
       "function",
    ],
    "java" : [
       "function",
    ],
    "javascript": [
       "function",
    ],
    "cs" : [
       "function",
    ],
    "cpp" : [
       "function",
    ],
    "rust" : [
       "function",
    ],   
}

# FUNCTION_NODES = [
#     "function","method_declaration",
# ]

EXPRESSION_NODES = [
    "expression",
]

    
VARIABLES_NODES = {
    "go" :  [
        "variable", "identifier" ,"field_identifier", "package_identifier","label_name"
    ],
    "python" : [
        "variable",
    ],
    "ruby" : [
        "variable", "instance_variable", "class_variable","global_variable","instance_variable"
    ],
    "php" : [
        "variable","name","variable_name"
    ],
    "java" : [
        "variable","identifier"
    ],
    "javascript": [
        "variable",
    ],
    "cs" : [
        "variable","identifier"
    ],
    "cpp" : [
        "variable",
    ],
    "rust" : [
        "variable",
    ],   
}


# VARIABLE_NODES = [
#     "name",
#     "property_identifier",
#     "field_identifier",
#     "variable",
#     "identifier",
#     "field_identifier",
#     "package_identifier",
#     "property_identifier",
#     "scoped_identifier",
#     "statement_identifier",
#     "instance_variable",
#     "class_variable",
#     "global_variable",
# ]

CALL_NODES = [
    "call",
]

TYPE_NODES = [
    "type",
]

# MODULE_NODES = [
#     "module",
# ]

KEY_NODES = [
    "args",
    "class",
    "void",
    "int",
    "string",
    "boolean",
    "bool",
    "console",
    "log",
    "system",
    "_",
    "-",
    "try",
    "catch",
    "finally",
    "variable",
]

# only ignorable wrappers / metadata-like nodes
# do not put identifier / parameter / module here
IGNORE_NODES = [
    "comment",
]


# =========================================================
# Wrapper nodes
# =========================================================

WRAPPER_CANDIDATES = [
    "compilation_unit",
    # "module",
    "program",
    "source_file",
    "translation_unit",
]


# =========================================================
# Compression / skipping rules
# Keep for backward compatibility, but cleaned.
# Prefer list-based usage in future code.
# =========================================================

NODE_REMOVE = {
    'null,this,from,new,protected,public,static,virtual,var,void,int,bool,override,**,(),$,;,(,),{,},:,\"': ''
}

NODE_SKIP = {
'expression_statement,expression_list,modifiers,formal_parameters,field_declaration_list,var_spec_list,const_declaration,field_declaration,scoped_call_expression,function_call_expression,string_literal,encapsed_string,template_string,heredoc,nowdoc,concatenated_string,chained_string,string_array,enhanced_for_statement,for_in_statement,type_switch_statement,invocation_expression,expression_switch_statement,switch_case,case_statement,switch_block_statement_group,expression_case,list,tuple,dictionary,hash,list_comprehension,dictionary_comprehension,set_comprehension,generator_expression,subscript_expression,local_variable_declaration,var_declaration,const_spec,method_definition,method_elem,anonymous_function,lambda_expression,func_literal,generator_function_declaration,typed_default_parameter,spread_parameter,dotted_name,keyword_argument,object_pattern,declaration_list,array_pattern,tuple_pattern,shell_command_expression,as_pattern,pattern_list,formal_parameters,simple_parameter,variadic_parameter,arguments,variadic_unpacking,readonly,readonly_modifier,var_modifier,endif,php_tag,php_end_tag,endswitch,endwhile,abstract_modifier,use_declaration,match_block,declare_directive,declare_statement,property_element,property_declaration,block': ''
}
codes=['go','python','ruby','php','java','javascript','cs']
codes = [
    """"
    def print_log(text, *colors):
    \"\"\"Print a log message to standard error.\"\"\"
    sys.stderr.write(sprint("{}: {}".format(script_name, text), *colors) + "\n")
    """,        # 0: Go
    "y = x + z * 3",         # 1: Python
    "y = x + z * 3",         # 2: Ruby
    "$y = $x + $z * 3;",     # 3: PHP
    "y = x + z * 3;",        # 4: Java
    "y = x + z * 3;"         # 5: JavaScript
]

# codes = [
#     # 0: Go
# """func NewSTM(c *v3.Client, apply func(STM) error, so ...stmOption) (*v3.TxnResponse, error) {\n\topts := &stmOptions{ctx: c.Ctx()}\n\tfor _, f := range so {\n\t\tf(opts)\n\t}\n\tif len(opts.prefetch) != 0 {\n\t\tf := apply\n\t\tapply = func(s STM) error {\n\t\t\ts.Get(opts.prefetch...)\n\t\t\treturn f(s)\n\t\t}\n\t}\n\treturn runSTM(mkSTM(c, opts), apply)\n}""",

#     # 1: Python
# """
# def hitung(x, z):
#     return x + z * 3""",

#     # 2: Ruby
# """
# def hitung(x, z)
#     return x + z * 3
# end""",

#     # 3: PHP
# """
# function hitung($x, $z) {
#     return $x + $z * 3;
# }""",

#     # 4: Java
# """public int hitung(int x, int z) {
#     return x + z * 3;
# }""",

#     # 5: JavaScript
# """function hitung(x, z) {
#     return x + z * 3;
# }"""
# ]

# Contoh kode golang

# codes[0]="""
# package main
# import "fmt"

# func fib(n uint) uint {
#     if n == 0 {
#         return 0
#     } else if n == 1 {
#         return 1
#     } else {
#         return fib(n-1) + fib(n-2)
#     }
# }

# func main() {
# 	n := uint(10) // Variable Declaration
# 	fmt.Println(fib(n))

# 	// For Loop
# 	for i := 0; i < 5; i++ {
# 		fmt.Println("Iteration:", i)
# 	}

# 	// While Loop (Simulasi dengan for)
# 	x := 5
# 	for x > 0 {
# 		fmt.Println("Countdown:", x)
# 		x--
# 	}

# 	// Assignment
# 	str := "Go is fun!"
# 	num := 42
# 	flag := true

# 	fmt.Println(str, num, flag)
# }
# """

# # Contoh kode Python
# codes[1]="""
# def fib(n):
#     if n == 0:
#         return 0
#     elif n == 1:
#         return 1
#     else:
#         return fib(n - 1) + fib(n - 2)

# def main():
#     n = 10  # Variable Declaration
#     print(fib(n))

#     # For Loop
#     for i in range(5):
#         print(f"Iteration: {i}")

#     # While Loop
#     x = 5
#     while x > 0:
#         print(f"Countdown: {x}")
#         x -= 1

#     # Assignment
#     str_val = "Python is great!"
#     num_val = 42
#     bool_val = True

#     print(str_val, num_val, bool_val)

# main()
# """

# # Contoh kode Ruby
# codes[2]="""
# def fib(n)
#   if n == 0
#     return 0
#   elsif n == 1
#     return 1
#   else
#     return fib(n - 1) + fib(n - 2)
#   end
# end

# def main
#   n = 10  # Variable Declaration
#   puts fib(n)

#   # For Loop
#   for i in 1..5 do
#     puts "Iteration: #{i}"
#   end

#   # While Loop
#   x = 5
#   while x > 0 
#     puts "Countdown: #{x}"
#     x -= 1
#   end

#   # Assignment
#   str_val = "Ruby is awesome!"
#   num_val = 42
#   bool_val = true

#   puts str_val, num_val, bool_val
# end

# main()
# """

# # Contoh kode PHP
# codes[3]="""
# <?php
# function fib($n) {
#     if ($n == 0) {
#         return 0;
#     } else if ($n == 1) {
#         return 1;
#     } else {
#         return fib($n - 1) + fib($n - 2);
#     }
# }

# function main() {
#     $n = 10; // Variable Declaration
#     echo fib($n) . PHP_EOL;

#     // For Loop
#     for ($i = 0; $i < 5; $i++) {
#         echo "Iteration: $i\n";
#     }

#     // While Loop
#     $x = 5;
#     while ($x > 0) {
#         echo "Countdown: $x\n";
#         $x--;
#     }

#     // Assignment
#     $str_val = "PHP is powerful!";
#     $num_val = 42;
#     $bool_val = true;

#     echo "$str_val, $num_val, $bool_val\n";
# }

# main();
# ?>
# """

# # Contoh kode Java
# codes[4]="""
# public class Fibonacci {
#     public static void main(String[] args) {
#         int n = 10; // Variable Declaration
#         System.out.println(fib(n));

#         // For Loop
#         for (int i = 0; i < 5; i++) {
#             System.out.println("Iteration: " + i);
#         }

#         // While Loop
#         int x = 5;
#         while (x > 0) {
#             System.out.println("Countdown: " + x);
#             x--;
#         }

#         // Assignment
#         String str_val = "Java is versatile!";
#         int num_val = 42;
#         boolean bool_val = true;

#         System.out.println(str_val + ", " + num_val + ", " + bool_val);
#     }

#     public static int fib(int n) {
#         if (n == 0) {
#             return 0;
#         } else if (n == 1) {
#             return 1;
#         } else {
#             return fib(n - 1) + fib(n - 2);
#         }
#     }
# }

# """

# # Contoh kode JavaScript
# codes[5]="""
# function fib(n) {
#     if (n === 0) {
#         return 0;
#     } else if (n === 1) {
#         return 1;
#     } else {
#         return fib(n - 1) + fib(n - 2);
#     }
# }

# function main() {
#     let n = 10; // Variable Declaration
#     console.log(fib(n));

#     // For Loop
#     for (let i = 0; i < 5; i++) {
#         console.log("Iteration:", i);
#     }

#     // While Loop
#     let x = 5;
#     while (x > 0) {
#         console.log("Countdown:", x);
#         x--;
#     }

#     // Assignment
#     let str_val = "JavaScript is dynamic!";
#     let num_val = 42;
#     let bool_val = true;

#     console.log(str_val, num_val, bool_val);
# }

# main();

# """
