# Release Readiness - Ledge 1.4.1 Alpha

This document records final release-readiness and post-release status for
Ledge 1.4.1 Alpha. It is a process document, not the PyPI long description.

## Historical Release State

- Ledge 1.3.0 has been published on PyPI.
- Git tag `v1.3.0` exists and points at the 1.3.0 release commit.
- GitHub Release `Ledge 1.3.0` exists as a pre-release.
- Ledge 1.3.1 has been published on PyPI.
- Git tag `v1.3.1` exists and points at the 1.3.1 release commit.
- GitHub Release `Ledge 1.3.1` exists as a pre-release.
- Ledge 1.4.0 Alpha has been published on PyPI.
- Git tag `v1.4.0` exists and points at the 1.4.0 release commit.
- GitHub Release `Ledge 1.4.0 Alpha - Python SDK Core` exists as a
  pre-release.
- Ledge 1.4.1 Alpha has been published on PyPI.
- Git tag `v1.4.1` exists and points at the 1.4.1 release commit.
- GitHub Release `Ledge 1.4.1 Alpha - Docs-only Public Surface Patch` exists
  as a pre-release.
- Ledge remains alpha software.

## 1.4.1 Alpha Publication Status

- Released version: `1.4.1 Alpha`.
- Purpose: docs-only public surface correction after 1.4.0.
- PyPI 1.4.1 uploaded: yes.
- PyPI project version: `ledge-lang 1.4.1`.
- PyPI URL: https://pypi.org/project/ledge-lang/1.4.1/
- Git tag `v1.4.1` created and pushed: yes.
- Tag target commit: `c72da1ecc1e697d383e60832322fb4f947500c1c`.
- GitHub Release `v1.4.1` created: yes.
- GitHub Release marked as pre-release: yes.
- Real PyPI install verification: passed.
- CLI smoke tests from real PyPI: passed.
- Python API smoke test from real PyPI: passed.
- SDK API smoke test from real PyPI: passed.
- SDK validation hardening smoke tests from real PyPI: passed.
- README/PyPI public description uses DSL plus SDK framing: yes.
- PyPI badge verification: passed.
- No SDK behavior changes.
- No CLI changes.
- No DSL/runtime changes.
- No test, example, or package functionality changes.
- Ledge remains alpha.
- Python static linting / CI enforcement remains future work.
- Confidence Evidence Engine remains future work.
- Framework adapters remain future work.
- Evidence Pack remains future work.
- No production, enterprise, or compliance guarantees.

## 1.4.0 Alpha Publication Status

- Released version: `1.4.0`.
- PyPI 1.4.0 uploaded: yes.
- PyPI project version: `ledge-lang 1.4.0`.
- PyPI URL: https://pypi.org/project/ledge-lang/1.4.0/
- Git tag `v1.4.0` created and pushed: yes.
- Tag target commit: `2837518d39d71128f9da74cdd1a14b7ee9c4d8c3`.
- GitHub Release `v1.4.0` created: yes.
- GitHub Release marked as pre-release: yes.
- Real PyPI install verification: passed.
- CLI smoke tests from real PyPI: passed.
- Python API smoke test from real PyPI: passed.
- SDK API smoke test from real PyPI: passed.
- SDK validation hardening smoke tests from real PyPI: passed.
- Current status: publicly released alpha.

This release adds Python SDK Core. It does not add a Python linter, static
Python CI enforcement, a calibrated Confidence Evidence Engine, framework
adapters, a gateway, a sidecar, a dashboard, a hosted service, or a policy
runtime.

## What Changed in 1.4.0 Since 1.3.1

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

## 1.4.1 Packaging Checklist

- `pyproject.toml` version: `1.4.1`.
- `ledge_lang._version.__version__`: `1.4.1`.
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

Completed before and after publication:

- `python -m ledge_lang.cli version`: passed.
- `python examples/sdk_decision_boundary/app.py`: passed.
- `python -m ledge_lang.cli demo`: passed.
- `python -m ledge_lang.cli demo medical_triage`: passed.
- `python -m ledge_lang.cli demo loan_approval`: passed.
- `python -m ledge_lang.cli pilot-dry-run loan_approval`: passed.
- `python -m ledge_lang.cli python-integration-demo`: passed.
- `python -m ledge_lang.cli ci-check ledge_lang/demos examples/python_integration`:
  passed.
- `python -m pytest tests/unit/ -q`: passed.
- `python -m pytest tests/integration/ -q`: passed.
- `python tests/conformance.py`: passed.
- `python scripts/pre_release_check.py`: passed.
- `python -m build`: passed.
- `python -m twine check dist/*`: passed.
- Clean local wheel install verification from outside the repository: passed.
- Real PyPI install verification from outside the repository: passed.
- Real PyPI CLI smoke tests: passed.
- Real PyPI Python API smoke test: passed.
- Real PyPI SDK API smoke test: passed.
- Real PyPI SDK validation hardening smoke tests: passed.

## Claims Audit Summary

The 1.4.1 Alpha docs-only patch release does not claim:

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
- Python static linting / CI enforcement remains future work.
- The SDK does not replace the DSL static checker.
- The static checker remains intentionally scoped and does not claim
  whole-program soundness.
- The Confidence Evidence Engine remains future work.
- Framework adapters remain future work.
- Evidence Pack remains future work.
- The SDK example is synthetic and low-stakes.
- Root-level source examples, pilot templates, and scripts remain
  source-checkout materials even though packaged commands are available.
- Audit records can support structured evidence review, but they do not
  establish legal or regulatory compliance.
- There are no production, enterprise, or compliance guarantees.

## Current Recommendation

Ledge 1.4.1 Alpha release closure is complete. PyPI publication, real PyPI
install verification, PyPI badge verification, tag creation/push, and GitHub
pre-release creation have all completed. Ready to close Phase 1 and start
Phase 2 planning.
