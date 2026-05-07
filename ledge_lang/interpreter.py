"""
Ledge Language — Interpreter v1.0
Tree-walking evaluator with AI-native types.

Architecture: imports from core_types.py to avoid circular dependencies.
ai_types.py also imports from core_types.py — no circular dependency exists.
"""

import math, time, json, re, threading, concurrent.futures
from .ast_nodes import *
from .core_types import (
    NOTHING, LedgeList, LedgeMap, LedgeLazyGenerator,
    LedgeFunction, LedgeType, LedgeInstance, _Native,
    PythonModule, PythonObject,
    _repr, _truthy, _eq, _type_of, _check_type_compat,
    _py_to_ledge, _ledge_to_py,
    LedgeError, _Return, _Break, _Continue, _Yield, Env
)
_HAS_AI_TYPES = False  # set lazily in _setup_globals


# ── Runtime values ────────────────────────────────────────────────────────────




class LedgeLazyGenerator:
    """
    Lazy generator — values are produced on demand.
    Fixes the critical v0.1 bug where infinite generators would hang.
    Supports: iteration, indexing, slicing, len (forces evaluation up to n).
    """
    def __init__(self, fn, env, interp):
        self._fn = fn       # LedgeFunction
        self._env = env
        self._interp = interp
        self._cache = []
        self._exhausted = False
        self._gen = None
        self._lock = threading.Lock()

    def _ensure_gen(self):
        if self._gen is None:
            self._gen = self._interp._make_python_gen(self._fn, self._env)

    def _advance_to(self, n):
        """Advance generator until we have n items cached."""
        self._ensure_gen()
        while len(self._cache) < n and not self._exhausted:
            try:
                val = next(self._gen)
                self._cache.append(val)
            except StopIteration:
                self._exhausted = True
                break

    def collect(self):
        """Force full evaluation — returns LedgeList."""
        self._ensure_gen()
        while not self._exhausted:
            try:
                self._cache.append(next(self._gen))
            except StopIteration:
                self._exhausted = True
        return LedgeList(self._cache)

    def __iter__(self):
        i = 0
        while True:
            self._advance_to(i + 1)
            if i >= len(self._cache):
                break
            yield self._cache[i]
            i += 1

    def __len__(self):
        return len(self.collect())

    def __getitem__(self, idx):
        if isinstance(idx, int):
            self._advance_to(idx + 1)
            if idx < len(self._cache):
                return self._cache[idx]
            return NOTHING
        return NOTHING

    def __repr__(self):
        return f"<generator>"






class _Native:
    def __init__(self, name, fn): self.name, self.fn = name, fn
    def __call__(self, args, kw, using): return self.fn(args, kw, using)
    def __repr__(self): return f"<builtin {self.name}>"

def _n(name, fn): return _Native(name, fn)

def _num_cast(v):
    if isinstance(v, bool): return NOTHING
    if isinstance(v, (int, float)): return v
    if isinstance(v, str):
        try:
            return float(v) if '.' in v else int(v)
        except (ValueError, TypeError):
            return NOTHING
    return NOTHING

def _bi_random(a, k, u):
    import random
    if not a: return random.random()
    if len(a)==2: return random.randint(int(a[0]), int(a[1]))
    if isinstance(a[0], (LedgeList, LedgeLazyGenerator)):
        lst = list(a[0])
        return random.choice(lst) if lst else NOTHING
    return random.random()

def _bi_json_parse(a, k, u):
    if not a: return NOTHING
    try:
        return _py_to_ledge(json.loads(a[0]))
    except Exception:
        return NOTHING

def _bi_assert(a, k, u):
    if not _truthy(a[0]):
        if len(a) > 1:
            raise LedgeError(f"Assertion failed: {_repr(a[1])}")
        raise LedgeError("Assertion failed. Use assert(condition, message) to explain what went wrong.")
    return True

def _make_error_fn():
    def fn(a, k, u): raise LedgeError(_repr(a[0]) if a else "An error occurred")
    return _n("error", fn)

def _coerce_list(v):
    """Convert lazy generator to list for operations that need all elements."""
    if isinstance(v, LedgeLazyGenerator): return v.collect()
    return v

def _make_builtins():
    def bi_len(a,k,u):
        v = _coerce_list(a[0])
        if isinstance(v, (str, list, dict)): return len(v)
        return 0
    
    def bi_sort(a,k,u):
        lst = list(_coerce_list(a[0]))
        reverse = _truthy(k.get("reverse", False))
        key_fn = k.get("by", None)
        if key_fn and isinstance(key_fn, (LedgeFunction, _Native)):
            # Will be handled by interpreter for key function
            pass
        try:
            return LedgeList(sorted(lst, reverse=reverse))
        except TypeError:
            return LedgeList(sorted(lst, key=_repr, reverse=reverse))
    
    def bi_range(a,k,u):
        if len(a)==1: return LedgeList(range(int(a[0])))
        if len(a)==2: return LedgeList(range(int(a[0]),int(a[1])))
        return LedgeList(range(int(a[0]),int(a[1]),int(a[2])))
    
    def bi_sum(a,k,u):
        lst = _coerce_list(a[0])
        return sum(x for x in lst if isinstance(x,(int,float)) and not isinstance(x,bool))
    
    def bi_max(a,k,u):
        if isinstance(a[0], (LedgeList, LedgeLazyGenerator)):
            lst = list(_coerce_list(a[0]))
            return max(lst) if lst else NOTHING
        return max(a)
    
    def bi_min(a,k,u):
        if isinstance(a[0], (LedgeList, LedgeLazyGenerator)):
            lst = list(_coerce_list(a[0]))
            return min(lst) if lst else NOTHING
        return min(a)
    
    def bi_collect(a,k,u):
        """Force a lazy generator to a list."""
        v = a[0]
        if isinstance(v, LedgeLazyGenerator): return v.collect()
        if isinstance(v, LedgeList): return v
        return LedgeList([v])
    
    def bi_first(a,k,u):
        v = a[0]
        n = int(a[1]) if len(a)>1 else 1
        if isinstance(v, LedgeLazyGenerator):
            result = []
            for i, x in enumerate(v):
                if i >= n: break
                result.append(x)
            return LedgeList(result) if n > 1 else (result[0] if result else NOTHING)
        lst = list(v)
        if n == 1: return lst[0] if lst else NOTHING
        return LedgeList(lst[:n])
    
    def bi_take_while(a,k,u):
        lst, fn = a[0], a[1]
        result = LedgeList()
        for x in lst:
            if not _truthy(fn([x], {}, None)): break
            result.append(x)
        return result
    
    def bi_drop_while(a,k,u):
        lst, fn = a[0], a[1]
        result = LedgeList()
        dropping = True
        for x in _coerce_list(lst):
            if dropping and _truthy(fn([x], {}, None)): continue
            dropping = False
            result.append(x)
        return result

    return {
        "len": _n("len", bi_len),
        "type": _n("type", lambda a,k,u: _type_of(a[0])),
        "number": _n("number", lambda a,k,u: (_num_cast(a[0]))),
        "text":  _n("text",  lambda a,k,u: _repr(a[0])),
        "truth": _n("truth", lambda a,k,u: _truthy(a[0])),
        "list":  _n("list",  lambda a,k,u: LedgeList() if not a else (_coerce_list(a[0]) if isinstance(a[0],(LedgeList,LedgeLazyGenerator)) else LedgeList(list(a[0]) if hasattr(a[0],'__iter__') and not isinstance(a[0],str) else [a[0]]))),
        "range": _n("range", bi_range),
        "append": _n("append", lambda a,k,u: LedgeList(list(_coerce_list(a[0])) + [a[1]])),
        "prepend": _n("prepend", lambda a,k,u: LedgeList([a[1]] + list(_coerce_list(a[0])))),
        "remove": _n("remove", lambda a,k,u: LedgeList(x for x in _coerce_list(a[0]) if not _eq(x,a[1]))),
        "slice":  _n("slice",  lambda a,k,u: LedgeList(_coerce_list(a[0])[int(a[1]) if len(a)>1 else 0:int(a[2]) if len(a)>2 else None])),
        "merge":  _n("merge",  lambda a,k,u: LedgeList(list(_coerce_list(a[0]))+list(_coerce_list(a[1]))) if isinstance(a[0],(LedgeList,LedgeLazyGenerator)) else LedgeMap({**a[0],**a[1]})),
        "join":   _n("join",   lambda a,k,u: (a[1] if len(a)>1 else "").join(_repr(x) for x in _coerce_list(a[0]))),
        "sum":    _n("sum",    bi_sum),
        "max":    _n("max",    bi_max),
        "min":    _n("min",    bi_min),
        "sort":   _n("sort",   bi_sort),
        "reverse": _n("reverse", lambda a,k,u: LedgeList(reversed(list(_coerce_list(a[0]))))),
        "collect": _n("collect", bi_collect),
        "first":   _n("first",  bi_first),
        "take_while": _n("take_while", bi_take_while),
        "drop_while": _n("drop_while", bi_drop_while),
        "zip": _n("zip", lambda a,k,u: LedgeList(LedgeList([x,y]) for x,y in zip(_coerce_list(a[0]),_coerce_list(a[1])))),
        "flatten": _n("flatten", lambda a,k,u: LedgeList(y for x in _coerce_list(a[0]) for y in (list(_coerce_list(x)) if isinstance(x,(LedgeList,LedgeLazyGenerator)) else [x]))),
        "has":    _n("has",    lambda a,k,u: (a[1] in a[0]) if isinstance(a[0],(LedgeMap,LedgeList,str)) else False),
        "keys":   _n("keys",   lambda a,k,u: LedgeList(a[0].keys()) if isinstance(a[0],LedgeMap) else NOTHING),
        "values": _n("values", lambda a,k,u: LedgeList(a[0].values()) if isinstance(a[0],LedgeMap) else NOTHING),
        "split":  _n("split",  lambda a,k,u: LedgeList(a[0].split(a[1] if len(a)>1 else " "))),
        "trim":   _n("trim",   lambda a,k,u: a[0].strip()),
        "upper":  _n("upper",  lambda a,k,u: a[0].upper()),
        "lower":  _n("lower",  lambda a,k,u: a[0].lower()),
        "replace": _n("replace", lambda a,k,u: a[0].replace(a[1],a[2])),
        "contains":    _n("contains",    lambda a,k,u: a[1] in a[0] if isinstance(a[0],str) else False),
        "starts_with": _n("starts_with", lambda a,k,u: a[0].startswith(a[1]) if isinstance(a[0],str) else False),
        "ends_with":   _n("ends_with",   lambda a,k,u: a[0].endswith(a[1]) if isinstance(a[0],str) else False),
        "pad_left":  _n("pad_left",  lambda a,k,u: _repr(a[0]).rjust(int(a[1]), a[2] if len(a)>2 else " ")),
        "pad_right": _n("pad_right", lambda a,k,u: _repr(a[0]).ljust(int(a[1]), a[2] if len(a)>2 else " ")),
        "divide":  _n("divide",  lambda a,k,u: NOTHING if a[1]==0 else a[0]/a[1]),
        "modulo":  _n("modulo",  lambda a,k,u: NOTHING if a[1]==0 else a[0]%a[1]),
        "power":   _n("power",   lambda a,k,u: a[0]**a[1]),
        "sqrt":    _n("sqrt",    lambda a,k,u: math.sqrt(a[0]) if a[0]>=0 else NOTHING),
        "log":     _n("log",     lambda a,k,u: math.log(a[0], a[1] if len(a)>1 else math.e) if a[0]>0 else NOTHING),
        "abs":     _n("abs",     lambda a,k,u: abs(a[0])),
        "round":   _n("round",   lambda a,k,u: round(a[0], int(a[1]) if len(a)>1 else 0)),
        "floor":   _n("floor",   lambda a,k,u: math.floor(a[0])),
        "ceil":    _n("ceil",    lambda a,k,u: math.ceil(a[0])),
        "clamp":   _n("clamp",   lambda a,k,u: max(a[1], min(a[2], a[0]))),
        "pi":      _n("pi",      lambda a,k,u: math.pi),
        "sin":     _n("sin",     lambda a,k,u: math.sin(a[0])),
        "cos":     _n("cos",     lambda a,k,u: math.cos(a[0])),
        "tan":     _n("tan",     lambda a,k,u: math.tan(a[0])),
        "random":  _n("random",  _bi_random),
        "now":     _n("now",     lambda a,k,u: time.time()),
        "json_parse":    _n("json_parse",    _bi_json_parse),
        "json_stringify": _n("json_stringify", lambda a,k,u: json.dumps(_ledge_to_py(a[0]), ensure_ascii=False)),
        "assert":  _n("assert",  _bi_assert),
        "make":    _n("make",    lambda a,k,u: LedgeMap(k)),
        "map":     _n("map",     lambda a,k,u: a[0]),  # special-cased in _call
        "filter":  _n("filter",  lambda a,k,u: a[0]),  # special-cased in _call
        "reduce":  _n("reduce",  lambda a,k,u: a[0]),  # special-cased in _call
        "zip_with": _n("zip_with", lambda a,k,u: a[0]), # special-cased
        "count":   _n("count",   lambda a,k,u: len(list(_coerce_list(a[0])))),
        "group_by":  _n("group_by",  lambda a,k,u: a[0]),  # special-cased in _call
        "stream_where": _n("stream_where", lambda a,k,u: a[0]),  # special-cased
        "stream_map": _n("stream_map", lambda a,k,u: a[0]),       # special-cased
        "pipe":       _n("pipe",       lambda a,k,u: a[0]),        # stream pipe
        "take_while": _n("take_while", lambda a,k,u: a[0]), # special-cased
        "drop_while": _n("drop_while", lambda a,k,u: a[0]), # special-cased
        "zip_with":   _n("zip_with",   lambda a,k,u: a[0]), # special-cased
        "is_empty": _n("is_empty", lambda a,k,u: (True if a[0] is NOTHING else (len(list(_coerce_list(a[0]))) == 0 if isinstance(a[0],(LedgeList,LedgeLazyGenerator,str,LedgeMap)) else False))),
        "deep_copy": _n("deep_copy", lambda a,k,u: _py_to_ledge(_ledge_to_py(a[0]))),
        "index_of": _n("index_of", lambda a,k,u: next((i for i,x in enumerate(_coerce_list(a[0])) if _eq(x,a[1])), NOTHING)),
    }


# ── Interpreter ───────────────────────────────────────────────────────────────

class Interpreter:
    def __init__(self, output_fn=None, ai_backend=None, source=None):
        self.output = output_fn or print
        self.ai = ai_backend or {}
        self.source = source  # original source for error context
        self.source_lines = source.splitlines() if source else []
        self._globals = Env(name="<global>")
        self.output_lines = []
        self._call_stack = []
        self._allowed_modules = None  # None = allow all; set = allowlist
        self._max_iterations = None     # None = unlimited; int = max loop iterations
        self._max_memory_mb  = None     # None = unlimited; float = max MB
        self._iteration_count = 0       # current iteration counter   # for stack traces
        self._yield_collector = None
        self._setup_globals()

    def _setup_globals(self):
        global _HAS_AI_TYPES
        builtins = _make_builtins()
        builtins["error"] = _make_error_fn()
        # AI-native types (lazy import to avoid circular dependency)
        try:
            from .ai_types import make_ai_native_builtins, GLOBAL_AUDIT as _AUDIT
            import ledge_lang.ai_types as _ai
            _HAS_AI_TYPES = True
            ai_builtins = make_ai_native_builtins(_AUDIT)
            builtins.update(ai_builtins)
            # Make AI types available for isinstance checks
            self._uncertain_type = _ai.Uncertain
            self._stream_type = _ai.LedgeStream
            self._pipeline_type = _ai.LedgePipeline
            self._audit = _AUDIT
            # Ensure audit_query builtin uses THIS instance's audit
            from .interpreter import _Native
            self._globals.set("audit_query", _Native("audit_query", lambda a,k,u: _AUDIT.query(
                operation=a[0] if a else None,
                limit=int(a[1]) if len(a) > 1 else 100
            )))
            self._globals.set("audit_log", _Native("audit_log", lambda a,k,u: _AUDIT.query()))
            self._globals.set("audit_export", _Native("audit_export", lambda a,k,u: _AUDIT.export()))
        except Exception:
            self._uncertain_type = None
            self._stream_type = None
            self._pipeline_type = None
            self._audit = None
        for name, val in builtins.items():
            self._globals.set(name, val)

    def run(self, program, env=None):
        env = env or self._globals
        last = NOTHING
        for stmt in program.stmts:
            try:
                last = self._exec(stmt, env)
            except _Yield:
                raise LedgeError("'yield' can only be used inside a function body.\n  Fix: Move this 'yield' inside a 'define f():' block.")
            except _Break:
                raise LedgeError("'break' can only be used inside a 'while', 'for', or 'repeat' loop.\n  Fix: Move this 'break' inside a loop body.")
            except _Continue:
                raise LedgeError("'continue' can only be used inside a 'while', 'for', or 'repeat' loop.\n  Fix: Move this 'continue' inside a loop body.")
            except RecursionError:
                raise LedgeError(
                    "Maximum recursion depth exceeded.\n"
                    "  A function is calling itself too many times.\n"
                    "  Fix: Add a base case that stops the recursion, or check for infinite loops."
                )
        return last

    def _source_line(self, line_no):
        if line_no and self.source_lines and 0 < line_no <= len(self.source_lines):
            return self.source_lines[line_no - 1]
        return None

    # ── Statement execution ────────────────────────────────────────────────────

    def _exec(self, node, env):
        t = type(node)

        if t == Define:
            val = self._eval(node.value, env)
            hint = node.type_hint
            if hint and hint not in ("any", "nothing", "unknown"):
                if not _check_type_compat(val, hint) and val is not NOTHING:
                    actual = _type_of(val)
                    raise LedgeError(
                        f"Type mismatch: '{node.name}' is declared as '{hint}' "
                        f"but the value is '{actual}'.\n"
                        f"  Fix: Remove the type annotation, "
                        f"or use a value of type '{hint}'.\n"
                        f"  Tip: Use 'define {node.name}: any as ...' to accept any type."
                    )
            # Give anonymous functions their defined name (for JIT and debugging)
            from .core_types import LedgeFunction as LFn
            if isinstance(val, LFn) and val.name in ("<anon>", "<lambda>"):
                val.name = node.name
            env.set(node.name, val, hint)
            return NOTHING

        if t == Assign:
            val = self._eval(node.value, env)
            env.assign(node.name, val)
            return NOTHING

        if t == Show:
            self._show(self._eval(node.expr, env), node.format)
            return NOTHING

        if t == If:
            for cond, blk in node.branches:
                if _truthy(self._eval(cond, env)):
                    return self._block(blk, env.child())
            if node.else_block:
                return self._block(node.else_block, env.child())
            return NOTHING

        if t == For:
            it = self._eval(node.iterable, env)
            if isinstance(it, LedgeMap) and node.var2:
                items = list(it.items())
            elif isinstance(it, LedgeMap):
                items = list(it.keys())
            elif isinstance(it, LedgeLazyGenerator):
                items = list(it)
            elif isinstance(it, (LedgeList, list)):
                items = list(it)
            elif isinstance(it, str):
                items = list(it)
            else:
                raise LedgeError(f"Cannot iterate over {_repr(it)}")
            
            for item in items:
                c = env.child()
                if node.var2 and isinstance(item, tuple):
                    c.set(node.var, item[0]); c.set(node.var2, item[1])
                else:
                    c.set(node.var, item)
                try:
                    self._block(node.body, c)
                except _Break: break
                except _Continue: continue
                except _Yield as y:
                    if self._yield_collector is not None:
                        self._yield_collector.append(y.v)
                    else:
                        raise
            return NOTHING

        if t == While:
            while _truthy(self._eval(node.condition, env)):
                # Check iteration limit
                if self._max_iterations is not None:
                    self._iteration_count += 1
                    if self._iteration_count > self._max_iterations:
                        raise LedgeError(
                            f"Iteration limit exceeded ({self._max_iterations}).\n"
                            f"  Increase: interp._max_iterations = N  or  set_limit(\"max_iterations\", N)"
                        )
                try: self._block(node.body, env.child())
                except _Break: break
                except _Continue: continue
                except _Yield as y:
                    if self._yield_collector is not None:
                        self._yield_collector.append(y.v)
                    else:
                        raise
            return NOTHING
        if t == Repeat:
            if node.count is not None:
                for _ in range(int(self._eval(node.count, env))):
                    try: self._block(node.body, env.child())
                    except _Break: break
                    except _Continue: continue
                    except _Yield as y:
                        if self._yield_collector is not None:
                            self._yield_collector.append(y.v)
                        else:
                            raise
            else:
                while not _truthy(self._eval(node.condition, env)):
                    try: self._block(node.body, env.child())
                    except _Break: break
                    except _Continue: continue
            return NOTHING

        if t == Match:
            subj = self._eval(node.subject, env)
            for val, blk in node.cases:
                if _eq(subj, self._eval(val, env)):
                    return self._block(blk, env.child())
            if node.otherwise:
                return self._block(node.otherwise, env.child())
            return NOTHING

        if t == Check:
            try:
                result = self._block(node.body, env.child())
            except LedgeError as e:
                if node.recover_block:
                    c = env.child()
                    if node.recover_var: c.set(node.recover_var, e.ledge_msg)
                    result = self._block(node.recover_block, c)
                else:
                    result = NOTHING
            finally:
                if node.always_block:
                    self._block(node.always_block, env.child())
            return result

        if t == Return:
            raise _Return(self._eval(node.value, env) if node.value else NOTHING)

        if t == Break:    raise _Break()
        if t == Continue: raise _Continue()
        if t == Pass:     return NOTHING

        if t == Yield:
            val = self._eval(node.value, env)
            if self._yield_collector is not None:
                self._yield_collector.append(val)
                return NOTHING
            raise _Yield(val)

        if t == RunStmt:
            val = self._eval(node.expr, env)
            return val if node.wait else NOTHING

        if t == Import:
            self._import(node, env)
            return NOTHING

        if t == TypeDef:
            env.set(node.name, LedgeType(node.name, node.fields))
            return NOTHING

        if t == ExprStmt:
            return self._eval(node.expr, env)

        if t == Block:
            return self._block(node, env)

        # v1.0 AI-native constructs
        if t.__name__ == 'WhenStmt':
            return self._exec_when(node, env)

        if t.__name__ == 'EmitStmt':
            val = self._eval(node.value, env)
            target = self._eval(node.target, env) if node.target else NOTHING
            if hasattr(target, 'emit'):
                target.emit(val)
            return NOTHING

        if t.__name__ == 'SubscribeStmt':
            return self._exec_subscribe(node, env)

        if t.__name__ == 'AgentDef':
            return self._exec_agent_def(node, env)

        raise LedgeError(f"Unknown statement: {type(node).__name__}")


    def _eval_stream(self, node, env):
        """Evaluate a StreamExpr to a LedgeStream."""
        try:
            from .ai_types import LedgeStream
        except ImportError:
            # Fallback: return list
            if node.source:
                src = self._eval(node.source, env)
                return src if isinstance(src, (LedgeList,)) else LedgeList(src)
            return LedgeList()

        if node.source_type == "url":
            source_val = _repr(self._eval(node.source, env))
            # For now: create a stream from the URL string (stub)
            s = LedgeStream.of(source_val)
        elif node.source_type == "list" and node.source:
            source_val = self._eval(node.source, env)
            s = LedgeStream.from_list(source_val)
        elif node.source_type == "empty":
            s = LedgeStream.of()
        else:
            s = LedgeStream.of()

        # Apply filters
        for filt in node.filters:
            fn = LedgeFunction("<stream-where>", [("_item", None)], filt, env)
            s = s.where(lambda item, f=fn: self._call_fn(f, [item], {}, None))

        # Apply transforms
        for trans in node.transforms:
            fn = LedgeFunction("<stream-transform>", [("_item", None)], trans, env)
            s = s.transform(lambda item, f=fn: self._call_fn(f, [item], {}, None))

        return s

    def _exec_when(self, node, env):
        """Execute: when stream has new item as name: block"""
        source = self._eval(node.source, env)
        
        try:
            from .ai_types import LedgeStream
            is_stream = isinstance(source, LedgeStream)
        except ImportError:
            is_stream = False
        
        if node.trigger == "has_new_item" and is_stream:
            # Subscribe to stream and run block for each item
            for item in source:
                c = env.child()
                if node.item_name:
                    c.set(node.item_name, item)
                try:
                    self._block(node.body, c)
                except _Break:
                    break
                except _Continue:
                    continue
        elif node.trigger == "condition":
            # One-time conditional
            if _truthy(source):
                self._block(node.body, env.child())
        else:
            # Iterable
            try:
                for item in (source if hasattr(source, '__iter__') else []):
                    c = env.child()
                    if node.item_name:
                        c.set(node.item_name, item)
                    try:
                        self._block(node.body, c)
                    except _Break:
                        break
                    except _Continue:
                        continue
            except TypeError:
                pass
        return NOTHING

    def _exec_subscribe(self, node, env):
        """Execute: subscribe to stream as name: block"""
        source = self._eval(node.source, env)
        for item in (source if hasattr(source, '__iter__') else []):
            c = env.child()
            c.set(node.item_name, item)
            try:
                self._block(node.body, c)
            except _Break:
                break
            except _Continue:
                continue
        return NOTHING

    def _exec_agent_def(self, node, env):
        """Execute: agent Name: tools: ... model: ... behavior: ..."""
        try:
            from .ai_types import MCPTool
            from .interpreter import LedgeFunction
        except ImportError:
            pass
        
        # Create agent as a LedgeMap with all components
        tools_map = LedgeMap()
        for tool_name, tool_source in node.tools:
            source_val = self._eval(tool_source, env)
            tools_map[tool_name] = source_val
        
        model_val = self._eval(node.model_name, env) if node.model_name else "claude-sonnet-4-6"
        
        # Create behavior function
        behavior_fn = LedgeFunction(
            name=f"<agent:{node.name}>",
            params=[],
            body=node.behavior,
            env=env
        )
        
        agent = LedgeMap({
            "name": node.name,
            "tools": tools_map,
            "model": model_val,
            "behavior": behavior_fn,
            "type": "agent",
        })
        
        env.set(node.name, agent)
        return NOTHING

    def _block(self, block, env, yields=None):
        last = NOTHING
        for stmt in block.stmts:
            last = self._exec(stmt, env)
        return last

    # ── Expression evaluation ──────────────────────────────────────────────────

    def _eval(self, node, env):
        t = type(node)

        if t == NumberLit:  return node.value
        if t == BoolLit:    return node.value
        if t == NothingLit: return NOTHING

        if t == StringLit:
            if '{' in node.value:
                return self._interpolate(node.value, env)
            return node.value

        if t == Identifier:
            return env.get(node.name)

        if t == ListLit:
            return LedgeList(self._eval(e, env) for e in node.elements)

        if t == MapLit:
            m = LedgeMap()
            for k, v in node.pairs:
                m[_repr(self._eval(k, env))] = self._eval(v, env)
            return m

        if t == BinOp:    return self._binop(node, env)
        if t == UnaryOp:  return self._unary(node, env)
        if t == LogicalOp: return self._logical(node, env)

        if t == IsOp:
            res = _eq(self._eval(node.left, env), self._eval(node.right, env))
            return not res if node.negated else res

        if t == Fallback:
            try:
                v = self._eval(node.expr, env)
                return self._eval(node.default, env) if v is NOTHING else v
            except LedgeError:
                return self._eval(node.default, env)

        if t == Call:     return self._call(node, env)
        if t == Index:    return self._index(node, env)
        if t == Field:    return self._field(node, env)

        if t == Lambda:
            return LedgeFunction("<lambda>", [(p, None) for p in node.params], node.body, env)

        if t == ParallelExpr:
            return self._parallel(node.exprs, env)

        if t.__name__ == 'StreamExpr':
            return self._eval_stream(node, env)

        if t.__name__ == 'UncertainExpr':
            val = self._eval(node.value, env)
            conf = self._eval(node.confidence, env)
            if self._uncertain_type:
                return self._uncertain_type(val, float(conf))
            return val

        if t.__name__ == 'ConfidenceGate':
            val = self._eval(node.expr, env)
            threshold = float(self._eval(node.threshold, env))
            if self._uncertain_type and isinstance(val, self._uncertain_type):
                return val.when(threshold, self._eval(node.fallback, env))
            if _truthy(val):
                return val
            return self._eval(node.fallback, env)

        if t.__name__ == 'MCPExpr':
            server = _repr(self._eval(node.server, env))
            url = _repr(self._eval(node.url, env)) if node.url else None
            try:
                from .ai_types import MCPTool
                return MCPTool(name=server, endpoint=url or f"http://localhost:3000", tool_name=server)
            except ImportError:
                return LedgeMap({"type": "mcp_tool", "server": server, "url": url or ""})

        if t == FuncDef:
            fn = LedgeFunction("<anon>", node.params, node.body, env, node.is_generator)
            fn.contract = getattr(node, 'contract', None)
            return fn

        if t == AnalyzeExpr:  return self._ai_analyze(node, env)
        if t == GenerateExpr: return self._ai_generate(node, env)
        if t == AskExpr:      return self._ai_ask(node, env)
        if t == EmbedExpr:    return self._ai_embed(node, env)
        if t == ClassifyExpr: return self._ai_classify(node, env)

        raise LedgeError(f"Unknown expression: {type(node).__name__}")

    def _binop(self, node, env):
        L = self._eval(node.left, env)
        R = self._eval(node.right, env)
        op = node.op
        if op == "+":
            if isinstance(L, str) or isinstance(R, str): return _repr(L) + _repr(R)
            if isinstance(L, (LedgeList, LedgeLazyGenerator)) and isinstance(R, (LedgeList, LedgeLazyGenerator)):
                return LedgeList(list(_coerce_list(L)) + list(_coerce_list(R)))
            if isinstance(L, (int,float)) and isinstance(R, (int,float)) and not isinstance(L,bool) and not isinstance(R,bool):
                return L + R
            raise LedgeError(f"Cannot add {_type_of(L)} and {_type_of(R)}")
        if op == "-":
            if isinstance(L,(int,float)) and isinstance(R,(int,float)) and not isinstance(L,bool) and not isinstance(R,bool):
                return L - R
            raise LedgeError(f"Cannot subtract {_type_of(R)} from {_type_of(L)}")
        if op == "*":
            if isinstance(L,(int,float)) and isinstance(R,(int,float)) and not isinstance(L,bool) and not isinstance(R,bool):
                return L * R
            if isinstance(L,str) and isinstance(R,(int,float)): return L * int(R)
            raise LedgeError(f"Cannot multiply {_type_of(L)} and {_type_of(R)}")
        if op == "/":
            if isinstance(L,(int,float)) and isinstance(R,(int,float)) and not isinstance(L,bool) and not isinstance(R,bool):
                return NOTHING if R == 0 else L / R
            raise LedgeError(f"Cannot divide {_type_of(L)} by {_type_of(R)}")
        if op == "=":  return _eq(L, R)
        if op == "!=": return not _eq(L, R)
        if op in ("<",">","<=",">="):
            if not isinstance(L,(int,float)) or not isinstance(R,(int,float)) or isinstance(L,bool) or isinstance(R,bool):
                raise LedgeError(f"Comparison '{op}' requires numbers, got {_type_of(L)} and {_type_of(R)}")
            return {"<":L<R, ">":L>R, "<=":L<=R, ">=":L>=R}[op]
        raise LedgeError(f"Unknown operator: {op}")

    def _unary(self, node, env):
        v = self._eval(node.operand, env)
        if node.op == "not": return not _truthy(v)
        if node.op == "-":
            if isinstance(v,(int,float)) and not isinstance(v,bool): return -v
            raise LedgeError(f"Cannot negate {_type_of(v)}")

    def _logical(self, node, env):
        L = self._eval(node.left, env)
        if node.op == "and": return L if not _truthy(L) else self._eval(node.right, env)
        if node.op == "or":  return L if _truthy(L) else self._eval(node.right, env)

    def _format_expr(self, node) -> str:
        """Format an AST node as human-readable Ledge source text."""
        t = type(node).__name__
        if t == "NumberLit":  return str(node.value)
        if t == "StringLit":  return f'"{node.value}"'
        if t == "BoolLit":    return "true" if node.value else "false"
        if t == "NothingLit": return "nothing"
        if t == "Identifier": return node.name
        if t == "BinOp":
            ops = {"=":"=","!=":"!=","<":"<",">":">","<=":"<=",">=":">=",
                   "+":"+","-":"-","*":"*","/":"/"}
            op_str = ops.get(node.op, node.op)
            return f"{self._format_expr(node.left)} {op_str} {self._format_expr(node.right)}"
        if t == "UnaryOp":
            if node.op == "not": return f"not {self._format_expr(node.operand)}"
            return f"{node.op}{self._format_expr(node.operand)}"
        if t == "LogicalOp":
            return f"{self._format_expr(node.left)} {node.op} {self._format_expr(node.right)}"
        if t == "Call":
            fn = self._format_expr(node.callee)
            args = ", ".join(self._format_expr(a) for a in node.args)
            return f"{fn}({args})"
        if t == "Index":
            return f"{self._format_expr(node.obj)}[{self._format_expr(node.key)}]"
        if t == "FieldAccess":
            return f"{self._format_expr(node.obj)}.{node.name}"
        return str(node)


    def _call(self, node, env):
        # Special higher-order functions
        if isinstance(node.callee, Identifier) and node.callee.name in ("map", "filter", "reduce", "zip_with", "group_by", "take_while", "drop_while", "stream_where", "stream_map"):
            name = node.callee.name
            args = [self._eval(a, env) for a in node.args]
            fn = args[1] if len(args) > 1 else None
            lst = args[0]
            
            if name == "map" and isinstance(fn, (LedgeFunction, _Native)):
                return LedgeList(self._call_fn(fn, [x], {}, None) for x in _coerce_list(lst))
            if name == "filter" and isinstance(fn, (LedgeFunction, _Native)):
                return LedgeList(x for x in _coerce_list(lst) if _truthy(self._call_fn(fn, [x], {}, None)))
            if name == "reduce" and isinstance(fn, (LedgeFunction, _Native)):
                acc = args[2] if len(args) > 2 else NOTHING
                for x in _coerce_list(lst):
                    acc = self._call_fn(fn, [acc, x], {}, None)
                return acc
            if name == "zip_with" and isinstance(fn, (LedgeFunction, _Native)) and len(args) >= 3:
                return LedgeList(self._call_fn(fn, [x, y], {}, None) for x, y in zip(_coerce_list(lst), _coerce_list(args[2])))
            if name == "stream_where" and isinstance(fn, (LedgeFunction, _Native)):
                try:
                    from .ai_types import LedgeStream
                    if isinstance(lst, LedgeStream):
                        return lst.where(lambda item, f=fn: self._call_fn(f, [item], {}, None))
                except ImportError:
                    pass
                return LedgeList(x for x in _coerce_list(lst) if _truthy(self._call_fn(fn, [x], {}, None)))

            if name == "stream_map" and isinstance(fn, (LedgeFunction, _Native)):
                try:
                    from .ai_types import LedgeStream
                    if isinstance(lst, LedgeStream):
                        return lst.transform(lambda item, f=fn: self._call_fn(f, [item], {}, None))
                except ImportError:
                    pass
                return LedgeList(self._call_fn(fn, [x], {}, None) for x in _coerce_list(lst))

            if name == "group_by" and isinstance(fn, (LedgeFunction, _Native)):
                result = LedgeMap()
                for item in _coerce_list(lst):
                    key = _repr(self._call_fn(fn, [item], {}, None))
                    if key not in result:
                        result[key] = LedgeList()
                    result[key].append(item)
                return result
            if name == "take_while" and isinstance(fn, (LedgeFunction, _Native)):
                result = LedgeList()
                for item in _coerce_list(lst):
                    if not _truthy(self._call_fn(fn, [item], {}, None)): break
                    result.append(item)
                return result
            if name == "drop_while" and isinstance(fn, (LedgeFunction, _Native)):
                result = LedgeList()
                dropping = True
                for item in _coerce_list(lst):
                    if dropping and _truthy(self._call_fn(fn, [item], {}, None)): continue
                    dropping = False
                    result.append(item)
                return result
            return _coerce_list(lst)

        callee = self._eval(node.callee, env)
        args   = [self._eval(a, env) for a in node.args]
        kwargs = {k: self._eval(v, env) for k, v in node.kwargs.items()}

        # Python FFI call
        if isinstance(callee, PythonObject):
            obj = callee.obj
            if callable(obj):
                py_args = [_ledge_to_py(a) for a in args]
                py_kw   = {k: _ledge_to_py(v) for k, v in kwargs.items()}
                try:
                    result = obj(*py_args, **py_kw)
                    return _py_to_ledge(result)
                except Exception as e:
                    raise LedgeError(f"Python call failed: {e}")
            return _py_to_ledge(obj)

        if isinstance(callee, LedgeType):
            return self._instantiate(callee, args, kwargs)

        return self._call_fn(callee, args, kwargs, node.using)

    def _call_fn(self, callee, args, kwargs, using):
        if isinstance(callee, _Native):
            try: return callee(args, kwargs, using)
            except LedgeError: raise
            except Exception as e: raise LedgeError(str(e))

        if isinstance(callee, LedgeFunction):
            fn_name = callee.name
            self._call_stack.append(fn_name)
            try:
                c = callee.env.child(fn_name)
                # Contract: check preconditions
                contract = getattr(callee, 'contract', None) or getattr(callee, '_contract', None)
                for i, (pname, phint) in enumerate(callee.params):
                    if i < len(args): val = args[i]
                    elif pname in kwargs: val = kwargs[pname]
                    else: raise LedgeError(f"Missing argument '{pname}' for '{fn_name}'")
                    if phint and phint not in ("any",):
                        if not _check_type_compat(val, phint):
                            raise LedgeError(f"Argument '{pname}' must be {phint}, got {_type_of(val)}")
                    c.set(pname, val, phint)
                for k, v in kwargs.items():
                    if not any(p[0]==k for p in callee.params): c.set(k, v)

                # Lazy generator — returns LedgeLazyGenerator
                if callee.is_gen:
                    gen = LedgeLazyGenerator(callee, c, self)
                    return gen

                # Contract preconditions
                if contract:
                    for i, req_expr in enumerate(contract.requires):
                        if not _truthy(self._eval(req_expr, c)):
                            # Reconstruct a human-readable condition
                            try:
                                cond_src = self._format_expr(req_expr)
                            except Exception:
                                cond_src = str(req_expr)
                            display_name = fn_name if fn_name != "<anon>" else "this function"
                            raise LedgeError(
                                f"Contract violated: precondition failed in {display_name}.\n"
                                f"  Failed condition: {cond_src}\n"
                                f"  Fix: Ensure this condition is true before calling {display_name}."
                            )

                # Lambda body is an expression, not a block
                if not isinstance(callee.body, Block):
                    result = self._eval(callee.body, c)
                    # Contract postconditions
                    if contract:
                        for ens_expr, ens_desc in zip(contract.ensures, contract.ensure_descs or [""]*len(contract.ensures)):
                            ens_env = c.child()
                            ens_env.set("result", result)
                            if not _truthy(self._eval(ens_expr, ens_env)):
                                try:
                                    cond_readable = self._format_expr(ens_expr)
                                except Exception:
                                    cond_readable = ens_desc if ens_desc else str(ens_expr)
                                dn = fn_name if fn_name != "<anon>" else "this function"
                                raise LedgeError(
                                    f"Contract violated: postcondition failed in {dn}.\n"
                                    f"  Failed condition: {cond_readable}\n"
                                    f"  Fix: The function must return a value satisfying: {cond_readable}"
                                )
                    return result

                try:
                    self._block(callee.body, c)
                except _Return as r:
                    result = r.v
                    # Contract postconditions
                    if contract:
                        for ens_expr, ens_desc in zip(contract.ensures, contract.ensure_descs or [""]*len(contract.ensures)):
                            ens_env = c.child()
                            ens_env.set("result", result)
                            if not _truthy(self._eval(ens_expr, ens_env)):
                                try:
                                    cond_r = self._format_expr(ens_expr)
                                except Exception:
                                    cond_r = ens_desc if ens_desc else str(ens_expr)
                                dn2 = fn_name if fn_name != "<anon>" else "this function"
                                raise LedgeError(
                                    f"Contract violated: postcondition failed in {dn2}.\n"
                                    f"  Failed condition: {cond_r}\n"
                                    f"  Fix: Return a value satisfying: {cond_r}"
                                )
                    return result
                return NOTHING
            finally:
                if self._call_stack: self._call_stack.pop()

        t = _type_of(callee)
        repr_c = _repr(callee)[:40]
        hints = {
            "number":  "Numbers can't be called. Use it as an argument instead.",
            "text":    "Strings can't be called. Did you mean to define a function?",
            "map":     "Maps can't be called. Access fields with map[key] or map.field",
            "list":    "Lists can't be called. Access items with list[index]",
            "nothing": "nothing is not callable. The variable may not have been initialized.",
            "truth":   "Booleans can't be called.",
        }
        hint = hints.get(t, "Only functions (defined with 'define f():') can be called.")
        raise LedgeError(
            f"'{repr_c}' is not callable — it is a {t}.\n"
            f"  {hint}\n"
            f"  Fix: Use 'define name(params):' to create a callable function."
        )

    def _make_python_gen(self, fn, env):
        """
        Create a truly lazy Python generator from a Ledge generator function.
        Uses a thread + queue so infinite generators work correctly.
        Values are produced on demand — never hangs on infinite sequences.
        """
        import queue as _queue
        
        _DONE = object()  # sentinel
        q = _queue.Queue(maxsize=1)  # backpressure: producer waits for consumer
        
        def producer():
            prev = self._yield_collector
            try:
                # Override yield handling to put values on queue
                def yield_handler(val):
                    q.put(val)
                
                self._yield_collector = None
                
                if isinstance(fn.body, Block):
                    for stmt in fn.body.stmts:
                        try:
                            self._exec_with_yield_queue(stmt, env, q)
                        except _Return:
                            break
                        except _Yield as y:
                            q.put(y.v)
            except Exception as e:
                q.put(("__error__", e))
            finally:
                self._yield_collector = prev
                q.put(_DONE)
        
        t = threading.Thread(target=producer, daemon=True)
        t.start()
        
        while True:
            item = q.get()
            if item is _DONE:
                break
            if isinstance(item, tuple) and len(item)==2 and item[0] == "__error__":
                raise item[1]
            yield item
    
    def _exec_with_yield_queue(self, stmt, env, q):
        """Execute a statement, putting yields on the queue."""
        import queue as _queue
        t = type(stmt)
        
        # For most statements, just run normally but catch yields
        if t in (While, Repeat, For):
            # These need special handling to propagate yields
            if t == While:
                while _truthy(self._eval(stmt.condition, env)):
                    try: self._block_with_yield_queue(stmt.body, env.child(), q)
                    except _Break: break
                    except _Continue: continue
            elif t == Repeat:
                if stmt.count is not None:
                    for _ in range(int(self._eval(stmt.count, env))):
                        try: self._block_with_yield_queue(stmt.body, env.child(), q)
                        except _Break: break
                        except _Continue: continue
                else:
                    while not _truthy(self._eval(stmt.condition, env)):
                        try: self._block_with_yield_queue(stmt.body, env.child(), q)
                        except _Break: break
                        except _Continue: continue
            elif t == For:
                it = self._eval(stmt.iterable, env)
                items = list(it) if not isinstance(it, (list,)) else it
                for item in items:
                    c = env.child()
                    c.set(stmt.var, item)
                    try: self._block_with_yield_queue(stmt.body, c, q)
                    except _Break: break
                    except _Continue: continue
        elif t == Yield:
            val = self._eval(stmt.value, env)
            q.put(val)
        else:
            try:
                self._exec(stmt, env)
            except _Yield as y:
                q.put(y.v)
    
    def _block_with_yield_queue(self, block, env, q):
        """Run a block, routing yields to the queue."""
        for stmt in block.stmts:
            self._exec_with_yield_queue(stmt, env, q)

    def _parallel(self, exprs, env):
        """True parallel execution using thread pool."""
        if len(exprs) == 0:
            return LedgeList()
        
        results = [NOTHING] * len(exprs)
        errors = [None] * len(exprs)
        
        def run_one(i, expr):
            try:
                results[i] = self._eval(expr, env)
            except Exception as e:
                errors[i] = e
        
        threads = []
        for i, expr in enumerate(exprs):
            t = threading.Thread(target=run_one, args=(i, expr), daemon=True)
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join(timeout=30)
        
        # Check for errors
        for i, err in enumerate(errors):
            if err is not None:
                raise LedgeError(f"Parallel task {i} failed: {err}")
        
        return LedgeList(results)

    def _index(self, node, env):
        obj = self._eval(node.obj, env)
        key = self._eval(node.key, env)
        if isinstance(obj, LedgeLazyGenerator):
            return obj[int(key)] if isinstance(key, (int, float)) else NOTHING
        if isinstance(obj, LedgeList):
            if not isinstance(key, (int, float)) or isinstance(key, bool):
                raise LedgeError(f"List index must be a number, got {_type_of(key)}")
            idx = int(key)
            return obj[idx] if 0 <= idx < len(obj) else NOTHING
        if isinstance(obj, LedgeMap):
            return obj.get(_repr(key), NOTHING)
        if isinstance(obj, str):
            idx = int(key)
            return obj[idx] if 0 <= idx < len(obj) else NOTHING
        if isinstance(obj, LedgeInstance):
            return obj.fields.get(_repr(key), NOTHING)
        if isinstance(obj, PythonModule):
            attr = getattr(obj.module, _repr(key), None)
            if attr is None: return NOTHING
            return _py_to_ledge(attr) if not callable(attr) else PythonObject(attr)
        if isinstance(obj, PythonObject):
            attr = getattr(obj.obj, _repr(key), None)
            if attr is None:
                try: return _py_to_ledge(obj.obj[_ledge_to_py(key)])
                except: return NOTHING
            return _py_to_ledge(attr) if not callable(attr) else PythonObject(attr)
        t = _type_of(obj)
        t = _type_of(obj)
        key_r = _repr(key)
        obj_r = str(_repr(obj))[:40]
        fixes = {
            "number":  "Fix: Use this number as a value, not as a container.",
            "truth":   "Fix: Booleans cannot be indexed.",
            "nothing": "Fix: The value is 'nothing' — it may not have been assigned.",
        }
        fix_msg = fixes.get(t, "Fix: Only list[index], map[key], and text[index] support indexing.")
        raise LedgeError(
            "Cannot index '" + t + "' with [" + key_r + "].\n"
            "  " + fix_msg
        )
    def _field(self, node, env):
        obj = self._eval(node.obj, env)
        name = node.name
        if isinstance(obj, LedgeMap): return obj.get(name, NOTHING)
        if isinstance(obj, LedgeInstance): return obj.fields.get(name, NOTHING)
        if isinstance(obj, PythonModule):
            attr = getattr(obj.module, name, None)
            if attr is None: return NOTHING
            return _py_to_ledge(attr) if not callable(attr) else PythonObject(attr)
        if isinstance(obj, PythonObject):
            attr = getattr(obj.obj, name, None)
            if attr is None: return NOTHING
            return _py_to_ledge(attr) if not callable(attr) else PythonObject(attr)
        raise LedgeError(f"Cannot access '.{name}' on {_type_of(obj)}")

    def _instantiate(self, lt, args, kwargs):
        fields = {}
        for i, (fname, ftype, fdefault) in enumerate(lt.fields):
            if i < len(args): val = args[i]
            elif fname in kwargs: val = kwargs[fname]
            elif fdefault is not None: val = self._eval(fdefault, self._globals)
            else: raise LedgeError(f"Missing field '{fname}' for type '{lt.name}'")
            if ftype and ftype not in ("any",):
                if not _check_type_compat(val, ftype):
                    raise LedgeError(f"Field '{fname}' must be {ftype}, got {_type_of(val)}")
            fields[fname] = val
        return LedgeInstance(lt.name, fields, lt)

    def _interpolate(self, template, env):
        result = []
        i = 0
        while i < len(template):
            if template[i] == '{' and (i == 0 or template[i-1] != '\\'):
                j = template.find('}', i + 1)
                if j == -1: result.append(template[i:]); break
                snippet = template[i+1:j]
                from .lexer import Lexer
                from .parser import Parser
                try:
                    toks = Lexer(snippet).tokenize()
                    expr = Parser(toks).parse_expr_entry()
                    result.append(_repr(self._eval(expr, env)))
                except Exception:
                    result.append(f"{{{snippet}}}")
                i = j + 1
            else:
                result.append(template[i]); i += 1
        return ''.join(result)

    def _show(self, val, fmt):
        if fmt == "json":
            text = json.dumps(_ledge_to_py(val), indent=2, ensure_ascii=False)
        elif fmt == "table" and isinstance(val, (LedgeList, LedgeLazyGenerator)):
            lst = list(_coerce_list(val))
            text = self._table(lst)
        elif fmt == "raw":
            text = str(val)
        else:
            text = _repr(val)
        self.output_lines.append(text)
        self.output(text)

    def _table(self, lst):
        if not lst: return "(empty)"
        if isinstance(lst[0], LedgeMap):
            keys = list(lst[0].keys())
            widths = {k: max(len(k), max(len(_repr(row.get(k,NOTHING))) for row in lst)) for k in keys}
            header = " | ".join(k.ljust(widths[k]) for k in keys)
            sep    = "-+-".join("-"*widths[k] for k in keys)
            rows   = [" | ".join(_repr(row.get(k,NOTHING)).ljust(widths[k]) for k in keys) for row in lst]
            return "\n".join([header, sep] + rows)
        return "\n".join(_repr(x) for x in lst)

    def _import(self, node, env):
        from .stdlib import load_module, STDLIB
        
        # Python FFI: import python "module_name" as alias
        if node.path.startswith("python:") or node.path.startswith("py:"):
            module_name = node.path.split(":", 1)[1].strip()
            return self._import_python(module_name, node, env)
        
        # Also support: from python "numpy" import array, zeros
        if node.path == "python" and node.names:
            # Handled differently
            pass
        
        try:
            m = load_module(node.path)
            if node.alias:
                env.set(node.alias, m)
            else:
                for name in node.names:
                    if name in m: env.set(name, m[name])
                    else: raise LedgeError(f"'{name}' not found in module '{node.path}'")
        except LedgeError:
            # Try as Python module
            try:
                self._import_python(node.path, node, env)
            except ImportError:
                raise LedgeError(f"No module named '{node.path}' — available stdlib: time, file, http, regex, collections, env, math, text. For Python packages: import \"python:{node.path}\" as alias")

    def _import_python(self, module_name, node, env):
        """Import a Python module for use in Ledge.
        
        If the interpreter has a restricted_modules set, only modules in that
        set can be imported. This is enabled by --restrict-ffi in the CLI.
        """
        import importlib
        
        # Check allowlist if restrictions are enabled
        allowed = getattr(self, '_allowed_modules', None)
        if allowed is not None and module_name not in allowed:
            raise LedgeError(
                f"Import blocked: '{module_name}' is not in the allowed modules list.\n"
                f"  Allowed: {sorted(allowed)}\n"
                f"  Run without --restrict-ffi to allow all modules, or add '{module_name}' to --allow-import."
            )
        
        try:
            mod = importlib.import_module(module_name)
            pm = PythonModule(module_name, mod)
            if node.alias:
                env.set(node.alias, pm)
            else:
                for name in node.names:
                    attr = getattr(mod, name, None)
                    if attr is None:
                        raise LedgeError(f"'{name}' not found in Python module '{module_name}'")
                    val = _py_to_ledge(attr) if not callable(attr) else PythonObject(attr)
                    env.set(name, val)
                if not node.names:
                    env.set(module_name.split('.')[-1], pm)
        except ImportError as e:
            raise LedgeError(f"Cannot import Python module '{module_name}': {e}\nInstall with: pip install {module_name}")

    # ── AI instructions ────────────────────────────────────────────────────────

    def _ai_analyze(self, node, env):
        text = _repr(self._eval(node.text, env))
        if "analyze" in self.ai:
            # Real backend connected
            result = self.ai["analyze"](text, node.mode)
            confidence = 1.0
            if isinstance(result, LedgeMap) and "confidence" in result:
                try: confidence = float(result["confidence"])
                except: pass
        else:
            # NO backend — confidence MUST be 0.0, never fake a result
            result = LedgeMap({
                "mode":   node.mode,
                "result": NOTHING,
                "ok":     False,
                "error":  "No AI backend connected. Connect a backend via run(source, ai_backend={...})"
            })
            confidence = 0.0   # CRITICAL: never return high confidence without real AI

        if self._uncertain_type is not None:
            if self._audit is not None:
                self._audit.record("analyze", text, result, model=node.mode, confidence=confidence)
            return self._uncertain_type(result, confidence, source="analyze", model=node.mode, declared_type="map")
        return result


    def _ai_generate(self, node, env):
        prompt = _repr(self._eval(node.prompt, env))
        if "generate" in self.ai:
            result = self.ai["generate"](prompt, node.mode)
        else:
            # NO backend — explicit failure, not silent stub
            result = NOTHING
        if self._uncertain_type is not None:
            confidence = 0.0 if result is NOTHING else 1.0
            if self._audit is not None:
                self._audit.record("generate", prompt, result, model=node.mode)
            return self._uncertain_type(result, confidence, source="generate", model=node.mode, declared_type="text")
        return result
    def _ai_ask(self, node, env):
        q = _repr(self._eval(node.question, env))
        if "ask" in self.ai:
            result = self.ai["ask"](q)
        else:
            result = NOTHING  # Explicit: no backend, no answer
        if self._uncertain_type is not None:
            confidence = 0.0 if result is NOTHING else 1.0
            if self._audit is not None:
                self._audit.record("ask", q, result)
            return self._uncertain_type(result, confidence, source="ask", declared_type="text")
        return result
    def _ai_embed(self, node, env):
        text = _repr(self._eval(node.text, env))
        if "embed" in self.ai:
            result = self.ai["embed"](text)
        else:
            result = NOTHING  # Explicit: no embedding without backend
        if self._uncertain_type is not None:
            confidence = 0.0 if result is NOTHING else 1.0
            if self._audit is not None:
                self._audit.record("embed", text, result)
            return self._uncertain_type(result, confidence, source="embed", declared_type="list")
        return result

    def _ai_classify(self, node, env):
        text   = _repr(self._eval(node.text, env))
        labels = [_repr(self._eval(l, env)) for l in node.labels]
        if "classify" in self.ai:
            # Real backend — supports both str return and {"value":..., "confidence":...} return
            result = self.ai["classify"](text, labels)
            confidence = 0.85  # default unless backend provides confidence
            if isinstance(result, dict) and "confidence" in result:
                confidence = float(result["confidence"])
                result = result.get("value", result.get("answer", NOTHING))
        else:
            # NO backend — do NOT silently pick first label
            # returning NOTHING makes it clear there's no real classification
            result     = NOTHING
            confidence = 0.0  # CRITICAL: never pretend to classify without AI

        if self._uncertain_type is not None:
            if self._audit is not None:
                self._audit.record("classify", text, result, model=str(labels))
            return self._uncertain_type(result, confidence, source="classify", declared_type="text")
        return result
