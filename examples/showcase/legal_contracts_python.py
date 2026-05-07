"""
Legal contracts — Python version without Ledge guarantees.
Demonstrates how low confidence can go unnoticed.
"""


def extract_clauses_python(contract, ai_fn):
    """Python version: can process clauses without checking confidence."""
    result = ai_fn(contract["text"])

    # PROBLEM 1: if confidence is low, the code ignores it and processes anyway
    clauses = result.get("clauses", [])
    return clauses


def extract_clauses_python_with_bug(contract, ai_fn):
    """
    Real bug: low confidence is not detected because the dict may lack the key.
    """
    result = ai_fn(contract["text"])
    if result is None:
        return []

    # PROBLEM 2: typo in the key — confidence silently ignored
    conf = result.get("confience", 1.0)  # typo → always 1.0
    if conf < 0.8:
        return []  # never executes due to the typo

    # Clauses processed without review even though model was not confident
    return result.get("clauses", [])


def extract_clauses_python_defensive(contract, ai_fn, min_conf=0.8):
    """
    Defensive version — the closest to Ledge that can be done in Python.
    But: depends on developer discipline, not the language.
    """
    result = ai_fn(contract["text"])
    if result is None:
        return {"clauses": [], "for_review": True, "reason": "backend_failed"}

    conf = result.get("confidence")
    if conf is None:
        # Backend did not return confidence — what to do?
        # In Python: depends on convention. In Ledge: impossible, Uncertain always has confidence.
        return {"clauses": [], "for_review": True, "reason": "no_confidence"}

    if conf < min_conf:
        return {"clauses": [], "for_review": True, "reason": f"low_confidence_{conf}"}

    return {
        "clauses":    result.get("clauses", []),
        "for_review": False,
    }


# Contrast:
# - In Ledge: analyze() ALWAYS returns Uncertain[T].
#   confidence_of() can never be None. is_confident is a property of the type.
# - In Python: confidence is a dict field. It can be absent, misspelled,
#   or ignored without the compiler or runtime detecting it.
# - The "defensive" Python version requires ~3x more code to approximate
#   what Ledge gives for free, and can still fail (the typo line).
