"""
ledge_datetime — Date/time utilities for Ledge
"""
from datetime import datetime, timedelta

LEDGE_PACKAGE = "ledge_datetime"
VERSION = "1.0.0"

def now(): return datetime.now().isoformat()
def today(): return datetime.now().date().isoformat()
def timestamp(): 
    import time; return time.time()
def parse(s): return datetime.fromisoformat(str(s)).isoformat()
def format_date(s, fmt="%Y-%m-%d"):
    return datetime.fromisoformat(str(s)).strftime(fmt)
def days_between(a, b):
    da = datetime.fromisoformat(str(a))
    db = datetime.fromisoformat(str(b))
    return abs((db - da).days)
def add_days(s, n):
    d = datetime.fromisoformat(str(s))
    return (d + timedelta(days=int(n))).isoformat()
def is_before(a, b):
    return datetime.fromisoformat(str(a)) < datetime.fromisoformat(str(b))
