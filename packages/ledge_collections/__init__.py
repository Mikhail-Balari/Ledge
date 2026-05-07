"""
ledge_collections — Advanced collection utilities for Ledge
"""

LEDGE_PACKAGE = "ledge_collections"
VERSION = "1.0.0"

def unique(lst): 
    seen, result = set(), []
    for item in lst:
        k = str(item)
        if k not in seen: seen.add(k); result.append(item)
    return result

def flatten(lst, depth=1):
    result = []
    for item in lst:
        if isinstance(item, list) and depth > 0: result.extend(flatten(item, depth-1))
        else: result.append(item)
    return result

def zip_lists(*lists): return [list(group) for group in zip(*lists)]
def window(lst, size): return [lst[i:i+size] for i in range(len(lst)-size+1)]
def chunks(lst, size): return [lst[i:i+size] for i in range(0, len(lst), size)]
def first(lst): return lst[0] if lst else None
def last(lst): return lst[-1] if lst else None
def nth(lst, n): 
    n = int(n)
    return lst[n] if 0 <= n < len(lst) else None
def count_if(lst, fn): return sum(1 for x in lst if fn(x))
def index_of(lst, val): 
    try: return lst.index(val)
    except: return -1
def rotate(lst, n):
    if not lst: return lst
    n = int(n) % len(lst)
    return lst[n:] + lst[:n]
