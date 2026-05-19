# Ledge Capability Matrix
## Version 1.2.0

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
- Clean wheel install verification passed for the local 1.2.0 wheel.

## Known Gaps

- No known production deployments.
- No mechanized proof or formal soundness theorem.
- No legal compliance certification.
- PyPI 1.2.0 has not been uploaded yet.
