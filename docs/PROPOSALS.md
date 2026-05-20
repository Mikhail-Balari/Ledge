# Ledge Enhancement Proposals (LEPs)
## Process and Index

A LEP (Ledge Enhancement Proposal) is the mechanism for proposing
significant changes to the Ledge language or standard library.

---

## When to write a LEP

Write a LEP for:
- New syntax or keywords
- Changes to existing semantics
- New standard library modules
- Changes to the type system
- Anything that modifies `docs/SPEC.md` or `docs/GRAMMAR.md`

You do NOT need a LEP for:
- Bug fixes (behavior diverges from spec)
- Documentation improvements
- Tooling improvements (formatter, LSP, debugger)
- Performance improvements with identical semantics
- New examples

---

## LEP template

Create `docs/proposals/LEP-NNN-short-title.md` with this structure:

```markdown
# LEP-NNN: Feature Title

## Status
Draft | Under Review | Accepted | Rejected | Withdrawn

## Author
Your name / handle

## Created
YYYY-MM-DD

## Summary
One paragraph: what problem does this solve and how?

## Motivation
What is wrong with the current language that requires this change?
Provide concrete examples of code that is harder than it should be.

## Specification
Exact syntax (EBNF for new grammar rules) and semantics.
Show before/after examples.

## Implementation plan
Which files change: parser, interpreter, typechecker, tests, docs.
Estimated complexity.

## Alternatives considered
What else was tried. Why this approach was chosen over others.

## Backwards compatibility
Does any existing valid Ledge program change behavior? If yes:
- What changes?
- What is the migration path?
- How many programs are affected?

## Reference implementation
Link to a branch or PR with working code and tests.
A LEP cannot be accepted without a reference implementation.

## Open questions
Unresolved issues that need discussion.
```

---

## Review process

1. **Draft** — Author creates the LEP, opens a PR, requests review
2. **Under Review** — Community (when it exists) and maintainers discuss for 30 days (7 days for non-breaking)
3. **Accepted** — Implementation merged, FEATURE_MATRIX.md updated
4. **Rejected** — Documented reason, may be re-proposed with changes
5. **Withdrawn** — Author withdraws before acceptance

A LEP is accepted when:
- All open questions are resolved
- Reference implementation passes the full test suite
- No strong objections from maintainers
- For breaking changes: 90-day review, deprecation path defined

---

## Active proposals

*(none — this is a new project)*

---

## Accepted proposals (in v1.0)

The following major design decisions were made during development.
They are documented here as retrospective proposals.

### LEP-001: `=` is always comparison, `set X to` is always mutation

**Decision:** The assignment operator `=` is reserved exclusively for comparison.
Mutation uses the English-natural `set X to value`.

**Rationale:** AI code generators frequently confuse `=` assignment with `=`
comparison. Making them syntactically distinct eliminates the entire class
of assignment-in-condition bugs. One form per concept.

### LEP-002: `or` as unified fallback/logical operator

**Decision:** `or` serves both as logical OR and as fallback for `nothing`-returning operations.

**Rationale:** `divide(a, b) or 0` reads as English. The dual use is intentional:
`nothing` is falsy, so `expr or default` works for both boolean and nothing cases.
This is documented in SEMANTICS.md §4.5.

### LEP-003: AI operations always return `Uncertain[T]`

**Decision:** `analyze`, `classify`, `generate`, `ask`, `embed` return `Uncertain[T]`,
not raw values. Without a backend, `confidence = 0.0` always.

**Rationale:** AI output is uncertain by nature. Making uncertainty explicit at
the type level lets checked execution paths reject a common AI integration bug:
using AI output as if it were certain.

### LEP-004: Automatic audit trail for all AI operations

**Decision:** Every AI instruction automatically records an entry in the
session audit trail. No opt-in required.

**Rationale:** Regulated or high-impact AI systems often need auditable decision
records. Making logging automatic reduces the discipline failure mode where
developers forget to log. This is supporting evidence infrastructure, not a
compliance certification.

### LEP-005: Contracts in the syntax (`requires:` / `ensures:`)

**Decision:** Function preconditions and postconditions are first-class
syntax, not library decorators.

**Rationale:** Runtime-checked preconditions and postconditions make boundary
assumptions visible at the function boundary. Built-in syntax makes those
assumptions visible in the code, not buried in decorators.
