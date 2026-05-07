"""
ledge_ai_utils — AI pipeline utilities for Ledge
=================================================
Utilities for building robust AI pipelines with proper uncertainty handling.

Usage:
    import "python:ledge_ai_utils" as ai
    define pipeline as ai["pipeline"](steps=["extract", "classify", "summarize"])
"""

LEDGE_PACKAGE = "ledge_ai_utils"
VERSION = "1.0.0"

def confidence_band(confidence):
    """Categorize confidence into a human-readable band."""
    if confidence >= 0.95: return "very_high"
    if confidence >= 0.80: return "high"
    if confidence >= 0.60: return "medium"
    if confidence >= 0.40: return "low"
    return "very_low"

def batch_process(items, max_batch_size=10):
    """Split items into batches for AI processing."""
    return [items[i:i+max_batch_size] for i in range(0, len(items), max_batch_size)]

def aggregate_confidence(confidences):
    """Aggregate multiple confidence scores."""
    if not confidences: return 0.0
    return sum(confidences) / len(confidences)

def make_prompt(template, **kwargs):
    """Fill a prompt template with values."""
    result = template
    for key, value in kwargs.items():
        result = result.replace("{" + key + "}", str(value))
    return result

def retry_with_fallback(primary_fn, fallback_fn, min_confidence=0.7):
    """Try primary_fn, fall back to fallback_fn if confidence too low."""
    def wrapper(*args, **kwargs):
        result = primary_fn(*args, **kwargs)
        if isinstance(result, dict) and result.get("confidence", 0) >= min_confidence:
            return result
        return fallback_fn(*args, **kwargs)
    return wrapper
