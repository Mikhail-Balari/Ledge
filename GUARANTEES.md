# What Ledge guarantees — and what it does not

> Each guarantee comes with code you can copy, paste, and run right now.
> No API keys. No setup. No blind trust.

---

## Guarantee 1: Zero confidence without a backend

Without an AI model connected, all AI operations
(`classify`, `analyze`, `generate`, `ask`, `embed`) return
`confidence=0.0`. Always. Without exception.

The system does not invent answers. It does not guess. It does not act.

**Proof you can run yourself:**

```python
# Run from repo root: python demo_garantia1.py
import sys; sys.path.insert(0, '.')
from ledge_lang import run

cases = [
    ('classify', 'define r as classify("chest pain") using ["urgent","routine"]\nshow confidence_of(r)'),
    ('analyze',  'define r as analyze("contract with ambiguous terms") using legal\nshow confidence_of(r)'),
    ('generate', 'define r as generate("write a summary") using model\nshow confidence_of(r)'),
]

for name, code in cases:
    lines, _ = run(code, output_fn=lambda x: None)
    conf = lines[0]
    print(f"{name:10s} without backend → confidence = {conf}")
    assert conf == '0', f"FAILED: expected 0, got {conf}"

print("\nGuarantee verified: without backend, confidence = 0 in all cases.")
```

**Expected output:**
```
classify   without backend → confidence = 0
analyze    without backend → confidence = 0
generate   without backend → confidence = 0

Guarantee verified: without backend, confidence = 0 in all cases.
```

**Why it matters:** A system that returns `confidence=0.5` when there is no model
is inventing certainty. Ledge does not do that.

---

## Guarantee 2: Unsafe use of AI results = error at analysis time

If you use an AI result without verifying confidence first,
the Ledge typechecker detects it **before running the program**.

Not a warning. Not a lint hint. An error that blocks execution.

**Proof you can run yourself:**

```python
# Run from repo root: python demo_garantia2.py
import sys; sys.path.insert(0, '.')
from ledge_lang.typechecker import check_types

# ── Unsafe code ──────────────────────────────────────────────────────────────
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

# ── Safe code ────────────────────────────────────────────────────────────────
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
print("\nGuarantee verified: typechecker blocks unsafe use at analysis time.")
```

**Expected output:**
```
Unsafe code ('show r' without guard):
  Errors detected: 1
  Message: Unsafe use of Uncertain value 'r' in 'show' — confidence was never verified.
  Suggestion: show value_of(r)                       -- extract value

Safe code (explicit confidence guard):
  Errors detected: 0

Guarantee verified: typechecker blocks unsafe use at analysis time.
```

**What it detects:**
- `show r` where `r` is `Uncertain[T]` → **ERROR**
- `upper(r)` with `r` Uncertain → **ERROR** (use in function expecting text)
- `define name: text as analyze(...)` → **ERROR** (incompatible type)
- `set x to r` where `x` is a typed variable → **ERROR**
- `map(list, given x: classify(x) using [...])` + `for each item in result: show item` → **ERROR**
- `define c as confidence_of(r); if c >= 0.85: show r` → **clean** (confidence alias recognized)

**What it does not detect yet (honest limitations):**
- Lambda in variable: `define f as given x: classify(x) using [...]` then `map(list, f)` — result type inferred as `list`, not `list[uncertain]`
- Multi-hop alias: `define d as c; if d >= 0.85:` where `c` is already an alias — only one level of aliasing
- Functions that internally call AI and return the extracted value — the caller does not see the AI behind it
- Inverted conditional: `0.85 <= confidence_of(r)` — only detects the form `confidence_of(r) >= threshold`

---

## Guarantee 3: Cryptographic audit trail

Every AI call is recorded with a chained SHA-256 hash
(blockchain-style). If anyone modifies any field of any
entry in the log, `audit_verify()` returns `false`.

**Proof you can run yourself:**

```python
# Run from repo root: python demo_garantia3.py
import sys; sys.path.insert(0, '.')
from ledge_lang import run
from ledge_lang.ai_types import GLOBAL_AUDIT

# ── Record three AI operations ────────────────────────────────────────────────
run(
    'define r1 as classify("urgent text") using ["urgent","routine"]\n'
    'define r2 as analyze("clause 3.2") using legal\n'
    'define r3 as classify("edge case") using ["yes","no"]',
    output_fn=lambda x: None,
    reset_audit=True
)

print(f"Entries recorded:        {len(GLOBAL_AUDIT._entries)}")
print(f"Chain intact (initial):  {GLOBAL_AUDIT.verify()}")

# ── Tamper: modify confidence of one entry ────────────────────────────────────
original_conf = GLOBAL_AUDIT._entries[0]["confidence"]
GLOBAL_AUDIT._entries[0]["confidence"] = 0.99
print(f"\nAfter modifying confidence[0]: {original_conf} → 0.99")
print(f"Chain after tamper:            {GLOBAL_AUDIT.verify()}")

# ── Tamper: insert a fake entry ───────────────────────────────────────────────
from ledge_lang.core_types import LedgeMap
GLOBAL_AUDIT._entries[0]["confidence"] = original_conf  # revert
fake = LedgeMap({
    "id": "fake", "operation": "fake_approve", "input_hash": "0" * 16,
    "output_type": "text", "confidence": 1.0, "model": "evil",
    "caller": "attacker", "timestamp": 0.0,
    "prev_hash": GLOBAL_AUDIT._entries[0]["chain_hash"],
    "chain_hash": "f" * 64,
})
GLOBAL_AUDIT._entries.insert(1, fake)
print(f"\nAfter inserting fake entry:    {GLOBAL_AUDIT.verify()}")
print("\nGuarantee verified: any modification to the log breaks the chain.")
```

**Expected output:**
```
Entries recorded:        3
Chain intact (initial):  True

After modifying confidence[0]: 1.0 → 0.99
Chain after tamper:            False

After inserting fake entry:    False

Guarantee verified: any modification to the log breaks the chain.
```

**Why it matters:** In high-risk systems (health, finance, legal), knowing
that the log is mathematically intact — not just "saved in a database" —
is the difference between auditable and truly auditable.

---

## Guarantee 4: Fail-safe by design

Without a backend, the system does not invent answers.
It does not approve loans. It does not classify patients. It does not sign contracts.
It escalates to a human.

**Proof you can run yourself:**

```python
# Run from repo root: python demo_garantia4.py
import sys; sys.path.insert(0, '.')
from ledge_lang import run

# Full medical triage system, with no model connected
with open('examples/showcase/medical_triage.ledge', encoding='utf-8') as f:
    src = f.read()

lines, _ = run(src, output_fn=lambda x: None, reset_audit=True)

print("Triage system output WITHOUT AI backend:")
print()
for l in lines:
    print(f"  {l}")

escalated = [l for l in lines if 'ESCALATE' in l]
automatic = [l for l in lines if 'URGENT' in l or 'ROUTINE' in l]

print()
print(f"Patients escalated to human:   {len(escalated)}")
print(f"Patients classified automatic: {len(automatic)}")
assert len(automatic) == 0, "FAILED: classified patients without a backend"
print("\nGuarantee verified: without backend, zero automatic decisions.")
```

**Expected output:**
```
Triage system output WITHOUT AI backend:

  === MEDICAL TRIAGE SYSTEM ===
  PATIENT P001: ESCALATE TO HUMAN (confidence=0)
  PATIENT P002: ESCALATE TO HUMAN (confidence=0)
  PATIENT P003: ESCALATE TO HUMAN (confidence=0)

  Decisions logged in audit trail: 3
  Cryptographic chain intact: true

Patients escalated to human:   3
Patients classified automatic: 0

Guarantee verified: without backend, zero automatic decisions.
```

**Why it matters:** A system that "fails open" (approves when uncertain)
is more dangerous than no system at all. Ledge fails closed: if there is no
certainty, it does not act.

---

## What Ledge does NOT guarantee

**1. That the AI model is correct.**
Ledge guarantees that you use the result explicitly. It does not guarantee
the result is good. A model that always responds "urgent" with
`confidence=0.95` would pass all Ledge checks without issue.

**2. That confidence=0.85 is the right threshold.**
Ledge forces you to choose a threshold. It does not tell you which one.
That depends on the domain, the cost of errors, and model calibration.

**3. That the audit trail persists across restarts.**
The audit trail lives in memory during the session. It is not a database.
If the process ends, the log is lost unless explicitly saved with `audit_export()`.

**4. That user-defined functions using AI are visible to the caller.**
If you write `define classify(x): return value_of(classify(x) using y)`,
whoever calls `classify(x)` receives a "clean" value — without `Uncertain`.
Ledge does not propagate that there was AI behind that function. The contract
must be explicit in the function signature.

**5. That AI lambdas in variables are tracked.**
`define f as given x: classify(x) using [...]` then `map(list, f)` —
the typechecker does not infer the result is `list[uncertain]`. It only detects
literal lambdas in direct calls to `map`.

**6. That Python code calling Ledge is safe.**
If you use the Python API (`from ledge_lang import run`) and access results
without checking confidence, Ledge cannot protect you. The guarantees
apply inside the Ledge language.

**7. That `audit_verify()` detects OS-level compromise.**
If someone has access to the process in memory and can modify the
`AuditTrail` object directly in Python, they can recalculate hashes.
The audit trail protects against post-hoc log modifications, not against
an attacker with root access to the process.
