"""
Ledge Type Checker v1.0
=======================
Static analysis for Ledge programs with AI-native type safety.

Two levels of severity:
  ERROR   — unsafe use of Uncertain[T] as if it were T without extraction
  WARNING — type annotation mismatch (advisory for non-AI types)

AI-native rules (ERRORS, not warnings):
  1. Using result of analyze/classify/generate/ask/embed directly
     without checking confidence or extracting value is an ERROR.
  2. Assigning Uncertain value to a declared typed variable is an ERROR.

This design is intentional: in a language built for AI, using AI output
as if it were certain is the primary source of bugs. The type checker
enforces safe handling.

Usage:
    from ledge_lang.typechecker import check_types
    issues = check_types(source)   # returns list of Issue

Each Issue has: kind ("error"|"warning"), message, line, suggestion.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Set
from .ast_nodes import *


# ── Issue types ───────────────────────────────────────────────────────────────

@dataclass
class Issue:
    kind:       str        # "error" or "warning"
    message:    str
    line:       int = 0
    suggestion: str = ""

    def __str__(self):
        loc  = f"[Line {self.line}] " if self.line else ""
        sug  = f"\n  Suggestion: {self.suggestion}" if self.suggestion else ""
        kind = self.kind.upper()
        return f"{loc}{kind}: {self.message}{sug}"

    @property
    def is_error(self):   return self.kind == "error"
    @property
    def is_warning(self): return self.kind == "warning"


# ── Type environment for the checker ─────────────────────────────────────────

class TypeEnv:
    def __init__(self, parent=None):
        self._types: Dict[str, str] = {}
        self.parent = parent

    def set(self, name: str, type_str: str):
        self._types[name] = type_str

    def get(self, name: str) -> Optional[str]:
        if name in self._types: return self._types[name]
        if self.parent:         return self.parent.get(name)
        return None

    def child(self) -> 'TypeEnv':
        return TypeEnv(parent=self)


# ── AI-returning expression types ────────────────────────────────────────────

AI_RETURNING_NODES = {
    "AnalyzeExpr":  "uncertain[map]",
    "ClassifyExpr": "uncertain[text]",
    "GenerateExpr": "uncertain[text]",
    "AskExpr":      "uncertain[text]",
    "EmbedExpr":    "uncertain[list]",
}

UNCERTAIN_SAFE_BUILTINS = {
    "confidence_of", "value_of", "is_uncertain", "is_confident",
    "when", "confidence_of", "uncertainty_of",
}

SAFE_UNWRAP_PATTERNS = {
    "when", "value_of", "confidence_of", "is_confident", "is_uncertain", "type", "str", "repr",
}


# ── Checker ───────────────────────────────────────────────────────────────────

class TypeChecker:
    def __init__(self):
        self.issues:     List[Issue]   = []
        self._env:       TypeEnv       = TypeEnv()
        self._uncertain: Set[str]      = set()  # names known to be Uncertain
        self._confidence_aliases: Dict[str, str] = {}  # alias var → original uncertain var

    # ── Entry point ───────────────────────────────────────────────────────────

    def check(self, program) -> List[Issue]:
        self.issues = []
        self._uncertain = set()
        self._confidence_aliases = {}
        self._check_block(program.stmts, self._env)
        return self.issues

    def _error(self, msg: str, line: int = 0, suggestion: str = ""):
        self.issues.append(Issue("error", msg, line, suggestion))

    def _warn(self, msg: str, line: int = 0, suggestion: str = ""):
        self.issues.append(Issue("warning", msg, line, suggestion))

    # ── Statement checking ────────────────────────────────────────────────────

    def _check_block(self, stmts, env: TypeEnv):
        for stmt in stmts:
            self._check_stmt(stmt, env)

    def _check_stmt(self, node, env: TypeEnv):
        t = type(node).__name__

        if t == "Define":
            self._check_define(node, env)

        elif t == "Assign":
            self._check_assign(node, env)

        elif t == "Show":
            self._check_show(node, env)

        elif t == "If":
            for cond, blk in node.branches:
                self._check_expr(cond, env)
                self._check_as_boolean(cond, env)
                # Flow narrowing: if confidence check on uncertain var,
                # narrow its type inside the block
                narrowed = env.child()
                narrowed_vars = self._extract_confidence_narrowing(cond)
                for var_name in narrowed_vars:
                    narrowed.set(var_name, "any")  # unwrapped from Uncertain
                    if var_name in self._uncertain:
                        self._uncertain.discard(var_name)
                self._check_block(blk.stmts, narrowed)
                # Restore after block
                for var_name in narrowed_vars:
                    if var_name in narrowed._types:
                        self._uncertain.add(var_name)
            if node.else_block:
                self._check_block(node.else_block.stmts, env.child())

        elif t == "For":
            iter_type = self._infer_type(node.iterable, env) if hasattr(node, 'iterable') else None
            c = env.child()
            elem_is_uncertain = bool(iter_type and iter_type.startswith("list[uncertain"))
            if hasattr(node, 'var'):
                if elem_is_uncertain:
                    self._uncertain.add(node.var)
                    c.set(node.var, "uncertain[any]")
                else:
                    c.set(node.var, "any")
            if hasattr(node, 'body'):
                self._check_block(node.body.stmts, c)
            if elem_is_uncertain and hasattr(node, 'var'):
                self._uncertain.discard(node.var)

        elif t in ("While", "Repeat"):
            if hasattr(node, 'condition'):
                self._check_expr(node.condition, env)
                self._check_as_boolean(node.condition, env)
            if hasattr(node, 'body'):
                c = env.child()
                self._check_block(node.body.stmts, c)

        elif t == "FuncDef" or (t == "Define" and hasattr(node, 'value') and
                                 type(getattr(node, 'value', None)).__name__ == "FuncDef"):
            pass  # handled in _check_define

        elif t == "Return":
            if node.value:
                self._check_expr(node.value, env)

        elif t == "ExprStmt":
            self._check_expr(node.expr, env)

        elif t == "Check":
            self._check_block(node.body.stmts, env.child())
            if node.recover_block:
                c = env.child()
                if node.recover_var:
                    c.set(node.recover_var, "text")
                self._check_block(node.recover_block.stmts, c)
            if node.always_block:
                self._check_block(node.always_block.stmts, env.child())

    def _check_define(self, node, env: TypeEnv):
        val_node = node.value
        if val_node is None:
            return

        val_type = type(val_node).__name__
        expr_type = self._infer_type(val_node, env)

        # Rule [DEF] + Compatibility: Uncertain[T] not compatible with non-uncertain type
        if expr_type and expr_type.startswith("uncertain"):
            self._uncertain.add(node.name)
            if node.type_hint and not node.type_hint.startswith("uncertain"):
                self._error(
                    f"'{node.name}' is declared as '{node.type_hint}' but receives "
                    f"an AI result of type '{expr_type}'. "
                    f"AI operations always return Uncertain[T] — "
                    f"you must handle low-confidence results explicitly.",
                    line=getattr(node, 'line', 0),
                    suggestion=(
                        f"Use: define {node.name} as when(ai_result, 0.8, fallback_value)\n"
                        f"  Or: define {node.name} as value_of(ai_result)  # only if confident"
                    )
                )
        else:
            # Normal type annotation check
            if node.type_hint and expr_type:
                if not self._compatible(expr_type, node.type_hint):
                    hint = node.type_hint
                    concrete = ("number","text","truth","list","map")
                    if hint == "any" or expr_type == "any":
                        pass
                    elif expr_type in concrete and hint in concrete:
                        msg = (
                            "Type mismatch: '" + node.name + "' is declared as '" + hint + "' "
                            "but assigned '" + expr_type + "'."
                        )
                        self._error(msg + "\n  Fix: Remove annotation or use a " + hint + " value.",
                                    line=getattr(node, "line", 0))
                    else:
                        self._warn(
                            "'" + node.name + "' declared as '" + hint + "' "
                            "but assigned '" + expr_type + "'",
                            line=getattr(node, "line", 0)
                        )

        # LIMITACION B: track define c as confidence_of(r) as a confidence alias
        if (val_type == "Call"
                and getattr(getattr(val_node, 'callee', None), 'name', None) == "confidence_of"
                and getattr(val_node, 'args', None)):
            arg = val_node.args[0]
            if type(arg).__name__ == "Identifier" and arg.name in self._uncertain:
                self._confidence_aliases[node.name] = arg.name

        env.set(node.name, expr_type or node.type_hint or "any")

        # Check function body if it's a function definition
        if val_type == "FuncDef":
            c = env.child()
            for pname, phint in val_node.params:
                c.set(pname, phint or "any")
            self._check_block(val_node.body.stmts, c)

    def _check_assign(self, node, env: TypeEnv):
        val_type = self._infer_type(node.value, env)
        declared = env.get(node.name)

        if val_type and val_type.startswith("uncertain"):
            if declared and not declared.startswith("uncertain"):
                self._error(
                    f"Cannot assign AI result (Uncertain[T]) to '{node.name}' "
                    f"which is declared as '{declared}'. "
                    f"Extract the value first.",
                    line=getattr(node, 'line', 0),
                    suggestion=(
                        f"set {node.name} to when(ai_result, 0.8, fallback)"
                    )
                )

        elif declared and val_type and not self._compatible(val_type, declared):
            self._error(
                f"Type error: '{node.name}' is declared as '{declared}', "
                f"cannot assign '{val_type}'",
                line=getattr(node, 'line', 0)
            )

    def _check_show(self, node, env: TypeEnv):
        expr_type = self._infer_type(node.expr, env)
        # Rule [UNSAFE-SHOW]: using Uncertain[T] directly in show is an ERROR.
        # The variable still carries unverified AI output — confidence was never
        # checked, so the value may be unreliable.
        if expr_type and expr_type.startswith("uncertain"):
            var_name = getattr(node.expr, 'name', 'result')
            self._error(
                f"Unsafe use of Uncertain value '{var_name}' in 'show' — "
                f"confidence was never verified. AI results must be explicitly "
                f"checked before use.",
                line=getattr(node, 'line', 0),
                suggestion=(
                    f"show value_of({var_name})                       -- extract value (skip if low-confidence)\n"
                    f"  show when({var_name}, 0.8, 'fallback')          -- safe extraction with threshold\n"
                    f"  show confidence_of({var_name})                  -- show the confidence score\n"
                    f"  if confidence_of({var_name}) >= 0.85: show ...   -- guard then use"
                )
            )

    # ── Expression type inference ─────────────────────────────────────────────

    def _infer_type(self, node, env: TypeEnv) -> Optional[str]:
        if node is None:
            return None
        t = type(node).__name__

        if t == "NumberLit":   return "number"
        if t == "StringLit":   return "text"
        if t == "BoolLit":     return "truth"
        if t == "NothingLit":  return "nothing"
        if t == "ListLit":     return "list"
        if t == "MapLit":      return "map"

        if t == "Identifier":
            # Check if we know this is uncertain
            if node.name in self._uncertain:
                return "uncertain[any]"
            return env.get(node.name) or "any"

        if t in AI_RETURNING_NODES:
            return AI_RETURNING_NODES[t]

        if t == "Call":
            # Check: calling a safe unwrap on uncertain → returns inner type
            if hasattr(node.callee, 'name'):
                fn_name = node.callee.name
                if fn_name in ("when", "value_of"):
                    return "any"  # extracting from Uncertain
                if fn_name in ("confidence_of",):
                    return "number"
                if fn_name in ("is_confident", "is_uncertain", "type", "str", "repr"):
                    return "truth"
                # LIMITACION A: map(list, given x: ai_expr) → list[uncertain[...]]
                if fn_name == "map" and len(node.args) >= 2:
                    fn_arg = node.args[1]
                    if type(fn_arg).__name__ == "Lambda":
                        lambda_env = env.child()
                        for p in fn_arg.params:
                            lambda_env.set(p, "any")
                        body_type = self._infer_type(fn_arg.body, lambda_env)
                        if body_type and body_type.startswith("uncertain"):
                            return f"list[{body_type}]"
                    return "list"
                # Check: using uncertain value in unsafe position
                if node.args:
                    first_arg_type = self._infer_type(node.args[0], env) if node.args else None
                    if (first_arg_type and first_arg_type.startswith("uncertain")
                            and fn_name not in UNCERTAIN_SAFE_BUILTINS):
                        self._error(
                            f"Unsafe use of Uncertain value as argument to '{fn_name}'. "
                            f"AI results must be checked for confidence before use.",
                            line=getattr(node, 'line', 0),
                            suggestion=(
                                f"Use: when(ai_result, 0.8, fallback) to extract safely\n"
                                f"  Or: if is_confident(ai_result): ...  to guard first"
                            )
                        )
            return "any"

        if t == "BinOp":
            l = self._infer_type(node.left, env)
            r = self._infer_type(node.right, env)
            # Rule [UNSAFE-USE]: Uncertain[T] must be extracted before arithmetic
            for side, side_node in [(l, node.left), (r, node.right)]:
                if side.startswith("uncertain"):
                    var_name = getattr(side_node, "name", None)
                    if var_name and var_name in self._uncertain:
                        # Rule [UNSAFE-USE]: arithmetic on Uncertain is an ERROR
                        # (would operate on the Uncertain wrapper, not the inner value)
                        self._error(
                            f"Unsafe use of Uncertain value '{var_name}' in arithmetic. "
                            f"Extract value first: value_of({var_name}) or when({var_name}, 0.8, fallback)",
                            getattr(side_node, "line", 0)
                        )
            if node.op == "+":
                if l == "number" and r == "number": return "number"
                if l == "text"   or r == "text":    return "text"
                if l == "list"   and r == "list":   return "list"
            if node.op in ("-", "*", "/"):             return "number"
            if node.op in ("=", "!=", "<", ">", "<=", ">="): return "truth"
            return "any"

        if t == "LogicalOp":
            left_type  = self._infer_type(node.left, env)
            right_type = self._infer_type(node.right, env)
            for side_type, side_node in [(left_type, node.left), (right_type, node.right)]:
                if side_type and side_type.startswith("uncertain"):
                    var_name = getattr(side_node, 'name', 'value')
                    self._error(
                        f"Unsafe use of Uncertain value '{var_name}' as boolean condition — "
                        f"confidence was never verified. "
                        f"Use: if confidence_of({var_name}) >= threshold:",
                        line=getattr(side_node, 'line', 0),
                        suggestion=f"if confidence_of({var_name}) >= 0.85:"
                    )
            return "truth"

        if t == "UnaryOp":
            if node.op == "not":
                operand_type = self._infer_type(node.operand, env)
                if operand_type and operand_type.startswith("uncertain"):
                    var_name = getattr(node.operand, 'name', 'value')
                    self._error(
                        f"Unsafe use of Uncertain value '{var_name}' as boolean condition — "
                        f"confidence was never verified. "
                        f"Use: if confidence_of({var_name}) >= threshold:",
                        line=getattr(node, 'line', 0),
                        suggestion=f"if confidence_of({var_name}) >= 0.85:"
                    )
                return "truth"
            if node.op == "-":   return "number"

        if t == "Fallback":
            left = self._infer_type(node.expr, env)
            if left and left.startswith("uncertain"):
                # or on uncertain — this is SAFE, it extracts with fallback
                return self._infer_type(node.default, env)
            return left or self._infer_type(node.default, env)

        if t == "Lambda":      return "function"
        if t == "FuncDef":     return "function"

        return "any"

    def _check_expr(self, node, env: TypeEnv):
        """Check an expression for issues (without returning type)."""
        self._infer_type(node, env)

    def _compatible(self, actual: str, declared: str) -> bool:
        """Check if actual type is compatible with declared annotation."""
        if declared in ("any", "unknown"): return True
        if actual == "any":                return True
        if actual == "nothing":            return True  # nothing is always compatible
        if actual == declared:             return True
        # uncertain is NOT compatible with any non-uncertain type
        if actual.startswith("uncertain") and not declared.startswith("uncertain"):
            return False
        return False


    def _check_as_boolean(self, node, env: TypeEnv):
        """Emit error if node is a bare Uncertain identifier used as boolean condition."""
        if type(node).__name__ == "Identifier" and node.name in self._uncertain:
            self._error(
                f"Unsafe use of Uncertain value '{node.name}' as boolean condition — "
                f"confidence was never verified. "
                f"Use: if confidence_of({node.name}) >= threshold:",
                line=getattr(node, 'line', 0),
                suggestion=f"if confidence_of({node.name}) >= 0.85:"
            )

    def _extract_confidence_narrowing(self, cond) -> set:
        """
        Extract variable names that are narrowed by a confidence check.
        Patterns recognized:
          - is_confident(var)
          - confidence_of(var) >= threshold
          - confidence_of(var) > threshold
        Returns set of variable names whose Uncertain type is narrowed.
        """
        narrowed = set()
        t = type(cond).__name__

        if t == "Call" and hasattr(cond, 'callee'):
            fn = getattr(cond.callee, 'name', None)
            if fn == "is_confident" and cond.args:
                arg = cond.args[0]
                if type(arg).__name__ == "Identifier":
                    narrowed.add(arg.name)

        elif t == "BinOp" and cond.op in (">=", ">", "="):
            left = cond.left
            # Pattern: confidence_of(var) >= threshold
            if (type(left).__name__ == "Call"
                    and hasattr(left, 'callee')
                    and getattr(left.callee, 'name', None) == "confidence_of"
                    and left.args):
                arg = left.args[0]
                if type(arg).__name__ == "Identifier":
                    narrowed.add(arg.name)
            # LIMITACION B: c >= threshold where c = confidence_of(r)
            elif (type(left).__name__ == "Identifier"
                    and left.name in self._confidence_aliases):
                narrowed.add(self._confidence_aliases[left.name])

        elif t == "LogicalOp" and cond.op == "and":
            # Combine narrowing from both sides
            narrowed.update(self._extract_confidence_narrowing(cond.left))
            narrowed.update(self._extract_confidence_narrowing(cond.right))

        return narrowed


# ── Public API ────────────────────────────────────────────────────────────────

class TypecheckerInternalError(Exception):
    """Raised when the typechecker itself fails — a bug in the checker, not user code."""
    pass


def check_types(source: str) -> List[Issue]:
    """
    Run the type checker on Ledge source code.
    Returns a list of Issue objects (errors and warnings).

    Raises TypecheckerInternalError if the checker itself crashes (not a user code error).
    User syntax errors (LexError, ParseError) are returned as Issues, not raised.
    """
    from .lexer import Lexer, LexError
    from .parser import Parser, ParseError

    try:
        tokens = Lexer(source).tokenize()
        program = Parser(tokens).parse()
    except (LexError, ParseError) as e:
        return [Issue("error", str(e), getattr(e, 'line', 0))]

    try:
        checker = TypeChecker()
        return checker.check(program)
    except Exception as e:
        import traceback
        raise TypecheckerInternalError(
            f"Internal typechecker error — this is a bug in the checker, not your code.\n"
            f"Error: {e}\n"
            f"{traceback.format_exc()}"
        ) from e


def check_file(path: str) -> List[Issue]:
    """Run the type checker on a .ledge file."""
    with open(path, encoding="utf-8") as f:
        return check_types(f.read())
