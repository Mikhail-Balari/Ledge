# Run from repo root: python demo_guarantee2.py
import sys; sys.path.insert(0, '.')
from ledge_lang.typechecker import check_types

# ── Unsafe code ───────────────────────────────────────────────────────────────
unsafe = '''
define r as analyze("contract with ambiguous terms") using legal
show r
'''
issues = check_types(unsafe)
errors = [i for i in issues if i.is_error]
print(f"Unsafe code ('show r' without guard):")
print(f"  Errors detected: {len(errors)}")
print(f"  Message: {errors[0].message[:80]}")
print(f"  Suggestion: {errors[0].suggestion.splitlines()[0]}")

# ── Safe code ─────────────────────────────────────────────────────────────────
safe = '''
define r as analyze("contract with ambiguous terms") using legal
if confidence_of(r) >= 0.85:
    show value_of(r)
else:
    show "ESCALATE TO HUMAN REVIEW"
'''
issues2 = check_types(safe)
errors2 = [i for i in issues2 if i.is_error]
print(f"\nSafe code (explicit confidence guard):")
print(f"  Errors detected: {len(errors2)}")
print("\nProperty checked: typechecker blocks unsafe use at analysis time.")
