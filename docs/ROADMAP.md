# Roadmap

This roadmap is for expert review before production-critical use. It is not a promise of dates or a claim that Ledge is already suitable for regulated deployment.

## Current Release: 1.2.0 Alpha

What exists now:

- A small DSL with `Uncertain[T]` values for AI outputs.
- A static checker that rejects unchecked uncertain values before `ledge run`.
- Explicit bypass via `ledge run --unsafe`.
- Safe Python entry points via `checked_run(...)` and `checked_run_file(...)`.
- Low-level direct execution via `run(...)` for tests and embedding.
- A hash-chained local audit log with a limited threat model.
- Unit, conformance, official example, demo, package build, and clean wheel verification through `scripts/pre_release_check.py` plus release-readiness checks.

What is not claimed:

- No whole-program soundness.
- No sandbox boundary.
- No compliance certification.
- No production-critical validation.
- No guarantee that model confidence is calibrated.

## 1. Stronger Static Checker

Planned work:

- Interprocedural tracking for functions that receive, return, or store `Uncertain[T]`.
- More precise alias tracking across local assignments and container operations.
- Better narrowing for guard patterns and early returns.
- Clearer diagnostics with source spans and repair suggestions.
- A public checker conformance corpus, including negative examples that must fail.

Exit criteria:

- The checker rejects the documented unsafe patterns across the conformance corpus.
- Known limitations are explicit and covered by regression tests.
- Safe patterns remain ergonomic enough for real examples.

## 2. Python Integration and Adapters

Planned work:

- Thin adapters for common Python AI clients that return `Uncertain[T]` values.
- A documented boundary between checked Ledge execution and low-level Python embedding.
- Integration examples for services that want to run Ledge snippets as policy-checked decision steps.
- Better packaging smoke tests across supported Python versions and operating systems.

Exit criteria:

- External callers can adopt the checked path without rewriting their entire application.
- Bypass paths remain explicit and documented.

## 3. Policy Engine

Planned work:

- First-class policy configuration for thresholds, fallback requirements, and allowed escape hatches.
- CI-friendly reports for policy violations.
- Per-domain policy examples for triage, hiring, legal review, finance, and moderation.

Exit criteria:

- Teams can review confidence policy separately from business logic.
- Policy failures are machine-readable and human-readable.

## 4. Audit Anchoring

Planned work:

- External append-only anchoring options for audit-chain roots.
- Rotation and retention guidance.
- Tamper-evidence wording that is precise about the attacker model.
- Export formats with stable schemas.

Exit criteria:

- Audit records can be independently reconciled against an external anchor.
- Documentation states exactly what compromise scenarios remain out of scope.

## 5. CI Gates and Release Discipline

Planned work:

- CI jobs for unit tests, conformance tests, official example typechecks, demo execution, package build, and wheel install smoke tests.
- Published release checklist matching `scripts/pre_release_check.py`.
- Negative-example inventory that is excluded from expected-to-pass example lists.

Exit criteria:

- A release cannot pass CI while official examples fail, package data is missing, or the console command is broken.

## 6. Security Review

Planned work:

- Review of file access, module loading, audit storage, export formats, CLI entry points, and Python embedding APIs.
- Explicit guidance for sandboxing and host-language isolation.
- Dependency and packaging review.

Exit criteria:

- Security assumptions are documented.
- Known bypasses are intentional, named, tested, and marked unsafe where appropriate.

## 7. Third-Party Validation

Planned work:

- Independent review of the static checker and threat model.
- External reproduction of the release verification script.
- Public issue tracking for review findings and fixes.

Exit criteria:

- Core safety claims have been reviewed by people outside the project.
- Findings are resolved or documented as limitations.

## 8. Production Pilot Criteria

A production pilot should not start until all of the following are true:

- The relevant domain has calibration measurements for the target model and task.
- Thresholds, fallbacks, and escape hatches have owner approval.
- CI runs the checker and release verification on every change.
- Audit records are anchored outside the local process boundary if they matter operationally.
- Human review exists for consequential decisions.
- Rollback and incident-response procedures are documented.
- The deployment treats Ledge as one control among several, not a replacement for monitoring, evals, or review.

## Final Target

The long-term goal is a small, auditable execution layer that makes uncertainty handling visible in code and enforceable at the entry points teams actually use. Getting there requires stronger analysis, operational controls, and independent validation.
