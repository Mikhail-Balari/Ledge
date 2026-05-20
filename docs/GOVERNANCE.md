# Ledge Governance
## Version 1.2.0

---

## 1. Project ownership

Ledge is currently maintained by a single author (bus factor = 1). This is
acknowledged as a risk. The roadmap to reduce this risk:

1. Public GitHub repository with open issues and PRs
2. Response commitment: critical bugs within 72 hours, feature proposals within 14 days
3. Governance transfer protocol: if the primary maintainer becomes unavailable,
   the project's MIT license ensures anyone can fork and continue

---

## 2. Language change process

### Levels of change

**Level 1 — Bug fix:** Behavior diverges from SPEC.md or SEMANTICS.md.
Fix without proposal. Must not break conformance tests.

**Level 2 — Clarification:** Spec text is ambiguous. Update documentation only,
no behavior change. No proposal required.

**Level 3 — Additive feature:** New syntax or builtin that doesn't break
existing programs. Requires a written proposal (see §3). 30-day review period.

**Level 4 — Breaking change:** Any change that makes previously valid programs
invalid or changes their behavior. Requires proposal + 90-day review + major
version bump.

**Rule:** A feature is not shipped until it passes the 7×1 standard:
syntax ✓ grammar ✓ semantics ✓ runtime ✓ typechecker ✓ tests ✓ working example ✓

---

## 3. Proposal process

A proposal is a document with these required sections:

```
# LEP-NNN: Feature Title

## Status
Draft | Under Review | Accepted | Rejected | Withdrawn

## Motivation
What problem does this solve? Concrete examples required.

## Specification
Exact syntax and semantics. EBNF for any new grammar.

## Implementation plan
What must change: parser, interpreter, typechecker, tests, docs.

## Alternatives considered
What else was tried and why it was rejected.

## Backwards compatibility
Does this break any existing programs? If yes, migration path.

## Reference implementation
Link to a branch or PR with working code.
```

Proposals live in `docs/proposals/LEP-NNN-title.md`.

---

## 4. Versioning policy

Ledge uses Semantic Versioning (semver.org):

```
MAJOR.MINOR.PATCH

MAJOR: Breaking changes to grammar, semantics, or stdlib
MINOR: New shipped features, backwards-compatible
PATCH: Bug fixes, documentation, no behavior changes
```

**Compatibility intent during alpha:**
The project aims to preserve behavior within a major version where practical,
but compatibility commitments are subordinate to the limitations documented in
`docs/COMPATIBILITY.md` and release notes.

Pre-1.0 versions (0.x.y) had no compatibility guarantee.

---

## 5. Release process

1. All tests pass: `python -m ledge_lang.test_runner tests/` → 0 failures
2. All conformance tests pass: `python tests/conformance.py` → 100%
3. All examples run green: `python -m ledge_lang.test_runner tests/examples/` → 0 failures
4. FEATURE_MATRIX.md is updated
5. CHANGELOG.md has an entry with every user-visible change
6. Version is consistent in: `pyproject.toml`, `ledge_lang/__init__.py`,
   `vscode-ledge/package.json`, `README.md`, `CHANGELOG.md`
7. Git tag: `git tag vX.Y.Z` after the distribution is published and verified

---

## 6. Definition of done (per feature)

A feature is **done** when ALL of these are true:

- [ ] Syntax: the construct parses without errors
- [ ] Grammar: `docs/GRAMMAR.md` is updated
- [ ] Semantics: `docs/SEMANTICS.md` or `docs/SPEC.md` describes the behavior
- [ ] Runtime: the interpreter executes it correctly
- [ ] Typechecker: the checker handles it (or explicitly documents it's unchecked)
- [ ] Tests: dedicated tests in `tests/unit/` or `tests/conformance_suite/`
- [ ] Example: at least one working example in `examples/`
- [ ] FEATURE_MATRIX.md: marked as **shipped**

If any item is missing, the feature is **experimental** in the matrix.
If a feature is in the matrix as **roadmap**, it must NOT appear in any README
or documentation as if it exists today.

---

## 7. Security policy

- Runtime errors must never expose internal Python stack traces to end users
- AI operations must never log plaintext inputs — audit trail uses input hashes
- `import "python:module"` is intentional; users are responsible for what they import
- No network access happens without explicit user code (`import "http"` or FFI)

To report a security issue: open a GitHub issue marked `[SECURITY]`.

---

## 8. Bus factor mitigation plan

Current bus factor: 1

Target bus factor: 3+ before production-critical use

Steps:
1. All design decisions documented with rationale (this document, SEMANTICS.md, SPEC.md)
2. CONTRIBUTING.md describes how to contribute
3. Test suite is comprehensive enough that a new maintainer can verify correctness
4. No critical knowledge lives only in the author's head — it's all in docs/
