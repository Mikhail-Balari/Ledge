"""
Credit risk analysis - Python version without Ledge's checked patterns.
Demonstrates voluntary explainability and manual audit plumbing.
"""

def evaluate_credit_python(applicant, ai_fn):
    """Python version: explainability is voluntary."""
    income = applicant["income"]
    debt   = applicant["debt"]

    ratio = debt / income if income else 0
    result = ai_fn(applicant["history"])

    # PROBLEM 1: confidence can be completely ignored
    risk_level = result.get("risk", "moderate") if result else "moderate"

    # PROBLEM 2: explainability is ad-hoc, not structured
    # Developer can omit factors, mix units, or not record them
    decision = "approve"
    if ratio > 0.5 or risk_level == "high":
        decision = "reject"
    elif ratio > 0.35 or risk_level == "moderate":
        decision = "review"

    # PROBLEM 3: what if ai_fn returned None?
    # Code continues silently with risk_level="moderate"
    return {"decision": decision}
    # Note: no "factors", no "confidence", no traceability


def evaluate_credit_python_with_bug(applicant, ai_fn):
    """Real bug seen in production: confidence ignored, always approves."""
    result = ai_fn(applicant["history"])
    # This code was written with good intentions but the developer
    # forgot to verify that result is not None before accessing "risk"
    level = result["risk"]  # KeyError if AI does not return "risk"
    if level == "low":
        return "approve"
    # Silently falls through — never reaches "reject"
    # Missing: elif level == "high": return "reject"
    return "approve"  # bug: always approves


# Contrast:
# - In Ledge, `ensures: has(result, "decision") and has(result, "explanation")`
#   checks at runtime that an incomplete result is never returned.
# - In Python, nothing forces the developer to include explainability.
# - In Ledge, the audit trail is automatic; in Python it is opt-in and forgettable.
