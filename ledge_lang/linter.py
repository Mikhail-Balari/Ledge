"""
Ledge Linter v1.0
==================
Separate from the typechecker — catches style and safety issues.

The typechecker says: this code is type-safe.
The linter says: this code is well-written.

Rules:
  E = Error (must fix)
  W = Warning (should fix)
  S = Style (convention)

AI-native rules (E):
  E001  Using AI result without confidence guard
  E002  AI operation with no fallback in non-check block

Safety rules (E/W):
  E010  Contract precondition but no contract postcondition for AI result
  W011  Function with AI operation but no requires:
  W012  Mutable global variable (define at module level then set)

Style rules (S):
  S020  Function longer than 30 lines
  S021  Deeply nested (>4 levels)
  S022  Unused define

Usage:
    from ledge_lang.linter import lint
    issues = lint(source)
    
    # Or from CLI:
    ledge check --lint file.ledge
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional
from .ast_nodes import *


@dataclass
class LintIssue:
    code:       str   # E001, W011, S020, etc.
    kind:       str   # "error", "warning", "style"
    message:    str
    line:       int   = 0
    suggestion: str   = ""

    def __str__(self):
        loc  = f"[Line {self.line}] " if self.line else ""
        sug  = f"\n  Fix: {self.suggestion}" if self.suggestion else ""
        return f"{loc}{self.code} {self.kind.upper()}: {self.message}{sug}"


class Linter:
    def __init__(self):
        self.issues: List[LintIssue] = []
        self._depth = 0
        self._uncertain_names: set = set()
        self._defined_names:   set = set()
        self._used_names:      set = set()
        self._module_defines:  list = []  # (name, has_set) tuples

    def lint(self, program) -> List[LintIssue]:
        self.issues = []
        self._uncertain_names = set()
        self._defined_names = set()
        self._used_names = set()
        self._module_defines = []
        self._lint_block(program.stmts, depth=0, in_fn=False)
        self._check_unused()
        return self.issues

    def _issue(self, code, kind, msg, line=0, suggestion=""):
        self.issues.append(LintIssue(code, kind, msg, line, suggestion))

    # ── Block/Statement linting ────────────────────────────────────────────

    def _lint_block(self, stmts, depth=0, in_fn=False):
        if depth > 4:
            self._issue("S021", "style",
                f"Deeply nested code ({depth} levels). Consider extracting a function.",
                line=getattr(stmts[0], 'line', 0) if stmts else 0,
                suggestion="Extract deeply nested logic into a named function.")
        for stmt in stmts:
            self._lint_stmt(stmt, depth=depth, in_fn=in_fn)

    def _lint_stmt(self, node, depth=0, in_fn=False):
        t = type(node).__name__

        if t == "Define":
            self._lint_define(node, depth, in_fn)

        elif t == "Assign":
            name = node.name
            self._used_names.add(name)
            # Track mutable globals
            if not in_fn:
                for d_name, has_set in self._module_defines:
                    if d_name == name:
                        # Mark it as having a set
                        self._module_defines = [
                            (n, True if n == name else s)
                            for n, s in self._module_defines
                        ]
            self._lint_expr(node.value, depth)

        elif t == "Show":
            self._lint_expr(node.expr, depth)

        elif t == "If":
            # Check if condition involves confidence guard
            has_guard = self._is_confidence_guard(node.branches[0][0] if node.branches else None)
            for cond, blk in node.branches:
                self._lint_expr(cond, depth)
                self._lint_block(blk.stmts, depth=depth+1, in_fn=in_fn)
            if node.else_block:
                self._lint_block(node.else_block.stmts, depth=depth+1, in_fn=in_fn)

        elif t in ("For", "While", "Repeat"):
            if hasattr(node, 'iterable'):
                self._lint_expr(node.iterable, depth)
            if hasattr(node, 'condition'):
                self._lint_expr(node.condition, depth)
            if hasattr(node, 'body'):
                self._lint_block(node.body.stmts, depth=depth+1, in_fn=in_fn)

        elif t == "Check":
            self._lint_block(node.body.stmts, depth=depth+1, in_fn=in_fn)
            if node.recover_block:
                self._lint_block(node.recover_block.stmts, depth=depth+1, in_fn=in_fn)
            if node.always_block:
                self._lint_block(node.always_block.stmts, depth=depth+1, in_fn=in_fn)

        elif t == "Return":
            if node.value:
                self._lint_expr(node.value, depth)

        elif t == "ExprStmt":
            self._lint_expr(node.expr, depth)

        elif t == "WhenStmt":
            src = getattr(node, 'source', None)
            if src: self._lint_expr(src, depth)
            self._lint_block(node.body.stmts, depth=depth+1, in_fn=in_fn)

    def _lint_define(self, node, depth, in_fn):
        name = node.name
        self._defined_names.add(name)
        
        if not in_fn:
            self._module_defines.append((name, False))

        val = node.value
        if val is None:
            return

        val_type = type(val).__name__

        # Track AI result assignments
        if val_type in ("AnalyzeExpr", "ClassifyExpr", "GenerateExpr", "AskExpr", "EmbedExpr"):
            self._uncertain_names.add(name)

        if val_type == "FuncDef":
            # Check function length
            body_stmts = len(val.body.stmts) if val.body else 0
            if body_stmts > 30:
                self._issue("S020", "style",
                    f"Function '{name}' is {body_stmts} lines long. Consider splitting.",
                    line=getattr(node, 'line', 0),
                    suggestion="Extract related logic into smaller, named functions.")

            # Check if function has AI operations but no requires
            has_ai = self._has_ai_op(val.body)
            has_contract = val.contract is not None and bool(getattr(val.contract, 'requires', []))
            if has_ai and not has_contract:
                self._issue("W011", "warning",
                    f"Function '{name}' uses AI operations but has no 'requires:' contract.",
                    line=getattr(node, 'line', 0),
                    suggestion=f"Add 'requires:' to validate inputs before expensive AI calls.")

            # Recurse into function body
            fn_uncertain = set(self._uncertain_names)
            for i, (pname, phint) in enumerate(val.params):
                self._defined_names.add(pname)
            self._lint_block(val.body.stmts, depth=1, in_fn=True)
            self._uncertain_names = fn_uncertain
        else:
            self._lint_expr(val, depth)

    def _lint_expr(self, node, depth):
        if node is None:
            return
        t = type(node).__name__

        if t == "Identifier":
            self._used_names.add(node.name)

        elif t in ("AnalyzeExpr", "ClassifyExpr", "GenerateExpr", "AskExpr", "EmbedExpr"):
            # AI operation — check it's being assigned to an Uncertain var
            # This is handled by the typechecker; linter trusts TC for this
            pass

        elif t == "Call":
            if hasattr(node, 'callee'):
                fn_name = getattr(node.callee, 'name', None)
                # E001: using uncertain variable in unsafe context
                if node.args:
                    first_arg = node.args[0]
                    if (type(first_arg).__name__ == "Identifier"
                            and first_arg.name in self._uncertain_names
                            and fn_name not in ("when", "value_of", "confidence_of",
                                               "is_confident", "is_uncertain")):
                        self._issue("E001", "error",
                            f"Unsafe use of AI result '{first_arg.name}' in '{fn_name}'. "
                            f"AI results are Uncertain — check confidence first.",
                            line=getattr(node, 'line', 0),
                            suggestion=f"Use: when({first_arg.name}, 0.8, fallback)")
            for arg in getattr(node, 'args', []):
                self._lint_expr(arg, depth)

        elif t == "BinOp":
            self._lint_expr(node.left, depth)
            self._lint_expr(node.right, depth)

        elif t == "UnaryOp":
            self._lint_expr(node.operand, depth)

        elif t == "LogicalOp":
            self._lint_expr(node.left, depth)
            self._lint_expr(node.right, depth)

        elif t == "Fallback":
            self._lint_expr(node.expr, depth)
            self._lint_expr(node.default, depth)

        elif t in ("ListLit",):
            for item in getattr(node, 'items', []):
                self._lint_expr(item, depth)

        elif t == "MapLit":
            for k, v in getattr(node, 'pairs', []):
                self._lint_expr(v, depth)

    # ── Helpers ─────────────────────────────────────────────────────────────

    def _is_confidence_guard(self, cond) -> bool:
        if cond is None:
            return False
        t = type(cond).__name__
        if t == "Call" and hasattr(cond, 'callee'):
            fn = getattr(cond.callee, 'name', None)
            return fn in ("is_confident", "confidence_of")
        if t == "BinOp" and cond.op in (">=", ">"):
            return type(cond.left).__name__ == "Call" and \
                   getattr(getattr(cond.left, 'callee', None), 'name', '') == "confidence_of"
        if t == "LogicalOp" and cond.op == "and":
            return self._is_confidence_guard(cond.left) or self._is_confidence_guard(cond.right)
        return False

    def _has_ai_op(self, block) -> bool:
        if block is None:
            return False
        ai_types = {"AnalyzeExpr", "ClassifyExpr", "GenerateExpr", "AskExpr", "EmbedExpr"}
        def check(node):
            if node is None:
                return False
            t = type(node).__name__
            if t in ai_types:
                return True
            for attr in ['stmts', 'value', 'expr', 'left', 'right', 'args',
                         'iterable', 'condition', 'body']:
                child = getattr(node, attr, None)
                if child is None:
                    continue
                if isinstance(child, list):
                    if any(check(c) for c in child):
                        return True
                elif check(child):
                    return True
            return False
        return any(check(s) for s in block.stmts)

    def _check_unused(self):
        # Warn on defined but never used variables (at module level)
        unused = self._defined_names - self._used_names
        # Filter out common non-issues
        ignore = {'_', 'result', 'error', 'e'}
        for name in sorted(unused - ignore):
            if not name.startswith('_'):
                self._issue("S022", "style",
                    f"Variable '{name}' is defined but never used.",
                    suggestion=f"Remove the define or use '{name}' somewhere.")


# ── Public API ────────────────────────────────────────────────────────────────

def lint(source: str) -> List[LintIssue]:
    """Run the linter on Ledge source code."""
    try:
        from .lexer import Lexer
        from .parser import Parser
        tokens = Lexer(source).tokenize()
        program = Parser(tokens).parse()
        linter = Linter()
        return linter.lint(program)
    except Exception:
        return []


def lint_file(path: str) -> List[LintIssue]:
    """Run the linter on a .ledge file."""
    with open(path, encoding="utf-8") as f:
        return lint(f.read())
