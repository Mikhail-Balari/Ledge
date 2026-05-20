# Ledge Red Team Notes

This document records the strongest criticisms of Ledge as an early technical
project. A criticism should be treated as resolved only when the repository has
tests, documentation, and runnable evidence that a neutral reviewer could check.

## Active Criticisms

### C-01: "This is Python with different keywords"

**Status:** Partially mitigated.

Ledge is implemented in Python and borrows familiar syntax. The distinction is
not that Ledge is a fundamentally new execution substrate. The distinction is
the checked uncertainty contract: AI primitives return `Uncertain[T]`, and the
checked execution paths reject direct use of those values before execution.

Remaining risk: a Python library, mypy/Pyright plugin, or custom linter could
approximate parts of this contract inside Python. Ledge needs continued evidence
that the language boundary is worth the migration cost.

### C-02: "The AI positioning is not yet externally validated"

**Status:** Acknowledged.

The repository contains implementation tests and examples, not an independent
user study. Claims about fewer real-world bugs, better LLM-generated programs,
or production outcomes require third-party evaluation.

Current support:

- the static checker rejects representative unsafe `Uncertain` uses;
- `ledge run` and `checked_run(...)` enforce that checker before execution;
- examples demonstrate confidence guards and `when(...)` fallbacks.

Remaining risk: external validation is still needed before broad production
claims are appropriate.

### C-03: "The checker is limited"

**Status:** Acknowledged, mitigated for the documented surface.

The typechecker is an intraprocedural AST walker. It is not a mechanized type
system and has no formal soundness proof. It recognizes the safe patterns
documented in `docs/STATIC_CHECKER.md`; other patterns may require refactoring
or future checker work.

Current support:

- unsafe direct use is an error;
- recognized confidence guards permit `value_of(...)` inside the guarded block;
- `when(...)` provides thresholded extraction with a fallback;
- `unsafe_value_of(...)` is explicit and intentionally visible.

Remaining risk: stronger interprocedural tracking and broader flow analysis are
roadmap work.

### C-04: "The audit trail is not a security boundary"

**Status:** Acknowledged.

The audit trail is useful for local evidence and tamper detection within its
documented threat model. It is not tamper-proof. An attacker who controls both
the SQLite store and the external anchor file can forge a consistent history.

Remaining risk: production-critical deployments need external anchoring,
access controls, immutable logging infrastructure, and security review.

### C-05: "Python FFI can bypass the model"

**Status:** Acknowledged.

Python FFI is powerful and intentionally available. It is not a sandbox. The
CLI supports import allowlisting flags, and the low-level Python API exposes
`allowed_modules`, but process isolation and dependency policy belong to the
host environment.

Remaining risk: deployments that run untrusted code need OS/container isolation
and should treat FFI as a governed capability.

### C-06: "Performance and tooling are immature"

**Status:** Acknowledged.

Ledge 1.2.0 is an alpha core. It has a tree-walking interpreter, bytecode VM
subset, formatter, debugger, LSP, examples, and tests, but it is not tuned for
compute-heavy workloads or mature production workflows.

Remaining risk: stronger profiling, CI matrices, package ecosystem, and
production pilots are needed before critical use.

### C-07: "Governance and bus factor are weak"

**Status:** Acknowledged.

The project is early and has a small contributor base. The MIT license,
documented roadmap, CI, conformance tests, and public issue tracker make it
forkable and reviewable, but they do not replace a broader maintainer group.

## Closed Or Mitigated Items

| ID | Criticism | Current evidence |
|---|---|---|
| C-03 | Direct `Uncertain` use can slip through checked CLI execution | `ledge run` typechecks by default; integration tests cover blocking and `--unsafe` bypass |
| C-04 | No installable demo path | Wheel includes `ledge_lang/demos/medical_triage.ledge`; clean wheel verification passes |
| C-05 | Python API had no checked execution helper | `checked_run(...)` and `checked_run_file(...)` exported and tested |
| C-06 | Public CI missing | GitHub Actions runs unit, integration, conformance, and pre-release checks |

## Next Validation Work

- Independent review of the checker rules and false-negative surface.
- Third-party reproduction of release checks from a clean environment.
- Security review of FFI, audit storage, and external anchoring.
- Production pilot criteria with explicit non-goals and rollback paths.
- Evidence bundles for real model-backed workflows, with outcomes recorded.
