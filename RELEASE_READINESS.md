# Release Readiness - Ledge 1.3.0 Alpha Candidate

This document records release-readiness status for a possible Ledge 1.3.0
alpha release. It is preparation only.

## Release Status

- Candidate version: `1.3.0`
- PyPI 1.3.0 uploaded: no
- Git tag `v1.3.0` created: no
- GitHub Release `Ledge 1.3.0` created: no
- Current status: unreleased alpha candidate

Ledge 1.2.0 remains the latest published PyPI release until a 1.3.0 upload is
performed and verified.

## What Changed Since 1.2.0

Installed package / CLI candidate:

- Bundled synthetic `loan_approval` demo for `ledge demo loan_approval`.
- Existing bundled `medical_triage` demo remains available through
  `ledge demo medical_triage`.
- Packaged synthetic pilot dry-run command:
  `ledge pilot-dry-run loan_approval`.
- Packaged Python integration demo command:
  `ledge python-integration-demo`.
- Packaged CI/static checker command:
  `ledge ci-check <paths...>`.
- Package version metadata prepared for `1.3.0`.

Source-checkout materials preserved:

- Public demo and pilot planning docs: `DEMO.md`, `COMMERCIAL.md`,
  `PILOT_PACK.md`.
- Pilot templates under `pilot_templates/`.
- Synthetic pilot dry-run harness:
  `python scripts/run_pilot_dry_run.py pilot_templates/loan_approval`.
- Minimal Python integration example:
  `python examples/python_integration/app.py`.
- CI/static checker helper:
  `python scripts/ledge_check_ci.py ledge_lang/demos examples/python_integration`.

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
- `ledge pilot-dry-run loan_approval` runs the packaged synthetic pilot dry
  run without source-checkout files.
- `ledge python-integration-demo` runs the packaged Python integration demo
  through `ledge_lang.checked_run(...)`.
- `ledge ci-check <paths...>` recursively typechecks `.ledge` files for CI use.

## Packaging Checklist

- `pyproject.toml` version: prepared as `1.3.0`.
- `ledge_lang._version.__version__`: prepared as `1.3.0`.
- Bundled package data includes `ledge_lang/demos/*.ledge`.
- Studio package data includes `ledge_lang/studio/templates/*.html` for the
  optional `ledge-lang[studio]` extra.
- Candidate wheel verified to contain:
  - `ledge_lang/demos/medical_triage.ledge`
  - `ledge_lang/demos/loan_approval.ledge`
  - `ledge_lang/pilot_templates/loan_approval/fixture.json`
  - `ledge_lang/pilot_templates/loan_approval/policy.json`
  - `ledge_lang/pilot_templates/loan_approval/expected_results.md`
  - `ledge_lang/pilot_templates/loan_approval/sample_final_report.md`
  - `ledge_lang/python_integration/decision_boundary.ledge`
  - `ledge_lang/python_integration/fixture.json`
  - `ledge_lang/studio/templates/studio.html`
- Candidate wheel exposes the packaged command surface for pilot dry-run,
  Python integration demo, and CI/static checking.
- Root-level `scripts/`, `examples/`, and `pilot_templates/` remain
  source-checkout materials; the wheel does not install them as standalone
  filesystem trees.

## Wheel And Source-Checkout Availability

Expected after installing the local 1.3.0 candidate wheel:

- `ledge version`
- `ledge demo`
- `ledge demo medical_triage`
- `ledge demo loan_approval`
- `ledge pilot-dry-run loan_approval`
- `ledge python-integration-demo`
- `ledge ci-check <paths...>`
- Python API imports such as `from ledge_lang import __version__, checked_run`

Expected source-checkout wrappers/materials:

- `python scripts/run_pilot_dry_run.py pilot_templates/loan_approval`
- `python scripts/ledge_check_ci.py ledge_lang/demos examples/python_integration`
- `python examples/python_integration/app.py`
- `pilot_templates/loan_approval/`
- `examples/python_integration/`

The wrapper commands are useful for review and adaptation from a clone. The
installed wheel uses packaged resources and CLI entry points instead.

## Verification Checklist

Local verification completed for this candidate:

- `python -m ledge_lang.cli version`: passed, reports `Ledge 1.3.0`.
- `python -m ledge_lang.cli demo`: passed, lists `loan_approval` and
  `medical_triage`.
- `python -m ledge_lang.cli demo medical_triage`: passed.
- `python -m ledge_lang.cli demo loan_approval`: passed.
- `python -m ledge_lang.cli pilot-dry-run loan_approval`: passed.
- `python -m ledge_lang.cli python-integration-demo`: passed.
- `python -m ledge_lang.cli ci-check ledge_lang/demos examples/python_integration`:
  passed.
- `python scripts/run_pilot_dry_run.py pilot_templates/loan_approval`: passed.
- `python examples/python_integration/app.py`: passed.
- `python scripts/ledge_check_ci.py ledge_lang/demos examples/python_integration`:
  passed.
- `python scripts/ledge_check_ci.py examples/showcase`: passed.
- `python -m pytest tests/unit/ -q`: passed, 373 tests.
- `python -m pytest tests/integration/ -q`: passed, 37 tests.
- `python tests/conformance.py`: passed, 284/284.
- `python scripts/pre_release_check.py`: passed after allowing isolated build
  dependency resolution.
- `python -m build`: passed.
- `python -m twine check dist/*`: passed.
- Clean wheel install verification from outside the repository: passed for
  `ledge version`, bundled demos, Python API import/`checked_run(...)`,
  `ledge pilot-dry-run loan_approval`, `ledge python-integration-demo`, valid
  `ledge ci-check`, and invalid `ledge ci-check` failure behavior.

## Claims Audit Summary

The 1.3.0 alpha candidate must not claim:

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
- Audit records are useful as supporting evidence but do not establish legal or
  regulatory compliance.

## Current Recommendation

Ready for human review as a 1.3.0 alpha release candidate. Do not upload PyPI
1.3.0, create tag `v1.3.0`, or create a GitHub Release until the candidate is
approved for publication.
