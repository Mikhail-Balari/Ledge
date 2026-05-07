"""
Ledge Core Value Types
======================
Base value types used by both interpreter.py and ai_types.py.
This module has NO internal dependencies — imports only stdlib.
This eliminates the circular dependency between interpreter and ai_types.

DO NOT import from interpreter.py or ai_types.py here.
"""

import math
import json
import time
import hashlib
import threading
from typing import Any, Dict, List, Optional


# ── Error type ────────────────────────────────────────────────────────────────

class LedgeError(Exception):
    """
    The single error type for all Ledge runtime errors.
    Contains: message, source location, suggestions, call stack.
    Never crashes — always provides actionable information.
    """
    def __init__(self, msg, line=0, col=0, source_line=None, stack_trace=None):
        self.ledge_msg   = msg
        self.line        = line
        self.col         = col
        self.source_line = source_line
        self.stack_trace = stack_trace or []

        parts = [f"[Line {line}] Runtime error: {msg}" if line else f"Runtime error: {msg}"]
        if source_line:
            parts.append(f"  | {source_line}")
            if col:
                parts.append(f"  | {' ' * (col - 1)}^")
        if stack_trace:
            parts.append("Call stack:")
            for frame in reversed(stack_trace[-5:]):
                parts.append(f"  in {frame}")
        super().__init__("\n".join(parts))


# ── Control flow signals ──────────────────────────────────────────────────────

class _Return(Exception):
    def __init__(self, v): self.v = v

class _Break(Exception):    pass
class _Continue(Exception): pass

class _Yield(Exception):
    def __init__(self, v): self.v = v



# ── Bottom value ──────────────────────────────────────────────────────────────

class _Nothing:
    """The unique bottom value. nothing is not null, not False, not 0."""
    _inst = None

    def __new__(cls):
        if not cls._inst:
            cls._inst = super().__new__(cls)
        return cls._inst

    def __repr__(self):  return "nothing"
    def __bool__(self):  return False
    def __eq__(self, other): return other is self
    def __hash__(self):  return hash("__ledge_nothing__")


NOTHING = _Nothing()


# ── Collection types ──────────────────────────────────────────────────────────

class LedgeList(list):
    """Ledge list — extends Python list for isinstance checks."""
    pass


class LedgeMap(dict):
    """Ledge map — extends Python dict for isinstance checks."""
    pass


# ── Function types ────────────────────────────────────────────────────────────

class LedgeFunction:
    """A Ledge function with lexical closure."""
    def __init__(self, name, params, body, env, is_gen=False, contract=None):
        self.name     = name
        self.params   = params        # [(param_name, type_hint), ...]
        self.body     = body
        self.env      = env
        self.is_gen   = is_gen
        self.contract = contract
        self._type_hints = {p[0]: p[1] for p in params if len(p) > 1 and p[1]}

    def __repr__(self): return f"<function {self.name}>"


class LedgeType:
    """A user-defined type descriptor."""
    def __init__(self, name, fields):
        self.name   = name
        self.fields = fields  # [(field_name, type_hint, default), ...]

    def __repr__(self): return f"<type {self.name}>"


class LedgeInstance:
    """An instance of a user-defined type."""
    def __init__(self, type_name, fields, type_def=None):
        self.type_name = type_name
        self.fields    = fields      # {field_name: value}
        self.type_def  = type_def

    def __repr__(self):
        parts = ", ".join(f"{k}: {_repr(v)}" for k, v in self.fields.items())
        return f"{self.type_name}({{{parts}}})"


class _Native:
    """A native (Python-implemented) builtin function."""
    def __init__(self, name, fn):
        self.name = name
        self.fn   = fn

    def __call__(self, args, kw, using):
        return self.fn(args, kw, using)

    def __repr__(self): return f"<builtin {self.name}>"


# ── Python interop wrappers ───────────────────────────────────────────────────

class PythonModule:
    """A Python module imported via import \"python:name\"."""
    def __init__(self, name, module):
        self.name   = name
        self.module = module

    def __repr__(self): return f"<python module {self.name}>"


class PythonObject:
    """A Python object returned from FFI."""
    def __init__(self, obj):
        self.obj = obj

    def __repr__(self): return repr(self.obj)


# ── Lazy generator ────────────────────────────────────────────────────────────

class LedgeLazyGenerator:
    """
    Truly lazy generator — values produced on demand.
    Supports infinite sequences without hanging.
    """
    def __init__(self, fn, env, interp):
        self._fn      = fn
        self._env     = env
        self._interp  = interp
        self._cache   = []
        self._exhausted = False
        self._gen     = None

    def _ensure_gen(self):
        if self._gen is None:
            self._gen = self._interp._make_python_gen(self._fn, self._env)

    def _advance_to(self, n):
        self._ensure_gen()
        while len(self._cache) < n and not self._exhausted:
            try:
                self._cache.append(next(self._gen))
            except StopIteration:
                self._exhausted = True
                break

    def collect(self):
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

    def __len__(self):    return len(self.collect())
    def __repr__(self):   return "<generator>"

    def __getitem__(self, idx):
        if isinstance(idx, int):
            self._advance_to(idx + 1)
            return self._cache[idx] if idx < len(self._cache) else NOTHING
        return NOTHING


# ── Environment ───────────────────────────────────────────────────────────────

class Env:
    """
    Lexical scope environment — linked chain of frames.
    Implements define (create), assign (mutate), and lookup.
    """
    def __init__(self, parent=None, name="<module>"):
        self._v:     dict = {}   # name -> value
        self._types: dict = {}   # name -> type hint
        self.parent  = parent
        self.name    = name

    def get(self, name: str):
        if name in self._v:
            return self._v[name]
        if self.parent:
            return self.parent.get(name)
        suggestions = self._suggest(name)
        msg = f"\'{name}\' is not defined"
        if suggestions:
            msg += f" — did you mean: {', '.join(repr(s) for s in suggestions[:3])}?"
        raise LedgeError(msg)

    def _suggest(self, name: str):
        """Edit-distance suggestions for undefined variable names."""
        all_names = list(self._v.keys())
        if self.parent:
            all_names += list(self.parent._v.keys())

        def edit_dist(a, b):
            if len(a) > len(b): a, b = b, a
            row = list(range(len(a) + 1))
            for c in b:
                row2 = [row[0] + 1]
                for j, d in enumerate(a):
                    row2.append(min(row[j] + (c != d), row2[-1] + 1, row[j+1] + 1))
                row = row2
            return row[-1]

        close = [(edit_dist(name, n), n) for n in all_names if n != name]
        close.sort()
        return [n for d, n in close if d <= 2]

    def set(self, name: str, value, type_hint=None):
        self._v[name] = value
        if type_hint:
            self._types[name] = type_hint

    def assign(self, name: str, value):
        """Mutate an existing binding. Walks the scope chain."""
        if name in self._v:
            if name in self._types:
                hint = self._types[name]
                if not _check_type_compat(value, hint):
                    raise LedgeError(
                        f"Type error: \'{name}\' is declared as {hint}, "
                        f"cannot assign {_type_of(value)}. "
                        f"Use \'define {name} as ...' to redefine with a new type."
                    )
            self._v[name] = value
            return
        if self.parent:
            self.parent.assign(name, value)
            return
        raise LedgeError(
            f"\'{name}\' is not defined. "
            f"Use \'define {name} as ...\' to create it first."
        )

    def child(self, name="<block>") -> 'Env':
        return Env(parent=self, name=name)



# ── Value helpers ─────────────────────────────────────────────────────────────

def _repr(v) -> str:
    """Convert any Ledge value to its canonical string representation."""
    if getattr(v, '_is_ai_derived', False): return _repr(v.value)
    if v is NOTHING:   return "nothing"
    if v is True:      return "true"
    if v is False:     return "false"
    if isinstance(v, float) and v == int(v) and not math.isinf(v):
        return str(int(v))
    if isinstance(v, (int, float)):  return str(v)
    if isinstance(v, str):           return v
    if isinstance(v, LedgeLazyGenerator): return repr(v)
    if isinstance(v, LedgeList):
        return "[" + ", ".join(_repr(x) for x in v) + "]"
    if isinstance(v, LedgeMap):
        parts = ", ".join(f'"{k}": {_repr(w)}' for k, w in v.items())
        return "{" + parts + "}"
    if isinstance(v, (LedgeInstance, LedgeFunction, LedgeType)):
        return repr(v)
    if isinstance(v, PythonModule):  return repr(v)
    if isinstance(v, PythonObject):  return repr(v.obj)
    # AI types handled by their own __repr__
    return str(v)


def _truthy(v) -> bool:
    """Ledge truthiness — strictly defined."""
    if getattr(v, '_is_ai_derived', False): return _truthy(v.value)
    if v is NOTHING or v is False:    return False
    if isinstance(v, bool):           return v
    if isinstance(v, (int, float)):   return v != 0
    if isinstance(v, (str, list, dict)): return len(v) > 0
    return True


def _eq(a, b) -> bool:
    """Ledge equality — strict: true≠1, false≠0, nothing≠null."""
    if getattr(a, '_is_ai_derived', False): a = a.value
    if getattr(b, '_is_ai_derived', False): b = b.value
    if a is NOTHING and b is NOTHING:  return True
    if a is NOTHING or b is NOTHING:   return False
    # Strict boolean/number separation
    if isinstance(a, bool) and not isinstance(b, bool): return False
    if isinstance(b, bool) and not isinstance(a, bool): return False
    if isinstance(a, bool) and isinstance(b, bool):     return a is b
    if isinstance(a, LedgeLazyGenerator): a = a.collect()
    if isinstance(b, LedgeLazyGenerator): b = b.collect()
    return a == b


def _type_of(v) -> str:
    """Return the Ledge type name of a value."""
    if getattr(v, '_is_ai_derived', False): return _type_of(v.value)
    if v is NOTHING:               return "nothing"
    if isinstance(v, bool):        return "truth"
    if isinstance(v, (int, float)): return "number"
    if isinstance(v, str):         return "text"
    if isinstance(v, (LedgeList, LedgeLazyGenerator)): return "list"
    if isinstance(v, LedgeMap):    return "map"
    if isinstance(v, LedgeFunction): return "function"
    if isinstance(v, LedgeInstance): return v.type_name
    if isinstance(v, PythonModule):  return "python_module"
    if isinstance(v, PythonObject):  return "python_object"
    # Deferred check for AI types to avoid circular import
    type_name = type(v).__name__
    if type_name == "Uncertain":
        # Use declared_type if value is NOTHING (no backend case)
        inner = getattr(v, 'declared_type', None)
        if inner is None or v.value is not NOTHING:
            inner = _type_of(v.value)
        return f"uncertain[{inner}]"
    if type_name == "LedgeStream": return "stream"
    if type_name == "LedgePipeline": return "pipeline"
    if type_name == "MCPTool":     return "mcp_tool"
    if type_name == "AuditTrail":  return "audit_trail"
    return "unknown"


def _check_type_compat(val, hint: str) -> bool:
    """Check if a value is compatible with a type annotation."""
    if hint in ("any", "nothing", "unknown"): return True
    if val is NOTHING: return True  # nothing is always compatible
    checks = {
        "text":   lambda v: isinstance(v, str),
        "number": lambda v: isinstance(v, (int, float)) and not isinstance(v, bool),
        "truth":  lambda v: isinstance(v, bool),
        "list":   lambda v: isinstance(v, (LedgeList, LedgeLazyGenerator)),
        "map":    lambda v: isinstance(v, LedgeMap),
    }
    check_fn = checks.get(hint)
    return check_fn(val) if check_fn else True


def _py_to_ledge(v) -> Any:
    """Convert a Python value to its Ledge equivalent."""
    if v is None:                           return NOTHING
    if isinstance(v, bool):                 return v
    if isinstance(v, dict):
        return LedgeMap({str(k): _py_to_ledge(w) for k, w in v.items()})
    if isinstance(v, (list, tuple)):
        return LedgeList([_py_to_ledge(x) for x in v])
    if isinstance(v, (int, float, str)):    return v
    return PythonObject(v)


def _ledge_to_py(v) -> Any:
    """Convert a Ledge value to its Python equivalent."""
    if getattr(v, '_is_ai_derived', False): return _ledge_to_py(v.value)
    if v is NOTHING:                        return None
    if isinstance(v, LedgeMap):
        return {k: _ledge_to_py(w) for k, w in v.items()}
    if isinstance(v, LedgeLazyGenerator):
        return [_ledge_to_py(x) for x in v]
    if isinstance(v, LedgeList):
        return [_ledge_to_py(x) for x in v]
    if isinstance(v, LedgeInstance):
        return {k: _ledge_to_py(w) for k, w in v.fields.items()}
    if isinstance(v, PythonObject):         return v.obj
    # AI types
    type_name = type(v).__name__
    if type_name == "Uncertain":
        return {"value": _ledge_to_py(v.value), "confidence": v.confidence}
    return v
