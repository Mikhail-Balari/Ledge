# Ledge runtime properties — what is true, with proofs, and what is not

> Each property comes with code you can copy, paste, and run.
> No API keys, no setup, no blind trust. The word "guarantee" is reserved
> for the precise statements below; everything else is supporting infrastructure.

---

## Guarantee 1: Zero confidence without a backend

Without an AI model connected, all AI operations
(`classify`, `analyze`, `generate`, `ask`, `embed`) return
`confidence=0.0`. Always. Without exception.

The system does not invent answers. It does not guess. It does not act.

**Verify it yourself:**

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

**What this means:** Without a connected backend, every AI primitive returns
`confidence = 0.0`. Code with a non-zero decision threshold will therefore
take the low-confidence branch (typically escalate-to-human) rather than act
on a fabricated certainty.

**What this does not mean:** It does not mean the model, once connected, is
correct. It does not mean confidence > 0 reflects actual accuracy. See the
calibration discussion in the README for that gap.

---

## Property 2: Direct use of an Uncertain[T] value is rejected statically

The Ledge static analyzer rejects direct uses of `Uncertain[T]` values
before any code runs. The set of "direct uses" the checker rejects is
listed precisely below.

This is a static-analysis property, not a soundness theorem. The checker is
a single-file, flow-sensitive AST walker with documented limitations.

**Verify it yourself:**

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
  Suggestion: if confidence_of(r) >= 0.85: show value_of(r)  -- guard then use

Safe code (explicit confidence guard):
  Errors detected: 0

Property verified: the checker rejects direct use at analysis time.
```

**What it rejects (errors):**
- `show r` where `r` is `Uncertain[T]`
- `upper(r)` or any function call with Uncertain `r` (except the recognized safe builtins)
- `r + 1` and other arithmetic on Uncertain values
- `if r:` and other boolean uses of Uncertain values
- `define name: text as analyze(...)` — Uncertain to typed variable
- `set x to r` where `x` is a typed variable
- `value_of(r)` outside a recognized confidence guard
- Iterating `list[uncertain[T]]` and using the element directly

**What it accepts (clean):**
- `when(r, 0.85, fallback)` — runtime-checked extraction
- `confidence_of(r)`, `is_confident(r)`, `is_uncertain(r)` — inspection
- `value_of(r)` inside `if confidence_of(r) >= t:` or `if is_confident(r):`
- `define c as confidence_of(r); if c >= 0.85: value_of(r)` — alias-aware guard
- `unsafe_value_of(r)` — the explicit escape hatch (deliberately ugly name)

**Documented limitations (the checker does NOT yet recognize):**
- **Intraprocedural only.** Uncertain is not tracked across function call boundaries.
  Function parameters/returns annotated as `uncertain[T]` are honored at the boundary;
  the runtime `AIDerived` wrapper preserves provenance for callers that look for it.
- **Early-return guards.** `if confidence_of(r) < t: return; use(r)` does not narrow
  the rest of the block. Use `if ... >= t: ... else:` or `unsafe_value_of(r)`.
- **`not is_uncertain(x)`** is not recognized — only the positive forms.
- **Multi-hop alias.** `define d as c` where `c = confidence_of(r)` — only one hop.
- **Inverted operators.** `0.85 <= confidence_of(r)` — only the form `confidence_of(r) >= t`.
- **Lambdas stored in variables.** `define f as given x: classify(x) using [...]; map(list, f)` —
  the literal-lambda case in `map(list, given x: ...)` is recognized; the stored-in-variable case is not.

---

## Property 3: SHA-256 chained audit log detects post-hoc modification

Every AI call is recorded with a SHA-256 hash that incorporates the
previous entry's hash. Modifying any field of any entry breaks the chain
and `audit_verify()` returns `false`. An external anchor file
(`~/.ledge/anchors.jsonl`) records chain state every 10 entries; deleting
and rebuilding the SQLite store leaves the anchors inconsistent.

**Threat model and limits.** This detects post-hoc modification by an actor
who can read/write the SQLite store but not the anchor file. An attacker
who controls both the database and the anchor file can compute a fresh
consistent chain and forge a clean history. An attacker with access to the
in-memory `AuditTrail` object can rewrite entries and recompute hashes
trivially. This is supporting evidence for governance review, not a
tamper-proof boundary against a malicious local operator.

**Verify it yourself:**

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

**What this means in practice.** A reviewer can verify the chain
independently of the recording process. If the chain verifies and the
anchors match, no entry has been altered or removed by anyone without
write access to both the store and the anchor file. That is a useful
piece of supporting evidence; it is not, by itself, a guarantee that the
decisions recorded were correct.

---

## Property 4: Fail-safe default when no backend is configured

Property 4 is a consequence of Property 1: without a backend,
`confidence = 0.0`, so any decision threshold above 0.0 causes the
low-confidence branch to run. For programs whose low-confidence branch
escalates to human review, the system therefore does not act on
fabricated certainty.

This is a consequence, not an independent guarantee. It depends on the
program's threshold being non-zero and the low-confidence branch being
sensible. A program that hard-codes `value_of(r) or "approve"` will still
approve.

**Verify it yourself:**

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

**Caveat.** "Fails closed" is a property of programs that follow the
escalation pattern, not a property of the runtime itself. Ledge makes the
escalation pattern idiomatic and rejects programs that violate the static
contract; it does not prevent a developer from writing a program that
hard-codes a permissive default.

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
