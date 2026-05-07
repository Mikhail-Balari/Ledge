"""
ledge_cache — Caching utilities for AI pipeline results
Avoids redundant AI calls for repeated inputs.
"""
import hashlib, json, time

LEDGE_PACKAGE = "ledge_cache"
VERSION = "1.0.0"

_CACHE = {}

def _key(text, mode=""):
    return hashlib.sha256(f"{text}:{mode}".encode()).hexdigest()[:16]

def get(text, mode=""):
    k = _key(text, mode)
    if k in _CACHE:
        entry = _CACHE[k]
        if entry["ttl"] == 0 or time.time() < entry["expires"]:
            return entry["value"]
    return None

def set(text, mode, value, ttl_seconds=3600):
    k = _key(text, mode)
    _CACHE[k] = {
        "value": value,
        "ttl": ttl_seconds,
        "expires": time.time() + ttl_seconds if ttl_seconds > 0 else 0
    }
    return value

def clear(): _CACHE.clear(); return True
def size(): return len(_CACHE)

def cached_classify(text, labels, classify_fn):
    """Run classify with caching — avoids redundant AI calls."""
    key_str = str(labels)
    cached = get(text, key_str)
    if cached is not None:
        return cached
    result = classify_fn(text, labels)
    set(text, key_str, result)
    return result
