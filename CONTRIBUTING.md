# Contributing to Ledge

Thank you for your interest in contributing.

---

## Before you start

Read these documents:
- `docs/SPEC.md` — language specification
- `docs/FEATURE_MATRIX.md` — what is shipped vs roadmap
- `docs/GOVERNANCE.md` — decision process
- `docs/PROPOSALS.md` — how to propose language changes

---

## Definition of Done

**A feature is only done when ALL of these are true:**

- [ ] **Syntax**: the construct parses without errors
- [ ] **Grammar**: `docs/GRAMMAR.md` is updated with EBNF
- [ ] **Semantics**: `docs/SEMANTICS.md` or `docs/SPEC.md` describes the behavior
- [ ] **Runtime**: the interpreter executes it correctly
- [ ] **Typechecker**: the checker handles it (or explicitly documents it's unchecked)
- [ ] **Tests**: dedicated tests in `tests/unit/` or `tests/conformance_suite/`
- [ ] **Example**: at least one working example in `examples/`
- [ ] **FEATURE_MATRIX.md**: marked as **shipped**

If any item is missing, the feature is **experimental**, not shipped.

This is the **7×1 standard** from the Plan Maestro.

---

## Test requirements

Every PR must:

1. Pass all existing tests:
```bash
python tests/conformance.py
python -m pytest tests/unit/ -q
```

2. Add tests for new behavior:
   - Unit tests in `tests/unit/test_*.py`
   - Conformance tests in `tests/conformance_suite/` if it's language behavior
   - Both positive cases (feature works) and negative cases (errors fail correctly)

3. Maintain 100% conformance test pass rate.

A PR that reduces the conformance pass rate from 100% will not be merged.

---

## Code standards

**Python code (implementation):**
- Follow the existing style in each file
- No unused imports
- No bare `except:` — always catch specific exceptions
- Error messages must include `Fix:` or `Tip:` suggestions
- No f-strings with nested quotes (use string concatenation instead)

**Ledge code (examples):**
- All examples must run green: `python -m ledge_lang.test_runner tests/examples/`
- No examples that show fake AI confidence without a backend
- Every AI operation must use `when()`, `confidence_of()`, or `value_of()` for extraction

---

## Documentation standards

- New language features require updates to `docs/GRAMMAR.md` (EBNF)
- New builtins require updates to `docs/SPEC.md` (builtins section)
- Changes to AI behavior require updates to `docs/SEMANTICS.md`
- `docs/FEATURE_MATRIX.md` must accurately reflect what is shipped

---

## Proposing language changes

For significant changes (new syntax, semantic changes), write a LEP first.
See `docs/PROPOSALS.md` for the template and process.

Language changes without a LEP will not be merged except for bug fixes.

---

## Bug reports

Open a GitHub issue with:
1. Minimal reproduction case (fewest lines that show the bug)
2. Expected behavior
3. Actual behavior
4. Ledge version (`ledge version`)

For AI safety bugs (fake confidence, wrong Uncertain behavior), label
the issue `[CRITICAL]` — these get priority response.

---

## Security issues

For security issues, open a GitHub issue marked `[SECURITY]`.
Do not publicly disclose before the maintainer has had time to respond.

---

## Review criteria

PRs are reviewed for:
1. **Correctness** — does it do what the spec says?
2. **Consistency** — does it fit the existing language design?
3. **Tests** — are there enough tests at the right level?
4. **Documentation** — are docs updated?
5. **7×1 compliance** — does the feature meet all seven criteria?

PRs that only add syntax without runtime/typechecker/tests will be
rejected with guidance on what's missing.
