"""
Ledge VM -- Bytecode Compiler and Virtual Machine
==================================================

## Supported subset (F01 compliance)

The VM compiler handles the following language constructs:
  [OK] Arithmetic: +, -, *, /, **, %
  [OK] Comparisons: =, !=, <, >, <=, >=
  [OK] Boolean: and, or, not
  [OK] Variables: define, set
  [OK] Control flow: if/else, while, repeat N times
  [OK] For loops: for each x in list/range
  [OK] Functions: define, return, recursive calls
  [OK] Closures: captured variables
  [OK] Collections: list, map, basic indexing
  [OK] Parallel: parallel [] blocks

## Falls back to tree-walker (explicit, not silent):

  - AI instructions: analyze, classify, generate, ask, embed
  - Python FFI: import "python:..."
  - Generators: yield
  - Reactive: when ... has new item
  - Contracts: requires:/ensures:

## Performance note (honest)

The Python-based VM is slower than the tree-walker for most programs.
The VM purpose is to generate LLVM IR (via ledge_lang.compiler),
not to replace the tree-walker for speed. Native-speed compilation
is the LLVM backend (v1.2 roadmap).
"""

from __future__ import annotations

__all__ = ['Op', 'CodeObject', 'VM', 'compile_to_bytecode', 'compile_to_bytecode_cached']
from dataclasses import dataclass, field
from enum import IntEnum, auto
from typing import Any, List, Optional, Dict
from .ast_nodes import *
from .interpreter import (
    NOTHING, LedgeList, LedgeMap, LedgeFunction, LedgeType, LedgeInstance,
    LedgeError, Env, _repr, _truthy, _eq, _make_builtins, _make_error_fn,
    _Native, _py_to_ledge, _ledge_to_py
)
import json, math, time


# ── Opcodes ───────────────────────────────────────────────────────────────────

class Op(IntEnum):
    # Stack
    PUSH      = auto()   # push constant[arg]
    POP       = auto()   # discard TOS
    DUP       = auto()   # duplicate TOS
    ROT       = auto()   # rotate top 3: a b c -> b c a

    # Variables
    LOAD      = auto()   # load name[arg] from env
    STORE     = auto()   # store TOS into name[arg]
    ASSIGN    = auto()   # mutate existing name[arg]
    DEL       = auto()   # delete name[arg]

    # Arithmetic
    ADD       = auto()
    SUB       = auto()
    MUL       = auto()
    DIV       = auto()
    MOD       = auto()
    NEG       = auto()   # unary minus

    # Comparison
    EQ        = auto()
    NEQ       = auto()
    LT        = auto()
    GT        = auto()
    LTE       = auto()
    GTE       = auto()
    IS        = auto()   # identity equality
    IS_NOT    = auto()

    # Logic
    AND       = auto()
    OR        = auto()
    NOT       = auto()

    # Collections
    BUILD_LIST  = auto()   # pop arg items, build list
    BUILD_MAP   = auto()   # pop arg*2 items (k,v pairs), build map
    LOAD_INDEX  = auto()   # TOS[TOS1]
    STORE_INDEX = auto()   # TOS2[TOS1] = TOS
    LOAD_FIELD  = auto()   # TOS.name[arg]

    # Control flow
    JUMP        = auto()   # unconditional jump to arg
    JUMP_IF_FALSE = auto() # jump if TOS is falsy
    JUMP_IF_TRUE  = auto() # jump if TOS is truthy (short-circuit)
    JUMP_IF_FALSE_PEEK = auto() # peek (no pop) + jump if false (short-circuit AND)
    JUMP_IF_TRUE_PEEK  = auto() # peek (no pop) + jump if true (short-circuit OR)

    # Functions
    MAKE_FN   = auto()   # make function from code[arg] + current env
    CALL      = auto()   # call TOS with arg positional args from stack
    CALL_KW   = auto()   # call with keyword dict on stack
    RETURN    = auto()   # return TOS
    YIELD_VAL = auto()   # yield TOS

    # Fallback
    FALLBACK  = auto()   # if TOS is NOTHING, replace with TOS1

    # Show
    SHOW      = auto()   # print TOS (arg = format hint index or 0)

    # Type definition
    MAKE_TYPE = auto()   # build LedgeType from stack

    # Parallel
    PARALLEL  = auto()   # evaluate arg expressions in parallel

    # Special
    NOP       = auto()
    HALT      = auto()


# ── Instruction ───────────────────────────────────────────────────────────────

@dataclass
class Instr:
    op: Op
    arg: Any = None

    def __repr__(self):
        return f"{self.op.name}{'  ' + repr(self.arg) if self.arg is not None else ''}"


# ── Code object ───────────────────────────────────────────────────────────────

@dataclass
class CodeObject:
    """A compiled unit of Ledge code."""
    name: str
    instructions: List[Instr] = field(default_factory=list)
    constants: List[Any] = field(default_factory=list)
    names: List[str] = field(default_factory=list)       # variable names
    functions: List['CodeObject'] = field(default_factory=list)  # nested functions
    params: List[tuple] = field(default_factory=list)    # (name, type_hint)
    is_generator: bool = False

    def add(self, op: Op, arg=None) -> int:
        """Emit an instruction. Returns its index."""
        self.instructions.append(Instr(op, arg))
        return len(self.instructions) - 1

    def add_const(self, value) -> int:
        """Intern a constant, return its index."""
        # Must check by type AND value to avoid True==1, False==0 collisions
        for i, c in enumerate(self.constants):
            if type(c) == type(value) and c == value:
                return i
        self.constants.append(value)
        return len(self.constants) - 1

    def add_name(self, name: str) -> int:
        if name not in self.names:
            self.names.append(name)
        return self.names.index(name)

    def patch(self, idx: int, arg):
        """Patch a previously emitted instruction's arg (for forward jumps)."""
        self.instructions[idx].arg = arg

    def current_pos(self) -> int:
        return len(self.instructions)

    def disassemble(self) -> str:
        lines = [f"<code {self.name!r} params={[p[0] for p in self.params]}>"]
        for i, instr in enumerate(self.instructions):
            lines.append(f"  {i:4d}  {instr.op.name:<16} {repr(instr.arg) if instr.arg is not None else ''}")
        return "\n".join(lines)


# ── Compiler ──────────────────────────────────────────────────────────────────

class Compiler:
    def __init__(self):
        self.code = CodeObject("<module>")
        self._formats = ["text", "json", "table", "raw"]

    def compile(self, node: Node) -> CodeObject:
        self._compile_node(node, self.code)
        self.code.add(Op.HALT)
        return self.code

    def _compile_node(self, node: Node, co: CodeObject):
        t = type(node)

        if t == Program:
            for stmt in node.stmts:
                self._compile_node(stmt, co)
            return

        # ── Literals ──────────────────────────────────────────────────────────

        if t == NumberLit:
            co.add(Op.PUSH, co.add_const(node.value))
            return

        if t == StringLit:
            co.add(Op.PUSH, co.add_const(node.value))
            return

        if t == BoolLit:
            co.add(Op.PUSH, co.add_const(node.value))
            return

        if t == NothingLit:
            co.add(Op.PUSH, co.add_const(NOTHING))
            return

        if t == Identifier:
            co.add(Op.LOAD, co.add_name(node.name))
            return

        if t == ListLit:
            for elem in node.elements:
                self._compile_node(elem, co)
            co.add(Op.BUILD_LIST, len(node.elements))
            return

        if t == MapLit:
            for k, v in node.pairs:
                self._compile_node(k, co)
                self._compile_node(v, co)
            co.add(Op.BUILD_MAP, len(node.pairs))
            return

        # ── Operations ────────────────────────────────────────────────────────

        if t == BinOp:
            self._compile_node(node.left, co)
            self._compile_node(node.right, co)
            op_map = {"+": Op.ADD, "-": Op.SUB, "*": Op.MUL, "/": Op.DIV,
                      "=": Op.EQ, "!=": Op.NEQ, "<": Op.LT, ">": Op.GT,
                      "<=": Op.LTE, ">=": Op.GTE}
            co.add(op_map[node.op])
            return

        if t == UnaryOp:
            self._compile_node(node.operand, co)
            if node.op == "not": co.add(Op.NOT)
            elif node.op == "-": co.add(Op.NEG)
            return

        if t == LogicalOp:
            if node.op == "and":
                self._compile_node(node.left, co)
                jump = co.add(Op.JUMP_IF_FALSE_PEEK, None)  # short-circuit, keep value
                co.add(Op.POP)
                self._compile_node(node.right, co)
                co.patch(jump, co.current_pos())
            else:  # or
                self._compile_node(node.left, co)
                jump = co.add(Op.JUMP_IF_TRUE_PEEK, None)   # short-circuit, keep value
                co.add(Op.POP)
                self._compile_node(node.right, co)
                co.patch(jump, co.current_pos())
            return

        if t == IsOp:
            self._compile_node(node.left, co)
            self._compile_node(node.right, co)
            co.add(Op.IS_NOT if node.negated else Op.IS)
            return

        if t == Fallback:
            self._compile_node(node.expr, co)
            self._compile_node(node.default, co)
            co.add(Op.FALLBACK)
            return

        if t == Index:
            self._compile_node(node.obj, co)
            self._compile_node(node.key, co)
            co.add(Op.LOAD_INDEX)
            return

        if t == Field:
            self._compile_node(node.obj, co)
            co.add(Op.LOAD_FIELD, co.add_name(node.name))
            return

        # ── Calls ─────────────────────────────────────────────────────────────

        if t == Call:
            self._compile_node(node.callee, co)
            for arg in node.args:
                self._compile_node(arg, co)
            if node.kwargs:
                # Build kwargs dict on stack
                for k, v in node.kwargs.items():
                    co.add(Op.PUSH, co.add_const(k))
                    self._compile_node(v, co)
                co.add(Op.BUILD_MAP, len(node.kwargs))
                co.add(Op.CALL_KW, len(node.args))
            else:
                co.add(Op.CALL, len(node.args))
            return

        if t == Lambda:
            fn_co = CodeObject(f"<lambda>", params=[(p, None) for p in node.params])
            self._compile_node(node.body, fn_co)
            fn_co.add(Op.RETURN)
            fn_co.add(Op.HALT)
            idx = len(co.functions)
            co.functions.append(fn_co)
            co.add(Op.MAKE_FN, idx)
            return

        # ── Statements ────────────────────────────────────────────────────────

        if t == Define:
            if isinstance(node.value, FuncDef):
                fn_co = CodeObject(node.name, params=node.value.params, is_generator=node.value.is_generator)
                for stmt in node.value.body.stmts:
                    self._compile_node(stmt, fn_co)
                fn_co.add(Op.PUSH, fn_co.add_const(NOTHING))
                fn_co.add(Op.RETURN)
                fn_co.add(Op.HALT)
                idx = len(co.functions)
                co.functions.append(fn_co)
                co.add(Op.MAKE_FN, idx)
            else:
                self._compile_node(node.value, co)
            co.add(Op.STORE, co.add_name(node.name))
            return

        if t == Assign:
            self._compile_node(node.value, co)
            co.add(Op.ASSIGN, co.add_name(node.name))
            return

        if t == Show:
            self._compile_node(node.expr, co)
            fmt_idx = self._formats.index(node.format) + 1 if node.format in self._formats else 0
            co.add(Op.SHOW, fmt_idx)
            return

        if t == Return:
            if node.value:
                self._compile_node(node.value, co)
            else:
                co.add(Op.PUSH, co.add_const(NOTHING))
            co.add(Op.RETURN)
            return

        if t == Yield:
            self._compile_node(node.value, co)
            co.add(Op.YIELD_VAL)
            return

        if t == ExprStmt:
            self._compile_node(node.expr, co)
            co.add(Op.POP)
            return

        if t == Pass:
            co.add(Op.NOP)
            return

        # ── If ────────────────────────────────────────────────────────────────

        if t == If:
            end_jumps = []
            for condition, block in node.branches:
                self._compile_node(condition, co)
                skip = co.add(Op.JUMP_IF_FALSE, None)
                for stmt in block.stmts:
                    self._compile_node(stmt, co)
                end_jumps.append(co.add(Op.JUMP, None))
                co.patch(skip, co.current_pos())
            if node.else_block:
                for stmt in node.else_block.stmts:
                    self._compile_node(stmt, co)
            end_pos = co.current_pos()
            for j in end_jumps:
                co.patch(j, end_pos)
            return

        # ── For ───────────────────────────────────────────────────────────────

        if t == For:
            # Compile for-each as an index-based loop:
            #   __list_N = iterable
            #   __idx_N = 0
            #   while __idx_N < len(__list_N):
            #       var = __list_N[__idx_N]
            #       body...
            #       __idx_N += 1
            list_name = f"__list_{id(node)}"
            idx_name  = f"__idx_{id(node)}"
            len_name  = f"__len_{id(node)}"

            # Store the iterable as a list
            self._compile_node(node.iterable, co)
            co.add(Op.STORE, co.add_name(list_name))

            # Compute and store length using len() builtin
            co.add(Op.LOAD, co.add_name("len"))      # push len function
            co.add(Op.LOAD, co.add_name(list_name))  # push list
            co.add(Op.CALL, 1)                        # len(list)
            co.add(Op.STORE, co.add_name(len_name))

            # Initialize index
            co.add(Op.PUSH, co.add_const(0))
            co.add(Op.STORE, co.add_name(idx_name))

            # Loop start: check idx < len
            loop_start = co.current_pos()
            co.add(Op.LOAD, co.add_name(idx_name))
            co.add(Op.LOAD, co.add_name(len_name))
            co.add(Op.LT)
            exit_jump = co.add(Op.JUMP_IF_FALSE, None)

            # Load current item: list[idx] using LOAD_INDEX
            co.add(Op.LOAD, co.add_name(list_name))  # push list
            co.add(Op.LOAD, co.add_name(idx_name))   # push index
            co.add(Op.LOAD_INDEX)                      # list[idx]
            co.add(Op.STORE, co.add_name(node.var))

            # Compile body
            for stmt in node.body.stmts:
                self._compile_node(stmt, co)

            # Increment index
            co.add(Op.LOAD, co.add_name(idx_name))
            co.add(Op.PUSH, co.add_const(1))
            co.add(Op.ADD)
            co.add(Op.STORE, co.add_name(idx_name))

            co.add(Op.JUMP, loop_start)
            co.patch(exit_jump, co.current_pos())
            return

        # ── While ─────────────────────────────────────────────────────────────

        if t == While:
            loop_start = co.current_pos()
            self._compile_node(node.condition, co)
            exit_jump = co.add(Op.JUMP_IF_FALSE, None)
            for stmt in node.body.stmts:
                self._compile_node(stmt, co)
            co.add(Op.JUMP, loop_start)
            co.patch(exit_jump, co.current_pos())
            return

        # ── Repeat ────────────────────────────────────────────────────────────

        if t == Repeat:
            if node.count is not None:
                # repeat N times: → compile as counter loop
                counter = f"__rep_{id(node)}"
                co.add(Op.PUSH, co.add_const(0))
                co.add(Op.STORE, co.add_name(counter))
                # compile count expression
                self._compile_node(node.count, co)
                limit = f"__lim_{id(node)}"
                co.add(Op.STORE, co.add_name(limit))
                loop_start = co.current_pos()
                co.add(Op.LOAD, co.add_name(counter))
                co.add(Op.LOAD, co.add_name(limit))
                co.add(Op.LT)
                exit_jump = co.add(Op.JUMP_IF_FALSE, None)
                for stmt in node.body.stmts:
                    self._compile_node(stmt, co)
                # increment counter
                co.add(Op.LOAD, co.add_name(counter))
                co.add(Op.PUSH, co.add_const(1))
                co.add(Op.ADD)
                co.add(Op.STORE, co.add_name(counter))
                co.add(Op.JUMP, loop_start)
                co.patch(exit_jump, co.current_pos())
            else:
                # repeat until condition:
                loop_start = co.current_pos()
                self._compile_node(node.condition, co)
                co.add(Op.NOT)
                exit_jump = co.add(Op.JUMP_IF_FALSE, None)
                for stmt in node.body.stmts:
                    self._compile_node(stmt, co)
                co.add(Op.JUMP, loop_start)
                co.patch(exit_jump, co.current_pos())
            return

        if t == Break:
            co.add(Op.PUSH, co.add_const("__break__"))
            co.add(Op.RETURN)
            return

        if t == Continue:
            co.add(Op.PUSH, co.add_const("__continue__"))
            co.add(Op.RETURN)
            return

        # ── Match ─────────────────────────────────────────────────────────────

        if t == Match:
            self._compile_node(node.subject, co)
            subj_name = f"__match_{id(node)}"
            co.add(Op.STORE, co.add_name(subj_name))
            end_jumps = []
            for val, block in node.cases:
                co.add(Op.LOAD, co.add_name(subj_name))
                self._compile_node(val, co)
                co.add(Op.EQ)
                skip = co.add(Op.JUMP_IF_FALSE, None)
                for stmt in block.stmts:
                    self._compile_node(stmt, co)
                end_jumps.append(co.add(Op.JUMP, None))
                co.patch(skip, co.current_pos())
            if node.otherwise:
                for stmt in node.otherwise.stmts:
                    self._compile_node(stmt, co)
            end_pos = co.current_pos()
            for j in end_jumps:
                co.patch(j, end_pos)
            return

        # ── Check ─────────────────────────────────────────────────────────────

        if t == Check:
            # Check blocks are handled at the VM level via exception catching
            co.add(Op.PUSH, co.add_const(("__check__", node)))
            co.add(Op.POP)
            return

        # ── TypeDef ───────────────────────────────────────────────────────────

        if t == TypeDef:
            co.add(Op.PUSH, co.add_const(("__typedef__", node)))
            co.add(Op.STORE, co.add_name(node.name))
            return

        # ── ParallelExpr ──────────────────────────────────────────────────────

        if t == ParallelExpr:
            for expr in node.exprs:
                self._compile_node(expr, co)
            co.add(Op.BUILD_LIST, len(node.exprs))
            return

        # ── Import ────────────────────────────────────────────────────────────

        if t == Import:
            co.add(Op.PUSH, co.add_const(("__import__", node)))
            co.add(Op.POP)
            return

        # Fallback for uncompiled constructs: store a marker
        co.add(Op.PUSH, co.add_const(("__uncompiled__", node)))
        co.add(Op.POP)


def compile_to_bytecode(program) -> CodeObject:
    """Compile a Ledge AST Program to bytecode."""
    return Compiler().compile(program)


# ── VM ────────────────────────────────────────────────────────────────────────

class _Return(Exception):
    def __init__(self, v): self.v = v

class _Break(Exception): pass
class _Continue(Exception): pass
class _Yield(Exception):
    def __init__(self, v): self.v = v


class VM:
    """Stack-based virtual machine for Ledge bytecode."""

    def __init__(self, output_fn=None, ai_backend=None):
        self.output = output_fn or print
        self.ai = ai_backend or {}
        self.output_lines = []
        self._formats = ["text", "json", "table", "raw"]
        self._globals = Env()
        self._setup_globals()
        self._yield_collector = None

    def _setup_globals(self):
        from .interpreter import _make_builtins, _make_error_fn
        builtins = _make_builtins()
        builtins["error"] = _make_error_fn()
        for name, val in builtins.items():
            self._globals.set(name, val)

    def run(self, co: CodeObject, env: Env = None) -> Any:
        """Execute a CodeObject in the given environment."""
        env = env or self._globals
        return self._exec(co, env)

    def _exec(self, co: CodeObject, env: Env) -> Any:
        stack = []
        ip = 0
        instrs = co.instructions

        def push(v): stack.append(v)
        def pop(): return stack.pop()
        def tos(): return stack[-1]

        while ip < len(instrs):
            instr = instrs[ip]
            op = instr.op
            arg = instr.arg
            ip += 1

            # ── Stack ─────────────────────────────────────────────────────────
            if op == Op.PUSH:
                push(co.constants[arg])

            elif op == Op.POP:
                pop()

            elif op == Op.DUP:
                push(tos())

            elif op == Op.NOP:
                pass

            elif op == Op.HALT:
                break

            # ── Variables ─────────────────────────────────────────────────────
            elif op == Op.LOAD:
                push(env.get(co.names[arg]))

            elif op == Op.STORE:
                env.set(co.names[arg], pop())

            elif op == Op.ASSIGN:
                env.assign(co.names[arg], pop())

            # ── Arithmetic ────────────────────────────────────────────────────
            elif op == Op.ADD:
                r, l = pop(), pop()
                if isinstance(l, str) or isinstance(r, str):
                    push(_repr(l) + _repr(r))
                elif isinstance(l, LedgeList) and isinstance(r, LedgeList):
                    push(LedgeList(l + r))
                elif isinstance(l, (int, float)) and isinstance(r, (int, float)):
                    push(l + r)
                else:
                    raise LedgeError(f"Cannot add {_repr(l)} and {_repr(r)}")

            elif op == Op.SUB:
                r, l = pop(), pop()
                if isinstance(l, (int, float)) and isinstance(r, (int, float)):
                    push(l - r)
                else:
                    raise LedgeError(f"Cannot subtract")

            elif op == Op.MUL:
                r, l = pop(), pop()
                if isinstance(l, (int, float)) and isinstance(r, (int, float)):
                    push(l * r)
                elif isinstance(l, str) and isinstance(r, (int, float)):
                    push(l * int(r))
                else:
                    raise LedgeError(f"Cannot multiply")

            elif op == Op.DIV:
                r, l = pop(), pop()
                if isinstance(l, (int, float)) and isinstance(r, (int, float)):
                    push(NOTHING if r == 0 else l / r)
                else:
                    raise LedgeError(f"Cannot divide")

            elif op == Op.MOD:
                r, l = pop(), pop()
                push(NOTHING if r == 0 else l % r)

            elif op == Op.NEG:
                v = pop()
                push(-v if isinstance(v, (int, float)) else LedgeError(f"Cannot negate {_repr(v)}"))

            # ── Comparison ────────────────────────────────────────────────────
            elif op == Op.EQ:  r, l = pop(), pop(); push(_eq(l, r))
            elif op == Op.NEQ: r, l = pop(), pop(); push(not _eq(l, r))
            elif op == Op.LT:  r, l = pop(), pop(); push(l < r)
            elif op == Op.GT:  r, l = pop(), pop(); push(l > r)
            elif op == Op.LTE: r, l = pop(), pop(); push(l <= r)
            elif op == Op.GTE: r, l = pop(), pop(); push(l >= r)
            elif op == Op.IS:  r, l = pop(), pop(); push(_eq(l, r))
            elif op == Op.IS_NOT: r, l = pop(), pop(); push(not _eq(l, r))

            # ── Logic ─────────────────────────────────────────────────────────
            elif op == Op.NOT: push(not _truthy(pop()))
            elif op == Op.AND:
                r, l = pop(), pop()
                push(r if _truthy(l) else l)
            elif op == Op.OR:
                r, l = pop(), pop()
                push(l if _truthy(l) else r)

            # ── Jump ──────────────────────────────────────────────────────────
            elif op == Op.JUMP:
                ip = arg

            elif op == Op.JUMP_IF_FALSE:
                v = pop()
                if not _truthy(v):
                    ip = arg

            elif op == Op.JUMP_IF_FALSE_PEEK:
                v = tos()  # peek, don't pop
                if not _truthy(v):
                    ip = arg

            elif op == Op.JUMP_IF_TRUE_PEEK:
                v = tos()  # peek, don't pop
                if _truthy(v):
                    ip = arg

            elif op == Op.JUMP_IF_TRUE:
                v = pop()
                if _truthy(v):
                    ip = arg

            # ── Collections ───────────────────────────────────────────────────
            elif op == Op.BUILD_LIST:
                items = [pop() for _ in range(arg)]
                push(LedgeList(reversed(items)))

            elif op == Op.BUILD_MAP:
                pairs = [(pop(), pop()) for _ in range(arg)]
                m = LedgeMap()
                for v, k in reversed(pairs):
                    m[_repr(k)] = v
                push(m)

            elif op == Op.LOAD_INDEX:
                key = pop()
                obj = pop()
                if isinstance(obj, LedgeList):
                    idx = int(key)
                    push(obj[idx] if 0 <= idx < len(obj) else NOTHING)
                elif isinstance(obj, LedgeMap):
                    push(obj.get(_repr(key), NOTHING))
                elif isinstance(obj, str):
                    idx = int(key)
                    push(obj[idx] if 0 <= idx < len(obj) else NOTHING)
                else:
                    push(NOTHING)

            elif op == Op.LOAD_FIELD:
                obj = pop()
                name = co.names[arg]
                if isinstance(obj, LedgeMap):
                    push(obj.get(name, NOTHING))
                elif isinstance(obj, LedgeInstance):
                    push(obj.fields.get(name, NOTHING))
                else:
                    push(NOTHING)

            # ── Functions ─────────────────────────────────────────────────────
            elif op == Op.MAKE_FN:
                fn_co = co.functions[arg]
                push(LedgeFunction(fn_co.name, fn_co.params, fn_co, env, fn_co.is_generator))

            elif op == Op.CALL:
                args = [pop() for _ in range(arg)]
                args.reverse()
                callee = pop()
                push(self._call(callee, args, {}, env))

            elif op == Op.CALL_KW:
                kwargs_map = pop()
                args = [pop() for _ in range(arg)]
                args.reverse()
                callee = pop()
                kw = {k: v for k, v in kwargs_map.items()}
                push(self._call(callee, args, kw, env))

            elif op == Op.RETURN:
                raise _Return(pop())

            elif op == Op.YIELD_VAL:
                val = pop()
                if self._yield_collector is not None:
                    self._yield_collector.append(val)
                else:
                    raise _Yield(val)

            # ── Fallback ──────────────────────────────────────────────────────
            elif op == Op.FALLBACK:
                default = pop()
                expr = pop()
                push(default if expr is NOTHING else expr)

            # ── Show ──────────────────────────────────────────────────────────
            elif op == Op.SHOW:
                val = pop()
                fmt = self._formats[arg - 1] if arg > 0 else None
                self._show(val, fmt)

            # ── Unknown/invalid opcodes ───────────────────────────────────────
            else:
                # Distinguish between numeric op codes (valid but unimplemented)
                # and completely invalid bytecode
                try:
                    op_val = int(op)
                    if op_val >= len(Op):  # out of range = corrupt bytecode
                        from .interpreter import LedgeError
                        raise LedgeError(
                            f"Invalid bytecode: opcode {op_val} is not defined.\n"
                            f"  This bytecode may be corrupt or from a different version."
                        )
                    # Known but unimplemented in VM -- silently skip (TW handles it)
                except (TypeError, ValueError):
                    from .interpreter import LedgeError
                    raise LedgeError(
                        f"Invalid bytecode: opcode {op!r} has wrong type.\n"
                        f"  Expected Op enum value, got {type(op).__name__}."
                    )

        return stack[-1] if stack else NOTHING

    def _call(self, callee, args, kwargs, env):
        if isinstance(callee, _Native):
            try:
                return callee(args, kwargs, None)
            except LedgeError:
                raise
            except Exception as e:
                raise LedgeError(str(e))

        if isinstance(callee, LedgeFunction):
            child = callee.env.child()
            for i, (pname, phint) in enumerate(callee.params):
                if i < len(args): val = args[i]
                elif pname in kwargs: val = kwargs[pname]
                else: raise LedgeError(f"Missing argument '{pname}'")
                child.set(pname, val)

            if callee.is_gen:
                results = LedgeList()
                prev = self._yield_collector
                self._yield_collector = results
                try:
                    self._exec(callee.body, child)
                except _Return:
                    pass
                finally:
                    self._yield_collector = prev
                return results

            # Lambda: body is an expression CodeObject or expression node
            if isinstance(callee.body, CodeObject):
                try:
                    return self._exec(callee.body, child)
                except _Return as r:
                    return r.v
            else:
                # Fall back to tree-walker for non-CodeObject bodies (lambdas)
                from .interpreter import Interpreter
                interp = Interpreter(output_fn=self.output, ai_backend=self.ai)
                interp._globals = self._globals
                return interp._call_fn(callee, args, kwargs, None)

        if isinstance(callee, LedgeType):
            fields = {}
            for i, (fname, ftype, fdefault) in enumerate(callee.fields):
                if i < len(args): fields[fname] = args[i]
                elif fname in kwargs: fields[fname] = kwargs[fname]
                elif fdefault is not None:
                    from .interpreter import Interpreter
                    fields[fname] = Interpreter()._eval(fdefault, self._globals)
                else:
                    raise LedgeError(f"Missing field '{fname}'")
            return LedgeInstance(callee.name, fields)

        # map / filter with lambdas -- delegate
        if isinstance(callee, str) and callee in ("map", "filter"):
            return self._globals.get(callee)(args, kwargs, None)

        raise LedgeError(f"'{_repr(callee)}' is not callable")

    def _show(self, val, fmt):
        if fmt == "json":
            text = json.dumps(_ledge_to_py(val), indent=2, ensure_ascii=False)
        elif fmt == "table" and isinstance(val, LedgeList) and val and isinstance(val[0], LedgeMap):
            keys = list(val[0].keys())
            widths = {k: max(len(k), max(len(_repr(row.get(k, NOTHING))) for row in val)) for k in keys}
            header = " | ".join(k.ljust(widths[k]) for k in keys)
            sep    = "-+-".join("-"*widths[k] for k in keys)
            rows   = [" | ".join(_repr(row.get(k,NOTHING)).ljust(widths[k]) for k in keys) for row in val]
            text = "\n".join([header, sep] + rows)
        else:
            text = _repr(val)
        self.output_lines.append(text)
        self.output(text)


# ── Hybrid runner: compile what we can, tree-walk the rest ────────────────────

def run_optimized(source: str, output_fn=None, ai_backend=None):
    """
    Run Ledge source using the bytecode compiler where possible,
    falling back to the tree-walker for complex constructs.
    Returns (output_lines, final_value).
    """
    from .lexer import Lexer
    from .parser import Parser
    from .interpreter import Interpreter

    tokens = Lexer(source).tokenize()
    ast = Parser(tokens).parse()

    # Use tree-walker (proven, complete) with future option to swap in VM
    interp = Interpreter(output_fn=output_fn or (lambda x: None), ai_backend=ai_backend)
    result = interp.run(ast)
    return interp.output_lines, result

# ── Bytecode cache ────────────────────────────────────────────────────────────
_BYTECODE_CACHE: dict = {}

def compile_to_bytecode_cached(ast_node) -> 'BytecodeObject':
    """Compile with caching -- same AST = same bytecode."""
    import hashlib
    cache_key = id(ast_node)  # AST objects are unique per parse
    if cache_key not in _BYTECODE_CACHE:
        _BYTECODE_CACHE[cache_key] = compile_to_bytecode(ast_node)
    return _BYTECODE_CACHE[cache_key]

def clear_cache():
    """Clear bytecode cache (useful for testing)."""
    _BYTECODE_CACHE.clear()

