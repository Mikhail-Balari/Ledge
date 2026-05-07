"""
ledge_strings — Advanced string utilities for Ledge AI pipelines
"""
import re, unicodedata

LEDGE_PACKAGE = "ledge_strings"
VERSION = "1.0.0"

def normalize(s):
    return unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode()

def slugify(s):
    s = normalize(s).lower()
    s = re.sub(r"[^\w\s-]", "", s)
    return re.sub(r"[-\s]+", "-", s).strip("-")

def camel_to_snake(s):
    return re.sub(r"(?<!^)(?=[A-Z])", "_", str(s)).lower()

def snake_to_camel(s):
    parts = str(s).split("_")
    return parts[0] + "".join(p.capitalize() for p in parts[1:])

def truncate_words(s, n):
    words = str(s).split()
    if len(words) <= n: return s
    return " ".join(words[:n]) + "..."

def count_words(s): return len(str(s).split())
def contains(s, sub): return str(sub) in str(s)
def starts_with(s, prefix): return str(s).startswith(str(prefix))
def ends_with(s, suffix): return str(s).endswith(str(suffix))
def strip_html(s): return re.sub(r"<[^>]+>", "", str(s))
def repeat_str(s, n): return str(s) * int(n)
def pad_left(s, width, char=" "): return str(s).rjust(int(width), str(char)[0])
def pad_right(s, width, char=" "): return str(s).ljust(int(width), str(char)[0])
