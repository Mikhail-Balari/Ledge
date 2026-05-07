"""
ledge_validation — Input validation for Ledge AI pipelines
"""
import re

LEDGE_PACKAGE = "ledge_validation"
VERSION = "1.0.0"

def is_email(s): return bool(re.match(r"[^@]+@[^@]+\.[^@]+", str(s)))
def is_url(s): return str(s).startswith(("http://","https://"))
def is_numeric(s):
    try: float(s); return True
    except: return False
def is_phone(s): return bool(re.match(r"^[+]?[\d\s\-()]{7,}$", str(s)))
def min_length(s, n): return len(str(s)) >= int(n)
def max_length(s, n): return len(str(s)) <= int(n)
def matches(s, pattern): return bool(re.match(pattern, str(s)))
def in_range(n, lo, hi): return float(lo) <= float(n) <= float(hi)
def not_empty(s): return len(str(s).strip()) > 0
def is_json(s):
    import json
    try: json.loads(str(s)); return True
    except: return False
