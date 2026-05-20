# Supply-Chain Posture

Ledge 1.2.0 is alpha software. This document describes the current package
dependency posture and the lightweight checks available today. It is not a
security certification, compliance certification, or institutional assurance
claim.

## Current Dependency Posture

The core package currently declares no required runtime dependencies in
`pyproject.toml`. Optional dependency groups are used for development tooling
and the Studio web interface.

The project publishes a normal Python wheel and source distribution through
PyPI. Releases are tagged on GitHub, but signed artifacts, trusted publishing,
SBOM publication, and build provenance are future work.

## Local Check

Run:

```bash
python scripts/supply_chain_check.py
```

The script reports:

- package name and version from `pyproject.toml`;
- Python interpreter and platform;
- direct runtime dependencies;
- optional dependency groups;
- installed distribution inventory and available license metadata;
- whether optional tools such as `pip-audit` or `cyclonedx-py` are available.

The script does not install heavy tooling and does not fail merely because
optional tools are missing. It is intended to make the current state visible in
CI and local review.

## What This Does Not Prove

The current check does not:

- generate or publish an SBOM;
- perform a vulnerability audit;
- verify signatures or build provenance;
- certify dependency licenses for a particular organization;
- establish production-critical or institutional readiness.

It is a lightweight visibility check only.

## Future Work

Tracked follow-up work includes:

- Generate SBOMs in CycloneDX or SPDX format.
- Add `pip-audit` or equivalent vulnerability scanning where practical.
- Add license-policy checks for direct and transitive dependencies.
- Evaluate GitHub trusted publishing for PyPI.
- Evaluate signed artifacts and signed release attestations.
- Move toward SLSA-aligned build provenance over time.

These steps would improve reviewability of the package supply chain, but they
would still need to be interpreted within Ledge's documented alpha status and
threat model.
