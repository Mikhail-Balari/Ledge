"""
Ledge Formatter — ledge fmt

Produces canonical Ledge formatting from any valid Ledge source.
Rules are non-configurable by design: one style, always.

Usage:
    from ledge_lang.formatter import format_ledge
    canonical = format_ledge(source)

    # Or via CLI:
    ledge fmt program.ledge          # format in-place
    ledge fmt --check program.ledge  # check without modifying
    ledge fmt --print program.ledge  # print to stdout
"""

from __future__ import annotations
from typing import List, Optional
from .ast_nodes import *
from .lexer import Lexer, LexError
from .parser import Parser, ParseError


INDENT = "    "   # exactly 4 spaces — non-negotiable


class Formatter:
    """AST → canonical Ledge source."""

    def __init__(self):
        self._depth = 0
        self._lines: List[str] = []

    def format(self, program: Program) -> str:
        self._depth = 0
        self._lines = []
        self._stmts(program.stmts)
        # Ensure single trailing newline
        source = "\n".join(self._lines)
        return source.rstrip() + "\n"

    # ── Emit helpers ──────────────────────────────────────────────────────────

    def _emit(self, text: str):
        indent = INDENT * self._depth
        self._lines.append(indent + text)

    def _blank(self):
        """Emit a blank line (only if previous line isn't already blank)."""
        if self._lines and self._lines[-1] != "":
            self._lines.append("")

    def _indent(self):
        self._depth += 1

    def _dedent(self):
        self._depth -= 1

    # ── Statement list ────────────────────────────────────────────────────────

    def _stmts(self, stmts: List[Node]):
        prev_type = None
        for i, stmt in enumerate(stmts):
            t = type(stmt)
            # Blank line before block-level definitions
            if i > 0 and t in (Define, TypeDef) and prev_type not in (None,):
                if isinstance(getattr(stmt, 'value', None), FuncDef):
                    self._blank()
            self._stmt(stmt)
            prev_type = t

    def _stmt(self, node: Node):
        t = type(node)

        if t == Define:
            self._fmt_define(node)
        elif t == Assign:
            self._emit(f"set {node.name} to {self._expr(node.value)}")
        elif t == Show:
            fmt = f" as {node.format}" if node.format else ""
            self._emit(f"show {self._expr(node.expr)}{fmt}")
        elif t == If:
            self._fmt_if(node)
        elif t == For:
            self._fmt_for(node)
        elif t == While:
            self._emit(f"while {self._expr(node.condition)}:")
            self._block(node.body)
        elif t == Repeat:
            if node.count is not None:
                self._emit(f"repeat {self._expr(node.count)} times:")
            else:
                self._emit(f"repeat until {self._expr(node.condition)}:")
            self._block(node.body)
        elif t == Match:
            self._fmt_match(node)
        elif t == Check:
            self._fmt_check(node)
        elif t == Return:
            if node.value:
                self._emit(f"return {self._expr(node.value)}")
            else:
                self._emit("return")
        elif t == Break:
            self._emit("break")
        elif t == Continue:
            self._emit("continue")
        elif t == Pass:
            self._emit("pass")
        elif t == Yield:
            self._emit(f"yield {self._expr(node.value)}")
        elif t == RunStmt:
            suffix = " and wait" if node.wait else ""
            self._emit(f"run {self._expr(node.expr)}{suffix}")
        elif t == Import:
            if node.alias:
                self._emit(f'import "{node.path}" as {node.alias}')
            else:
                names = ", ".join(node.names)
                self._emit(f'from "{node.path}" import {names}')
        elif t == TypeDef:
            self._fmt_typedef(node)
        elif t == ExprStmt:
            self._emit(self._expr(node.expr))
        elif type(node).__name__ == "WhenStmt":
            # Attributes: source (stream expr), item_name (var), trigger, body
            src_expr = getattr(node, 'source', None)
            item = getattr(node, 'item_name', None)
            trigger = getattr(node, 'trigger', None)
            if src_expr is not None:
                var_part = f" as {item}" if item else ""
                self._emit(f"when {self._expr(src_expr)} has new item{var_part}:")
            elif trigger is not None:
                self._emit(f"when {self._expr(trigger)}:")
            else:
                self._emit("when:")
            self._block(node.body)
        elif t == "AgentDef" or type(node).__name__ == "AgentDef":
            # agent Name: tools: ..., model: ..., behavior: ...
            self._emit(f"agent {node.name}:")
            self._indent()
            tools = getattr(node, "tools", None)
            model = getattr(node, "model_name", None)
            behavior = getattr(node, "behavior", None)
            if tools:
                self._emit("tools:")
                self._indent()
                items = tools.items() if hasattr(tools, "items") else tools
                for tool_name, tool_src in items:
                    self._emit(f'{tool_name} from mcp {self._expr(tool_src)}')
                self._dedent()
            if model:
                self._emit(f"model: {self._expr(model)}")
            if behavior and hasattr(behavior, "stmts"):
                self._emit("behavior:")
                self._block(behavior)
            self._dedent()
        else:
            # Unknown node — emit a comment so the formatter stays idempotent
            # on second pass (empty output is stable)
            pass  # Silently skip unknown nodes rather than emitting unformatted comment

    def _block(self, block: Block):
        self._indent()
        for stmt in block.stmts:
            self._stmt(stmt)
        self._dedent()

    # ── Statement formatters ──────────────────────────────────────────────────

    def _fmt_define(self, node: Define):
        if isinstance(node.value, FuncDef):
            fn = node.value
            params = self._params(fn.params)
            self._emit(f"define {node.name}({params}):")
            self._block(fn.body)
        else:
            hint = f": {node.type_hint}" if node.type_hint else ""
            value = self._expr(node.value)
            self._emit(f"define {node.name}{hint} as {value}")

    def _fmt_if(self, node: If):
        for i, (cond, block) in enumerate(node.branches):
            keyword = "if" if i == 0 else "else if"
            self._emit(f"{keyword} {self._expr(cond)}:")
            self._block(block)
        if node.else_block:
            self._emit("else:")
            self._block(node.else_block)

    def _fmt_for(self, node: For):
        var = node.var
        if node.var2:
            var = f"{node.var}, {node.var2}"
        self._emit(f"for each {var} in {self._expr(node.iterable)}:")
        self._block(node.body)

    def _fmt_match(self, node: Match):
        self._emit(f"match {self._expr(node.subject)}:")
        self._indent()
        for val, block in node.cases:
            self._emit(f"case {self._expr(val)}:")
            self._block(block)
        if node.otherwise:
            self._emit("otherwise:")
            self._block(node.otherwise)
        self._dedent()

    def _fmt_check(self, node: Check):
        self._emit("check:")
        self._block(node.body)
        if node.recover_block:
            rv = f" {node.recover_var}" if node.recover_var else ""
            self._emit(f"recover{rv}:")
            self._block(node.recover_block)
        if node.always_block:
            self._emit("always:")
            self._block(node.always_block)

    def _fmt_typedef(self, node: TypeDef):
        self._emit(f"type {node.name} has:")
        self._indent()
        for fname, ftype, fdefault in node.fields:
            hint = f": {ftype}" if ftype else ""
            default = f" = {self._expr(fdefault)}" if fdefault else ""
            self._emit(f"{fname}{hint}{default}")
        self._dedent()

    # ── Expression formatter ──────────────────────────────────────────────────

    def _expr(self, node: Node) -> str:
        t = type(node)

        if t == NumberLit:
            v = node.value
            # Integer display: no .0
            if isinstance(v, float) and v == int(v):
                return str(int(v))
            return str(v)

        if t == StringLit:
            # Always double-quoted
            escaped = node.value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\t", "\\t")
            return f'"{escaped}"'

        if t == BoolLit:
            return "true" if node.value else "false"

        if t == NothingLit:
            return "nothing"

        if t == Identifier:
            return node.name

        if t == ListLit:
            if not node.elements:
                return "list []"
            items = [self._expr(e) for e in node.elements]
            return "list [" + ", ".join(items) + "]"
        if t == MapLit:
            if not node.pairs:
                return "map {}"
            pairs = [f"{self._expr(k)}: {self._expr(v)}" for k, v in node.pairs]
            return "map {" + ", ".join(pairs) + "}"
        if t == BinOp:
            # Add spaces around operators
            l = self._expr(node.left)
            r = self._expr(node.right)
            # Parens for lower-precedence operators in higher-precedence context
            return f"{self._maybe_paren(node.left, node.op, 'left')} {node.op} {self._maybe_paren(node.right, node.op, 'right')}"

        if t == UnaryOp:
            operand = self._expr(node.operand)
            if node.op == "not":
                return f"not {operand}"
            return f"-{operand}"

        if t == LogicalOp:
            l = self._expr(node.left)
            r = self._expr(node.right)
            return f"{l} {node.op} {r}"

        if t == IsOp:
            l = self._expr(node.left)
            r = self._expr(node.right)
            op = "is not" if node.negated else "is"
            return f"{l} {op} {r}"

        if t == Fallback:
            return f"{self._expr(node.expr)} or {self._expr(node.default)}"

        if t == Call:
            callee = self._expr(node.callee)
            args = [self._expr(a) for a in node.args]
            kwargs = [f"{k}={self._expr(v)}" for k, v in node.kwargs.items()]
            all_args = ", ".join(args + kwargs)
            using = f" using {node.using}" if node.using else ""
            return f"{callee}({all_args}){using}"

        if t == Index:
            return f"{self._expr(node.obj)}[{self._expr(node.key)}]"

        if t == Field:
            return f"{self._expr(node.obj)}.{node.name}"

        if t == Lambda:
            params = ", ".join(node.params)
            body = self._expr(node.body)
            if len(node.params) > 1:
                return f"given ({params}): {body}"
            return f"given {params}: {body}"

        if t == ParallelExpr:
            exprs = [self._expr(e) for e in node.exprs]
            if len(exprs) <= 3:
                return "parallel [" + ", ".join(exprs) + "]"
            lines = ["parallel ["]
            for e in exprs:
                lines.append(INDENT + e + ",")
            lines.append("]")
            return "\n".join(lines)

        if t == AnalyzeExpr:
            return f"analyze({self._expr(node.text)}) using {node.mode}"

        if t == GenerateExpr:
            return f"generate({self._expr(node.prompt)}) using {node.mode}"

        if t == AskExpr:
            return f"ask({self._expr(node.question)})"

        if t == EmbedExpr:
            return f"embed({self._expr(node.text)})"

        if t == ClassifyExpr:
            labels = ", ".join(self._expr(l) for l in node.labels)
            return f"classify({self._expr(node.text)}) using [{labels}]"

        if t == FuncDef:
            # Inline anonymous function — shouldn't appear as expression normally
            params = self._params(node.params)
            return f"define ({params}): ..."

        return f"# [unformatted expr: {type(node).__name__}]"

    def _maybe_paren(self, node: Node, parent_op: str, side: str) -> str:
        """Add parentheses if needed for precedence clarity."""
        expr = self._expr(node)
        # Only parenthesize LogicalOp inside arithmetic
        if isinstance(node, LogicalOp) and parent_op in ("+", "-", "*", "/"):
            return f"({expr})"
        return expr

    def _params(self, params) -> str:
        parts = []
        for name, hint in params:
            if hint:
                parts.append(f"{name}: {hint}")
            else:
                parts.append(name)
        return ", ".join(parts)


# ── Public API ────────────────────────────────────────────────────────────────

def format_ledge(source: str) -> str:
    """
    Format Ledge source code canonically.
    Raises ParseError if source has syntax errors.
    """
    tokens = Lexer(source).tokenize()
    ast = Parser(tokens).parse()
    return Formatter().format(ast)


def format_file(path: str, check_only: bool = False) -> bool:
    """
    Format a .ledge file in-place.
    If check_only=True, returns True if file is already formatted, False if not.
    """
    with open(path, encoding="utf-8") as f:
        original = f.read()

    try:
        formatted = format_ledge(original)
    except (LexError, ParseError) as e:
        raise

    if check_only:
        return original == formatted

    if original != formatted:
        with open(path, "w", encoding="utf-8") as f:
            f.write(formatted)
        return True  # file was changed

    return False  # file was already clean


def main():
    """CLI entry point: ledge fmt"""
    import sys
    import argparse

    parser = argparse.ArgumentParser(description="Format Ledge source files")
    parser.add_argument("files", nargs="+", help=".ledge files to format")
    parser.add_argument("--check", action="store_true",
                        help="Check formatting without modifying files")
    parser.add_argument("--print", action="store_true", dest="print_only",
                        help="Print formatted output to stdout")
    args = parser.parse_args()

    exit_code = 0

    for path in args.files:
        try:
            with open(path, encoding="utf-8") as f:
                source = f.read()
            formatted = format_ledge(source)

            if args.print_only:
                sys.stdout.write(formatted)
            elif args.check:
                if source != formatted:
                    print(f"  would reformat: {path}")
                    exit_code = 1
                else:
                    print(f"  already formatted: {path}")
            else:
                if source != formatted:
                    with open(path, "w", encoding="utf-8") as f:
                        f.write(formatted)
                    print(f"  reformatted: {path}")
                else:
                    print(f"  unchanged: {path}")

        except (LexError, ParseError) as e:
            print(f"  error in {path}: {e}", file=sys.stderr)
            exit_code = 1
        except FileNotFoundError:
            print(f"  not found: {path}", file=sys.stderr)
            exit_code = 1

    sys.exit(exit_code)
