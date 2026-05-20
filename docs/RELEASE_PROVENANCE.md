# Release Provenance Plan

Ledge 1.2.0 is alpha software. This document describes the current release
provenance status and the path toward stronger package supply-chain trust. It
is not a claim of signed artifacts, compliance certification, or
SLSA-certified provenance.

## Current Status

- Ledge 1.2.0 was uploaded to PyPI using a token-based Twine upload after local
  release gates and PyPI installation verification.
- Git tag `v1.2.0` exists and points at release commit
  `e330e164fc5ba8d49ccf16fa288514392ac5e41b`.
- GitHub Release `Ledge 1.2.0` exists.
- The source distribution and wheel are published on PyPI.
- Release artifacts are not currently signed.
- PyPI publishing is not currently using GitHub trusted publishing.
- Build provenance is not currently SLSA-certified.
- Reproducible builds have not yet been demonstrated.

## Near-Term Target

Future releases should move publishing into GitHub Actions and make the
source-to-package path easier to audit:

- Configure PyPI trusted publishing through GitHub Actions.
- Build release artifacts in CI rather than on a local workstation.
- Keep `scripts/pre_release_check.py` and `scripts/ci_wheel_smoke.py` as release
  gates before publication.
- Verify that the GitHub Actions workflow, Git tag, repository identity, and
  PyPI project identity form a clear path from source commit to uploaded
  artifact.
- Document which workflow is allowed to publish and which branch or tag patterns
  it accepts.

## Future Target

Longer-term provenance work should be explicit and incremental:

- Sign release artifacts or publish signed attestations.
- Generate provenance attestations for built distributions.
- Evaluate a SLSA-aligned release process over time.
- Investigate reproducible builds for the wheel and source distribution.
- Publish SBOM artifacts alongside releases once SBOM tooling is chosen.
- Define rotation and revocation procedures for release signing keys or trusted
  publisher configuration.

## Explicit Non-Claims

The current release process does not claim:

- signed PyPI artifacts;
- SLSA certification;
- compliance certification;
- institutional or critical-infrastructure assurance;
- enabled PyPI trusted publishing;
- demonstrated reproducible builds.

These items are future hardening goals, not properties of the current alpha
release.

## Practical Review Notes

Today, reviewers can inspect the Git tag, GitHub Release, PyPI package files,
CI workflow, release readiness record, and installed-wheel smoke tests. That
provides useful traceability, but it is not equivalent to signed provenance or
third-party supply-chain assurance.
