# Ledge Capability Matrix
## Version 1.3.0 Alpha Candidate

This matrix reflects the current main branch prepared for a 1.3.0 alpha
candidate. Ledge 1.2.0 remains the latest published PyPI release until the
candidate is uploaded and verified.

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

## Packaging

- The package builds as sdist and wheel.
- The wheel contains `ledge_lang/demos/medical_triage.ledge`.
- The 1.3.0 alpha candidate wheel is expected to contain both bundled demos:
  `medical_triage.ledge` and `loan_approval.ledge`.
- The 1.3.0 alpha candidate wheel is expected to expose:
  `ledge pilot-dry-run loan_approval`, `ledge python-integration-demo`, and
  `ledge ci-check <paths...>`.
- Root-level `scripts/`, `examples/`, and `pilot_templates/` remain
  source-checkout materials for review and adaptation.

## Known Gaps

- No known production deployments.
- No mechanized proof or formal soundness theorem.
- No legal compliance certification.
- PyPI 1.2.0 has been published. PyPI 1.3.0 has not been uploaded yet.
