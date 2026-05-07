"""
ledge_data — Data pipeline utilities for Ledge
===============================================
CSV, JSON, and tabular data processing.
Designed for AI data pipelines.

Usage:
    import "python:ledge_data" as data
    define rows as data["from_csv"]("dataset.csv")
    for each row in rows:
        define result as classify(row["text"]) using ["positive","negative"]
"""
import json, csv, io

LEDGE_PACKAGE = "ledge_data"
VERSION = "1.0.0"

def from_json(text):
    """Parse JSON string into Ledge-compatible structure."""
    return json.loads(text)

def to_json(value):
    """Serialize to JSON string."""
    return json.dumps(value, indent=2, default=str)

def from_csv(text, delimiter=","):
    """Parse CSV text into list of dicts."""
    reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
    return list(reader)

def group_by(items, key):
    """Group list of dicts by a key."""
    groups = {}
    for item in items:
        k = item.get(key, "unknown")
        groups.setdefault(k, []).append(item)
    return groups

def pluck(items, key):
    """Extract a field from each item in a list."""
    return [item.get(key) for item in items]

def flatten(nested, depth=1):
    """Flatten nested list."""
    if depth == 0: return nested
    result = []
    for item in nested:
        if isinstance(item, list):
            result.extend(flatten(item, depth-1))
        else:
            result.append(item)
    return result
