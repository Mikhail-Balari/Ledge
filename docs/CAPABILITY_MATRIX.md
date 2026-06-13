# Ledge Capability Matrix
## Version 1.6.0 Alpha

This matrix reflects the 1.6.0 alpha release. Ledge 1.4.0 Alpha
added Python SDK Core while preserving the DSL and checked `.ledge` execution
path. Ledge 1.5.0 Alpha adds AST-based Python linter / CI enforcement for
common unsafe SDK decision-boundary patterns. Ledge 1.6.0 Alpha adds the
Confidence Evidence Engine. Phase 4 Slice 0 defines the planned ledger
architecture and contract in docs only.

This matrix is a sober snapshot of implemented capabilities and known gaps.
Release-readiness results live in `RELEASE_READINESS.md`.

## Language And Runtime

- Tree-walker interpreter: implemented.
- Bytecode VM: implemented for a core subset.
- Python FFI: implemented, with security caveats documented in `docs/SECURITY.md`.
- Native compilation experiments: present, but no broad performance claim is made for this release.

## AI And Audit

- AI operations return `Uncertain[T]`.
- `ledge check --types` rejects unchecked `Uncertain[T]` use.
- `ledge run` typechecks before execution by default.
- `ledge run --unsafe` is the explicit bypass.
- The audit store records AI decisions with input hashes and a hash chain under a limited threat model.
- Python SDK Core provides `Uncertain`, `DecisionPolicy`, `DecisionResult`,
  minimal confidence evidence metadata, validators, and deterministic fake
  clients for normal Python examples.
- Python linter / CI enforcement provides `ledge lint-python` for common unsafe
  SDK decision-boundary patterns in normal Python code.
- Confidence Evidence Engine provides audit-ready confidence evidence records,
  schema validation evidence, ensemble stability evidence, logprob signal
  evidence, conservative scoring, calibration reports, redaction-safe report
  rendering, and SDK evidence interoperability.
- Tamper-Evident Decision Ledger is planned / architecture-defined in
  documentation only. Runtime ledger writing, verification, export, and review
  pack generation are not implemented in this release.

## Packaging

- The package builds as sdist and wheel.
- The wheel contains `ledge_lang/demos/medical_triage.ledge`.
- The wheel contains both bundled demos:
  `medical_triage.ledge` and `loan_approval.ledge`.
- The installed package exposes:
  `ledge pilot-dry-run loan_approval`, `ledge python-integration-demo`, and
  `ledge ci-check <paths...>`.
- The installed package exposes `ledge lint-python <paths...>` for Python SDK
  unsafe-use linting.
- The installed package exposes `ledge confidence-eval <fixture.json>` and
  `ledge calibration-report <outcomes.json>` for confidence evidence and
  calibration report examples.
- Root-level `scripts/`, `examples/`, and `pilot_templates/` remain
  source-checkout materials for review and adaptation.

## Known Gaps

- No known production deployments.
- No mechanized proof or formal soundness theorem.
- No legal compliance certification.
- Ledge 1.4.0 Alpha adds Python SDK Core, not a production deployment pattern.
- Ledge 1.5.0 Alpha adds AST-based Python linter / CI enforcement, not
  complete Python semantic verification.
- No complete Python semantic verification or mypy/Pyright plugin.
- Python linter coverage is AST-based and intentionally scoped to common local
  unsafe-use patterns; it does not yet perform complete cross-file or
  interprocedural dataflow analysis.
- Confidence Evidence Engine is alpha. It does not claim calibrated confidence
  without historical outcomes, legal compliance certification, production
  readiness, or formal verification.
- No hidden persistence is added by the Confidence Evidence Engine.
- Tamper-Evident Decision Ledger is architecture-defined but not implemented.
- Ledger architecture is not production-ready and does not claim legal
  compliance certification.
- Ledger architecture is tamper-evident in design, not tamper-proof, and makes
  no immutable storage claim.
- Ledger architecture uses append-oriented local records, not blockchain.
