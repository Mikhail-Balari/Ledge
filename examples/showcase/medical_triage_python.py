"""
Medical triage — Python version without Ledge guarantees.

Demonstrates the problems that Ledge solves:
1. Confidence silently ignored
2. No automatic audit trail
3. No contract to enforce preconditions
4. No automatic escalation when confidence < threshold
"""

def classify_python(patient, ai_fn):
    """Python version: can fail silently."""
    result = ai_fn(patient["symptoms"])
    # PROBLEM 1: the developer can forget to check confidence
    # result["confidence"] exists but nothing forces it to be checked
    level = result.get("risk_level", "unknown")
    print(f"Patient {patient['id']}: {level}")
    return level


def classify_python_with_bug(patient, ai_fn):
    """Version with the most common bug: uses result even if backend fails."""
    try:
        result = ai_fn(patient["symptoms"])
        # PROBLEM 2: if backend returns None, this returns "unknown"
        # without warning the doctor that AI did not work
        level = result.get("risk_level", "unknown") if result else "unknown"
    except Exception:
        # PROBLEM 3: any exception returns "unknown" silently
        level = "unknown"
    return level


# Manual audit — forgettable, incomplete
_audit_log = []

def classify_python_with_audit(patient, ai_fn):
    """Manual audit trail attempt — fragile."""
    result = ai_fn(patient["symptoms"])
    # PROBLEM 4: the audit is voluntary, not guaranteed
    # If the developer forgets this line, there is no trace
    _audit_log.append({"patient": patient["id"], "result": result})
    level = result.get("risk_level", "unknown")
    return level


# Contrast: what Ledge guarantees that Python does NOT:
# - confidence ALWAYS present in Uncertain[T] (cannot be forgotten)
# - audit trail AUTOMATIC on every call to analyze/classify/generate
# - requires/ensures verified at runtime
# - without backend → confidence=0.0 (not silent "unknown")
