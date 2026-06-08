# Ledge Capability Matrix
## Version 1.4.x Alpha

This matrix reflects the 1.4.x alpha line. Ledge 1.4.0 Alpha adds Python SDK
Core while preserving the DSL and checked `.ledge` execution path.

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

## Packaging

- The package builds as sdist and wheel.
- The wheel contains `ledge_lang/demos/medical_triage.ledge`.
- The wheel contains both bundled demos:
  `medical_triage.ledge` and `loan_approval.ledge`.
- The installed package exposes:
  `ledge pilot-dry-run loan_approval`, `ledge python-integration-demo`, and
  `ledge ci-check <paths...>`.
- Root-level `scripts/`, `examples/`, and `pilot_templates/` remain
  source-checkout materials for review and adaptation.

## Known Gaps

- No known production deployments.
- No mechanized proof or formal soundness theorem.
- No legal compliance certification.
- Ledge 1.4.0 Alpha adds Python SDK Core, not a production deployment pattern.
- No Python static linting/type-checker enforcement for SDK code yet.
- No full Confidence Evidence Engine, ensemble scoring, logprobs, or
  calibration engine yet.
