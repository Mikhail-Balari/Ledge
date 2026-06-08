# Ledge Capability Matrix
## Version 1.3.x Alpha

This matrix reflects the 1.3.x alpha line. Ledge 1.3.0 has been published on
PyPI, tagged as `v1.3.0`, and released on GitHub as a pre-release. Ledge 1.3.1
is a documentation and release-metadata cleanup patch with no new runtime
features.

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
- Ledge 1.3.0 has been published. Ledge 1.3.1 is a cleanup patch.
