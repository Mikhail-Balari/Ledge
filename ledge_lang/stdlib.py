"""
Ledge Standard Library
Modules available via: import "module_name" as alias
"""

import math
import time
import json
import re
import os
import urllib.request
import urllib.error
from .interpreter import (
    NOTHING, LedgeList, LedgeMap, LedgeInstance, LedgeError,
    _repr, _truthy, _py_to_ledge, _ledge_to_py, _Native
)


def _n(name, fn):
    return _Native(name, fn)


# ── time ──────────────────────────────────────────────────────────────────────

def _make_time():
    def now(a, k, u):
        return time.time()

    def sleep(a, k, u):
        if not a or not isinstance(a[0], (int, float)):
            raise LedgeError("sleep requires a number (seconds)")
        time.sleep(a[0])
        return NOTHING

    def format_time(a, k, u):
        ts = a[0] if a else time.time()
        fmt = a[1] if len(a) > 1 else "%Y-%m-%d %H:%M:%S"
        return time.strftime(fmt, time.localtime(ts))

    def timestamp(a, k, u):
        return int(time.time())

    return LedgeMap({
        "now":       _n("now", now),
        "sleep":     _n("sleep", sleep),
        "format":    _n("format", format_time),
        "timestamp": _n("timestamp", timestamp),
    })


# ── file ──────────────────────────────────────────────────────────────────────

def _make_file():
    def read(a, k, u):
        if not a or not isinstance(a[0], str):
            raise LedgeError("file.read requires a path")
        path = a[0]
        encoding = a[1] if len(a) > 1 else "utf-8"
        try:
            with open(path, encoding=encoding) as f:
                return f.read()
        except FileNotFoundError:
            return NOTHING
        except Exception as e:
            raise LedgeError(f"Cannot read '{path}': {e}")

    def write(a, k, u):
        if len(a) < 2:
            raise LedgeError("file.write requires a path and content")
        path, content = a[0], _repr(a[1])
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            return True
        except Exception as e:
            raise LedgeError(f"Cannot write '{path}': {e}")

    def append_file(a, k, u):
        if len(a) < 2:
            raise LedgeError("file.append requires a path and content")
        path, content = a[0], _repr(a[1])
        try:
            with open(path, "a", encoding="utf-8") as f:
                f.write(content)
            return True
        except Exception as e:
            raise LedgeError(f"Cannot append to '{path}': {e}")

    def exists(a, k, u):
        return os.path.exists(a[0]) if a else False

    def delete(a, k, u):
        if not a:
            raise LedgeError("file.delete requires a path")
        try:
            os.remove(a[0])
            return True
        except FileNotFoundError:
            return False
        except Exception as e:
            raise LedgeError(f"Cannot delete '{a[0]}': {e}")

    def list_dir(a, k, u):
        path = a[0] if a else "."
        try:
            return LedgeList(os.listdir(path))
        except Exception as e:
            raise LedgeError(f"Cannot list '{path}': {e}")

    def lines(a, k, u):
        if not a:
            raise LedgeError("file.lines requires a path")
        content = read(a, k, u)
        if content is NOTHING:
            return NOTHING
        return LedgeList(content.split("\n"))

    def read_json(a, k, u):
        content = read(a, k, u)
        if content is NOTHING:
            return NOTHING
        try:
            return _py_to_ledge(json.loads(content))
        except json.JSONDecodeError as e:
            raise LedgeError(f"Invalid JSON in '{a[0]}': {e}")

    def write_json(a, k, u):
        if len(a) < 2:
            raise LedgeError("file.write_json requires a path and data")
        path = a[0]
        data = json.dumps(_ledge_to_py(a[1]), indent=2, ensure_ascii=False)
        return write([path, data], k, u)

    return LedgeMap({
        "read":       _n("read", read),
        "write":      _n("write", write),
        "append":     _n("append", append_file),
        "exists":     _n("exists", exists),
        "delete":     _n("delete", delete),
        "list":       _n("list", list_dir),
        "lines":      _n("lines", lines),
        "read_json":  _n("read_json", read_json),
        "write_json": _n("write_json", write_json),
    })


# ── http ──────────────────────────────────────────────────────────────────────

def _make_http():
    def _do_request(url, method, body=None, headers=None):
        try:
            data = body.encode("utf-8") if body else None
            req = urllib.request.Request(url, data=data, method=method)
            req.add_header("User-Agent", "Ledge/0.1")
            req.add_header("Accept", "application/json, text/plain, */*")
            if body:
                req.add_header("Content-Type", "application/json")
            if headers and isinstance(headers, LedgeMap):
                for k, v in headers.items():
                    req.add_header(k, _repr(v))
            with urllib.request.urlopen(req, timeout=10) as resp:
                content = resp.read().decode("utf-8", errors="replace")
                status = resp.status
                resp_headers = dict(resp.headers)
                result = LedgeMap({
                    "status": status,
                    "ok": status < 400,
                    "body": content,
                    "headers": _py_to_ledge(resp_headers),
                })
                # Auto-parse JSON
                try:
                    result["data"] = _py_to_ledge(json.loads(content))
                except Exception:
                    result["data"] = NOTHING
                return result
        except urllib.error.HTTPError as e:
            return LedgeMap({
                "status": e.code,
                "ok": False,
                "body": str(e.reason),
                "headers": LedgeMap(),
                "data": NOTHING,
            })
        except Exception as e:
            raise LedgeError(f"HTTP request failed: {e}")

    def get(a, k, u):
        if not a:
            raise LedgeError("http.get requires a URL")
        headers = a[1] if len(a) > 1 else None
        return _do_request(a[0], "GET", headers=headers)

    def post(a, k, u):
        if not a:
            raise LedgeError("http.post requires a URL")
        url = a[0]
        body = json.dumps(_ledge_to_py(a[1])) if len(a) > 1 else None
        headers = a[2] if len(a) > 2 else None
        return _do_request(url, "POST", body=body, headers=headers)

    def put(a, k, u):
        if not a:
            raise LedgeError("http.put requires a URL")
        url = a[0]
        body = json.dumps(_ledge_to_py(a[1])) if len(a) > 1 else None
        return _do_request(url, "PUT", body=body)

    def delete(a, k, u):
        if not a:
            raise LedgeError("http.delete requires a URL")
        return _do_request(a[0], "DELETE")

    def fetch(a, k, u):
        """Convenience: GET and return body or parsed JSON."""
        result = get(a, k, u)
        if not result["ok"]:
            return NOTHING
        return result.get("data", NOTHING) or result.get("body", NOTHING)

    return LedgeMap({
        "get":    _n("get", get),
        "post":   _n("post", post),
        "put":    _n("put", put),
        "delete": _n("delete", delete),
        "fetch":  _n("fetch", fetch),
    })


# ── regex ─────────────────────────────────────────────────────────────────────

def _make_regex():
    def match(a, k, u):
        if len(a) < 2:
            raise LedgeError("regex.match requires pattern and text")
        pattern, text = a[0], a[1]
        m = re.match(pattern, text)
        if not m:
            return NOTHING
        return LedgeMap({
            "matched": m.group(0),
            "groups": LedgeList(m.groups()),
            "start": m.start(),
            "end": m.end(),
        })

    def search(a, k, u):
        if len(a) < 2:
            raise LedgeError("regex.search requires pattern and text")
        pattern, text = a[0], a[1]
        m = re.search(pattern, text)
        if not m:
            return NOTHING
        return LedgeMap({
            "matched": m.group(0),
            "groups": LedgeList(m.groups()),
            "start": m.start(),
            "end": m.end(),
        })

    def find_all(a, k, u):
        if len(a) < 2:
            raise LedgeError("regex.find_all requires pattern and text")
        pattern, text = a[0], a[1]
        return LedgeList(re.findall(pattern, text))

    def replace(a, k, u):
        if len(a) < 3:
            raise LedgeError("regex.replace requires pattern, replacement, and text")
        pattern, replacement, text = a[0], a[1], a[2]
        return re.sub(pattern, replacement, text)

    def split(a, k, u):
        if len(a) < 2:
            raise LedgeError("regex.split requires pattern and text")
        return LedgeList(re.split(a[0], a[1]))

    def test(a, k, u):
        if len(a) < 2:
            raise LedgeError("regex.test requires pattern and text")
        return bool(re.search(a[0], a[1]))

    return LedgeMap({
        "match":    _n("match", match),
        "search":   _n("search", search),
        "find_all": _n("find_all", find_all),
        "replace":  _n("replace", replace),
        "split":    _n("split", split),
        "test":     _n("test", test),
    })


# ── collections ───────────────────────────────────────────────────────────────

def _make_collections():
    def group_by(a, k, u):
        """group_by(list, key_fn) -> map of key -> list"""
        if len(a) < 2:
            raise LedgeError("group_by requires a list and a key function")
        lst, fn = a[0], a[1]
        from .interpreter import Interpreter
        result = LedgeMap()
        for item in lst:
            if callable(fn):
                key = _repr(fn([item], {}, None))
            else:
                key = _repr(item)
            if key not in result:
                result[key] = LedgeList()
            result[key].append(item)
        return result

    def count_by(a, k, u):
        """count_by(list) -> map of value -> count"""
        if not a:
            raise LedgeError("count_by requires a list")
        result = LedgeMap()
        for item in a[0]:
            key = _repr(item)
            result[key] = result.get(key, 0) + 1
        return result

    def unique(a, k, u):
        if not a:
            raise LedgeError("unique requires a list")
        seen = set()
        result = LedgeList()
        for item in a[0]:
            key = _repr(item)
            if key not in seen:
                seen.add(key)
                result.append(item)
        return result

    def flatten(a, k, u):
        if not a:
            raise LedgeError("flatten requires a list")
        result = LedgeList()
        for item in a[0]:
            if isinstance(item, LedgeList):
                result.extend(item)
            else:
                result.append(item)
        return result

    def zip_lists(a, k, u):
        if len(a) < 2:
            raise LedgeError("zip requires two lists")
        return LedgeList(
            LedgeList([x, y]) for x, y in zip(a[0], a[1])
        )

    def take(a, k, u):
        if len(a) < 2:
            raise LedgeError("take requires a list and count")
        return LedgeList(a[0][:int(a[1])])

    def drop(a, k, u):
        if len(a) < 2:
            raise LedgeError("drop requires a list and count")
        return LedgeList(a[0][int(a[1]):])

    def reduce(a, k, u):
        if len(a) < 3:
            raise LedgeError("reduce requires a list, function, and initial value")
        lst, fn, acc = a[0], a[1], a[2]
        for item in lst:
            acc = fn([acc, item], {}, None)
        return acc

    def chunk(a, k, u):
        if len(a) < 2:
            raise LedgeError("chunk requires a list and size")
        lst, size = a[0], int(a[1])
        result = LedgeList()
        for i in range(0, len(lst), size):
            result.append(LedgeList(lst[i:i+size]))
        return result

    def frequencies(a, k, u):
        return count_by(a, k, u)

    def intersection(a, k, u):
        if len(a) < 2:
            raise LedgeError("intersection requires two lists")
        s = set(_repr(x) for x in a[1])
        return LedgeList(x for x in a[0] if _repr(x) in s)

    def difference(a, k, u):
        if len(a) < 2:
            raise LedgeError("difference requires two lists")
        s = set(_repr(x) for x in a[1])
        return LedgeList(x for x in a[0] if _repr(x) not in s)

    return LedgeMap({
        "group_by":     _n("group_by", group_by),
        "count_by":     _n("count_by", count_by),
        "unique":       _n("unique", unique),
        "flatten":      _n("flatten", flatten),
        "zip":          _n("zip", zip_lists),
        "take":         _n("take", take),
        "drop":         _n("drop", drop),
        "reduce":       _n("reduce", reduce),
        "chunk":        _n("chunk", chunk),
        "frequencies":  _n("frequencies", frequencies),
        "intersection": _n("intersection", intersection),
        "difference":   _n("difference", difference),
    })


# ── env ───────────────────────────────────────────────────────────────────────

def _make_env():
    def get_env(a, k, u):
        if not a:
            raise LedgeError("env.get requires a variable name")
        val = os.environ.get(a[0])
        if val is None:
            return a[1] if len(a) > 1 else NOTHING
        return val

    def set_env(a, k, u):
        if len(a) < 2:
            raise LedgeError("env.set requires a name and value")
        os.environ[a[0]] = _repr(a[1])
        return True

    def all_env(a, k, u):
        return _py_to_ledge(dict(os.environ))

    return LedgeMap({
        "get": _n("get", get_env),
        "set": _n("set", set_env),
        "all": _n("all", all_env),
    })


# ── math extended ─────────────────────────────────────────────────────────────

def _make_math():
    return LedgeMap({
        "pi":      math.pi,
        "e":       math.e,
        "tau":     math.tau,
        "inf":     math.inf,
        "sqrt":    _n("sqrt",    lambda a,k,u: math.sqrt(a[0]) if a[0] >= 0 else NOTHING),
        "cbrt":    _n("cbrt",    lambda a,k,u: a[0] ** (1/3) if a[0] >= 0 else -((-a[0]) ** (1/3))),
        "sin":     _n("sin",     lambda a,k,u: math.sin(a[0])),
        "cos":     _n("cos",     lambda a,k,u: math.cos(a[0])),
        "tan":     _n("tan",     lambda a,k,u: math.tan(a[0])),
        "asin":    _n("asin",    lambda a,k,u: math.asin(a[0])),
        "acos":    _n("acos",    lambda a,k,u: math.acos(a[0])),
        "atan":    _n("atan",    lambda a,k,u: math.atan(a[0])),
        "atan2":   _n("atan2",   lambda a,k,u: math.atan2(a[0], a[1])),
        "log":     _n("log",     lambda a,k,u: math.log(a[0], a[1]) if len(a)>1 else math.log(a[0])),
        "log2":    _n("log2",    lambda a,k,u: math.log2(a[0])),
        "log10":   _n("log10",   lambda a,k,u: math.log10(a[0])),
        "exp":     _n("exp",     lambda a,k,u: math.exp(a[0])),
        "gcd":     _n("gcd",     lambda a,k,u: math.gcd(int(a[0]), int(a[1]))),
        "lcm":     _n("lcm",     lambda a,k,u: abs(int(a[0]) * int(a[1])) // math.gcd(int(a[0]), int(a[1]))),
        "clamp":   _n("clamp",   lambda a,k,u: max(a[1], min(a[2], a[0]))),
        "lerp":    _n("lerp",    lambda a,k,u: a[0] + (a[1] - a[0]) * a[2]),
        "degrees": _n("degrees", lambda a,k,u: math.degrees(a[0])),
        "radians": _n("radians", lambda a,k,u: math.radians(a[0])),
        "is_nan":  _n("is_nan",  lambda a,k,u: math.isnan(a[0])),
        "is_inf":  _n("is_inf",  lambda a,k,u: math.isinf(a[0])),
    })


# ── text extended ─────────────────────────────────────────────────────────────

def _make_text():
    def pad_left(a, k, u):
        s, width = _repr(a[0]), int(a[1])
        char = a[2] if len(a) > 2 else " "
        return s.rjust(width, char)

    def pad_right(a, k, u):
        s, width = _repr(a[0]), int(a[1])
        char = a[2] if len(a) > 2 else " "
        return s.ljust(width, char)

    def center(a, k, u):
        s, width = _repr(a[0]), int(a[1])
        return s.center(width)

    def repeat_str(a, k, u):
        return _repr(a[0]) * int(a[1])

    def count_occurrences(a, k, u):
        return _repr(a[0]).count(_repr(a[1]))

    def index_of(a, k, u):
        idx = _repr(a[0]).find(_repr(a[1]))
        return idx if idx >= 0 else NOTHING

    def is_number(a, k, u):
        try:
            float(_repr(a[0]))
            return True
        except ValueError:
            return False

    def is_empty(a, k, u):
        v = a[0]
        if v is NOTHING: return True
        if isinstance(v, str): return len(v.strip()) == 0
        if isinstance(v, (list, dict)): return len(v) == 0
        return False

    def lines(a, k, u):
        return LedgeList(_repr(a[0]).splitlines())

    def words(a, k, u):
        return LedgeList(_repr(a[0]).split())

    def title_case(a, k, u):
        return _repr(a[0]).title()

    def snake_to_camel(a, k, u):
        parts = _repr(a[0]).split("_")
        return parts[0] + "".join(p.capitalize() for p in parts[1:])

    return LedgeMap({
        "pad_left":    _n("pad_left", pad_left),
        "pad_right":   _n("pad_right", pad_right),
        "center":      _n("center", center),
        "repeat":      _n("repeat", repeat_str),
        "count":       _n("count", count_occurrences),
        "index_of":    _n("index_of", index_of),
        "is_number":   _n("is_number", is_number),
        "is_empty":    _n("is_empty", is_empty),
        "lines":       _n("lines", lines),
        "words":       _n("words", words),
        "title_case":  _n("title_case", title_case),
        "to_camel":    _n("to_camel", snake_to_camel),
        "upper":       _n("upper",  lambda a,k,u: _repr(a[0]).upper()),
        "lower":       _n("lower",  lambda a,k,u: _repr(a[0]).lower()),
        "trim":        _n("trim",   lambda a,k,u: _repr(a[0]).strip()),
        "split":       _n("split",  lambda a,k,u: LedgeList(_repr(a[0]).split(a[1] if len(a)>1 else " "))),
        "join":        _n("join",   lambda a,k,u: (_repr(a[1]) if len(a)>1 else "").join(_repr(x) for x in a[0])),
        "replace":     _n("replace", lambda a,k,u: _repr(a[0]).replace(_repr(a[1]), _repr(a[2]))),
        "contains":    _n("contains", lambda a,k,u: _repr(a[1]) in _repr(a[0])),
        "starts_with": _n("starts_with", lambda a,k,u: _repr(a[0]).startswith(_repr(a[1]))),
        "ends_with":   _n("ends_with",   lambda a,k,u: _repr(a[0]).endswith(_repr(a[1]))),
    })


# ── Registry ──────────────────────────────────────────────────────────────────

STDLIB = {
    "time":        _make_time,
    "file":        _make_file,
    "http":        _make_http,
    "regex":       _make_regex,
    "collections": _make_collections,
    "env":         _make_env,
    "math":        _make_math,
    "text":        _make_text,
}


def load_module(name: str):
    """Load a stdlib module by name. Returns LedgeMap or raises LedgeError."""
    if name not in STDLIB:
        raise LedgeError(f"No module named '{name}' — available: {', '.join(sorted(STDLIB))}")
    return STDLIB[name]()


# ── Memory and execution quotas ────────────────────────────────────────────────
# These are advisory in v1.1 (documented, not hard-enforced)

_EXECUTION_LIMITS = {
    "max_iterations": None,    # None = unlimited
    "max_memory_mb": None,     # None = unlimited
    "max_call_depth": 500,     # Default Python recursion limit / 2
}

def _bi_set_limit(a, k, u):
    """set_limit(name, value) — set an execution limit."""
    if len(a) < 2:
        raise LedgeError("set_limit requires 2 arguments: limit_name, value")
    name = _repr(a[0])
    value = a[1]
    if name not in _EXECUTION_LIMITS:
        raise LedgeError(
            f"Unknown limit: '{name}'. Available: {list(_EXECUTION_LIMITS.keys())}"
        )
    _EXECUTION_LIMITS[name] = None if value is NOTHING else value
    return True

def _bi_get_limit(a, k, u):
    """get_limit(name) → current limit value or nothing."""
    if not a: raise LedgeError("get_limit requires 1 argument")
    name = _repr(a[0])
    return _EXECUTION_LIMITS.get(name, NOTHING)

def _bi_memory_usage(a, k, u):
    """memory_usage() → approximate memory used in MB."""
    import tracemalloc
    if not tracemalloc.is_tracing():
        tracemalloc.start()
    current, _ = tracemalloc.get_traced_memory()
    return round(current / 1024 / 1024, 3)

def _n_lim(name, fn): return _n(name, fn)
_quota_builtins = [
    _n_lim("set_limit", _bi_set_limit),
    _n_lim("get_limit", _bi_get_limit),
    _n_lim("memory_usage", _bi_memory_usage),
]
