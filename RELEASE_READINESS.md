# Release Readiness - Ledge 1.4.0 Alpha

This document records release-readiness status for the Ledge 1.4.0 Alpha
candidate. It is a process document, not the PyPI long description.

## Historical Release State

- Ledge 1.3.0 has been published on PyPI.
- Git tag `v1.3.0` exists and points at the 1.3.0 release commit.
- GitHub Release `Ledge 1.3.0` exists as a pre-release.
- Ledge 1.3.1 has been published on PyPI.
- Git tag `v1.3.1` exists and points at the 1.3.1 release commit.
- GitHub Release `Ledge 1.3.1` exists as a pre-release.
- Ledge remains alpha software.

## 1.4.0 Alpha Candidate Status

- Candidate version: `1.4.0`.
- PyPI 1.4.0 uploaded: no.
- Git tag `v1.4.0` created: no.
- GitHub Release `Ledge 1.4.0` created: no.
- Current status: release-preparation working tree.

This candidate adds Python SDK Core. It does not add a Python linter, static
Python CI enforcement, a calibrated Confidence Evidence Engine, provider
adapters, a gateway, a sidecar, a dashboard, a hosted service, or a policy
runtime.

## What Changed Since 1.3.1

- Package version metadata prepared for `1.4.0`.
- Python SDK Core added under `ledge_lang.sdk`.
- SDK public objects added:
  - `Uncertain[T]`
  - `DecisionPolicy`
  - `DecisionResult[T]`
  - `ConfidenceEvidence`
  - SDK exceptions
  - validation helpers
  - deterministic fake client utilities for examples and tests
- Low-stakes customer-support refund-routing SDK example added under
  `examples/sdk_decision_boundary/`.
- SDK unit and integration tests added.
- README and Python integration docs updated for 1.4.0 Alpha.

## SDK Scope

The SDK is alpha and intentionally small:

- API/runtime-level handling only.
- No Python static linting or CI enforcement yet.
- No calibrated confidence engine.
- No ensemble scoring.
- No logprobs integration.
- No calibration scoring.
- No LangChain, LlamaIndex, Langfuse, or LangSmith adapters.
- No real OpenAI, Anthropic, or other provider client.

`ConfidenceEvidence` is a minimal metadata container for SDK-level decision
handling. It does not prove model correctness, calibrate confidence, establish
legal compliance, or prevent hallucinations.

## Existing Command Behavior

- `ledge run <file.ledge>` runs the static typechecker first. If type issues are
  found, it prints the issues, exits non-zero, and does not execute the program.
- `ledge run <file.ledge> --unsafe` skips the static typecheck and executes the
  program anyway. This is the explicit bypass for experiments and unsafe
  examples.
- `ledge check --types <file.ledge>` runs the static checker without executing
  the program.
- `ledge_lang.checked_run(source)` is the safety-gated Python API for `.ledge`
  source. It runs the static checker first and raises `LedgeError` without
  executing on failure.
- `ledge_lang.run(source)` remains the low-level direct execution API and
  bypasses the checker by design.
- `ledge pilot-dry-run loan_approval` runs the packaged synthetic pilot dry run
  without source-checkout files.
- `ledge python-integration-demo` runs the packaged Python integration demo
  through `ledge_lang.checked_run(...)`.
- `ledge ci-check <paths...>` recursively typechecks `.ledge` files for CI use.

## Packaging Checklist

- `pyproject.toml` version: prepared as `1.4.0`.
- `ledge_lang._version.__version__`: prepared as `1.4.0`.
- `vscode-ledge/package.json`: not modified for this PyPI package release.
- Bundled package data includes `ledge_lang/demos/*.ledge`.
- Studio package data includes `ledge_lang/studio/templates/*.html` for the
  optional `ledge-lang[studio]` extra.
- Expected wheel contents include:
  - `ledge_lang/sdk/*.py`
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
- `python examples/sdk_decision_boundary/app.py`
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

The 1.4.0 Alpha candidate must not claim:

- production readiness;
- enterprise readiness;
- compliance readiness or certification;
- model correctness;
- calibrated confidence by default;
- hallucination prevention;
- a real credit model or lending decision system;
- tamper-proof or audit-proof behavior;
- static Python enforcement for SDK code today.

Allowed framing:

- alpha software;
- minimal Python SDK Core;
- API/runtime-level SDK handling;
- synthetic demos;
- checked execution path for `.ledge` boundaries;
- future Python linting/CI enforcement;
- future Confidence Evidence Engine work.

## Remaining Risks

- Ledge remains alpha software.
- The SDK does not statically enforce Python code yet.
- The SDK does not replace the DSL static checker.
- The static checker remains intentionally scoped and does not claim
  whole-program soundness.
- The SDK example is synthetic and low-stakes.
- Root-level source examples, pilot templates, and scripts remain
  source-checkout materials even though packaged commands are available.
- Audit records can support structured evidence review, but they do not
  establish legal or regulatory compliance.

## Current Recommendation

Ready for human review as a 1.4.0 Alpha candidate once validation, build,
claims audit, command accuracy audit, package content audit, and clean wheel
verification all pass. Do not upload PyPI 1.4.0, create tag `v1.4.0`, or create
a GitHub Release until this candidate is approved for publication.
