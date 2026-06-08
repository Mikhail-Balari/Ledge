# Release Readiness - Ledge 1.3.1 Alpha Patch

This document records release-readiness status for the Ledge 1.3.1 alpha patch.
It is a process document, not the PyPI long description.

## Historical Release State

- Ledge 1.3.0 has been published on PyPI.
- Git tag `v1.3.0` exists and points at the 1.3.0 release commit.
- GitHub Release `Ledge 1.3.0` exists as a pre-release.
- Ledge remains alpha software.

## 1.3.1 Patch Status

- Candidate version: `1.3.1`.
- PyPI 1.3.1 uploaded: no.
- Git tag `v1.3.1` created: no.
- GitHub Release `Ledge 1.3.1` created: no.
- Current status: release-preparation working tree.

This patch is documentation and release-metadata cleanup only. It does not add
new runtime features, new SDK behavior, a gateway, a sidecar, a dashboard, or a
policy runtime.

## What Changed Since 1.3.0

- Package version metadata prepared for `1.3.1`.
- README and public docs updated to stop describing 1.3.0 as a candidate,
  unreleased, or not yet published.
- README written as the final public README for the 1.3.1 package.
- Installed commands documented as package commands:
  - `ledge demo`
  - `ledge demo medical_triage`
  - `ledge demo loan_approval`
  - `ledge pilot-dry-run loan_approval`
  - `ledge python-integration-demo`
  - `ledge ci-check <paths...>`
- Source-checkout wrappers documented separately:
  - `python scripts/run_pilot_dry_run.py pilot_templates/loan_approval`
  - `python examples/python_integration/app.py`
  - `python scripts/ledge_check_ci.py ledge_lang/demos examples/python_integration`
- Release docs updated to record that 1.3.0 was published, tagged, and released.

## Command Behavior

- `ledge run <file.ledge>` runs the static typechecker first. If type issues are
  found, it prints the issues, exits non-zero, and does not execute the program.
- `ledge run <file.ledge> --unsafe` skips the static typecheck and executes the
  program anyway. This is the explicit bypass for experiments and unsafe
  examples.
- `ledge check --types <file.ledge>` runs the static checker without executing
  the program.
- `ledge_lang.checked_run(source)` is the safety-gated Python API. It runs the
  static checker first and raises `LedgeError` without executing on failure.
- `ledge_lang.run(source)` remains the low-level direct execution API and
  bypasses the checker by design.
- `ledge pilot-dry-run loan_approval` runs the packaged synthetic pilot dry run
  without source-checkout files.
- `ledge python-integration-demo` runs the packaged Python integration demo
  through `ledge_lang.checked_run(...)`.
- `ledge ci-check <paths...>` recursively typechecks `.ledge` files for CI use.

## Packaging Checklist

- `pyproject.toml` version: prepared as `1.3.1`.
- `ledge_lang._version.__version__`: prepared as `1.3.1`.
- Bundled package data includes `ledge_lang/demos/*.ledge`.
- Studio package data includes `ledge_lang/studio/templates/*.html` for the
  optional `ledge-lang[studio]` extra.
- Expected wheel contents:
  - `ledge_lang/demos/medical_triage.ledge`
  - `ledge_lang/demos/loan_approval.ledge`
  - `ledge_lang/pilot_templates/loan_approval/fixture.json`
  - `ledge_lang/pilot_templates/loan_approval/policy.json`
  - `ledge_lang/pilot_templates/loan_approval/expected_results.md`
  - `ledge_lang/pilot_templates/loan_approval/sample_final_report.md`
  - `ledge_lang/python_integration/decision_boundary.ledge`
  - `ledge_lang/python_integration/fixture.json`
  - `ledge_lang/studio/templates/studio.html`
- Root-level `scripts/`, `examples/`, and `pilot_templates/` remain
  source-checkout materials; the wheel does not install them as standalone
  filesystem trees.

## Verification Checklist

To complete before approving publication:

- `python -m ledge_lang.cli version`
- `python -m ledge_lang.cli demo`
- `python -m ledge_lang.cli demo medical_triage`
- `python -m ledge_lang.cli demo loan_approval`
- `python -m ledge_lang.cli pilot-dry-run loan_approval`
- `python -m ledge_lang.cli python-integration-demo`
- `python -m ledge_lang.cli ci-check ledge_lang/demos examples/python_integration`
- `python -m pytest tests/unit/ -q`
- `python -m pytest tests/integration/ -q`
- `python tests/conformance.py`
- `python scripts/pre_release_check.py`
- `python -m build`
- `python -m twine check dist/*`
- clean local wheel install verification from outside the repository

## Claims Audit Summary

The 1.3.1 alpha patch must not claim:

- production readiness;
- enterprise readiness;
- compliance certification;
- model correctness;
- calibrated confidence by default;
- a real credit model or lending decision system;
- tamper-proof or audit-proof behavior.

Allowed framing:

- alpha software;
- synthetic demos;
- packaged pilot dry-run;
- packaged Python integration example;
- checked execution path for `.ledge` boundaries;
- packaged CI/static checker helper.

## Remaining Risks

- Ledge remains alpha software.
- The static checker is intentionally scoped and does not claim whole-program
  soundness.
- The pilot dry-run and Python integration example are synthetic.
- Root-level source examples, pilot templates, and scripts remain
  source-checkout materials even though packaged commands are available.
- Audit records can support structured evidence review, but they do not
  establish legal or regulatory compliance.

## Current Recommendation

Ready for human review as a 1.3.1 alpha patch candidate once the validation,
build, claims audit, command accuracy audit, package content audit, and clean
wheel verification all pass. Do not upload PyPI 1.3.1, create tag `v1.3.1`, or
create a GitHub Release until the patch is approved for publication.
