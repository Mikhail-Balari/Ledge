# Ledge Normative Rule Index
## Version 1.1.0

Every normative rule in Ledge with its conformance test.
A rule without a conformance test is not normatively verified.

---

## Core Semantics

| Rule ID | Rule | Test | Status |
|---------|------|------|--------|
| SEM-01 | `true ≠ 1`, `false ≠ 0`, `nothing ≠ false` | tests/conformance.py::test_boolean_semantics | ✓ |
| SEM-02 | Divide by zero returns `nothing`, never crashes | tests/conformance.py::test_safe_division | ✓ |
| SEM-03 | Out-of-bounds index returns `nothing` | tests/conformance.py::test_safe_indexing | ✓ |
| SEM-04 | `nothing or X` returns `X` | tests/conformance.py::test_fallback | ✓ |
| SEM-05 | Left-to-right evaluation order | tests/unit/test_core_language.py | ✓ |
| SEM-06 | Closures capture lexical scope | tests/unit/test_core_language.py::test_closures | ✓ |
| SEM-07 | Generator laziness: not evaluated until accessed | tests/unit/test_core_language.py | ✓ |
| SEM-08 | `set` requires prior `define` | tests/conformance.py | ✓ |
| SEM-09 | Type annotation enforced on `set` | tests/unit/test_typechecker.py | ✓ |
| SEM-10 | `match` falls through to `otherwise` when no case matches | tests/conformance.py | ✓ |

## AI Semantics (Critical)

| Rule ID | Rule | Test | Status |
|---------|------|------|--------|
| AI-01 | Without backend: all AI ops return confidence=0.0 EXACTLY | tests/test_security.py::TestAISafetyCore | ✓ |
| AI-02 | Without backend: classify() returns `nothing`, never first label | tests/test_security.py::TestAISafetyCore | ✓ |
| AI-03 | Uncertain[T] declared type preserved when value=nothing | tests/unit/test_ai_native.py | ✓ |
| AI-04 | confidence_of() always in [0.0, 1.0] — clamped | tests/test_security.py | ✓ |
| AI-05 | Audit trail resets per run() call by default | tests/test_security.py::TestAuditTrailIsolation | ✓ |
| AI-06 | Audit trail inputs stored as hash, not plaintext | tests/test_security.py | ✓ |
| AI-07 | Using Uncertain without extraction = typechecker ERROR | tests/test_security.py::TestUncertainEnforcement | ✓ |
| AI-08 | After confidence guard: Uncertain narrowed to safe type | tests/unit/test_typechecker.py | ✓ |

## Contract Semantics

| Rule ID | Rule | Test | Status |
|---------|------|------|--------|
| CON-01 | `requires:` fires BEFORE body — body never executes on violation | tests/unit/test_core_language.py | ✓ |
| CON-02 | `ensures:` fires AFTER body — uses `result` binding | tests/unit/test_core_language.py | ✓ |
| CON-03 | Violation raises LedgeError with readable condition | tests/unit/test_core_language.py | ✓ |
| CON-04 | Contracts survive recursion | tests/unit/test_core_language.py | ✓ |

## Stream Semantics

| Rule ID | Rule | Test | Status |
|---------|------|------|--------|
| STR-01 | list-based streams are re-iterable | tests/unit/test_core_language.py | ✓ |
| STR-02 | `stream_take(s, n)` terminates after n items | tests/unit/test_core_language.py | ✓ |
| STR-03 | Infinite generators don't blow up memory if not consumed | tests/unit/test_core_language.py | ✓ |
| STR-04 | `when s has new item as x:` processes all items in order | tests/unit/test_core_language.py | ✓ |

## FFI Semantics

| Rule ID | Rule | Test | Status |
|---------|------|------|--------|
| FFI-01 | `import "python:X"` fails safely if module doesn't exist | tests/unit/test_core_language.py | ✓ |
| FFI-02 | Python None → nothing | tests/unit/test_core_language.py | ✓ |
| FFI-03 | With allowlist, non-listed module = LedgeError | tests/test_security.py::TestFFISecurity | ✓ |
| FFI-04 | Empty allowlist blocks all Python imports | tests/test_security.py::TestFFISecurity | ✓ |

## Format

Rules are versioned with Ledge. A rule can only change in a MAJOR version bump.
Breaking a rule is a conformance failure.
