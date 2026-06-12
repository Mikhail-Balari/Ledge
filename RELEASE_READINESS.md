# Release Readiness - Ledge 1.6.0 Alpha

This document records release-prep status for Ledge 1.6.0 Alpha and
publication status for earlier alpha releases. It is a process document, not
the PyPI long description.

## 1.6.0 Alpha Release Prep Status

- Target version: `1.6.0 Alpha`.
- Feature: Confidence Evidence Engine.
- PyPI 1.6.0 uploaded: no.
- PyPI project version: pending.
- Git tag `v1.6.0` created and pushed: no.
- GitHub Release `v1.6.0` created: no.
- GitHub Release should be marked as pre-release: yes.
- Ledge remains alpha.
- Confidence Evidence Engine is available in local release-prep state.
- Tamper-evident decision ledger remains future Phase 4.
- No production, enterprise, or compliance guarantees.
- No hallucination-prevention claim.
- No truth guarantee.
- No formal verification claim.
- No audit-proof, immutable, blockchain-secured, or certification claim.

## 1.6.0 Scope

- Adds audit-ready `ledge_lang.confidence.ConfidenceEvidence`.
- Adds `EvidenceSource` records and canonical evidence serialization.
- Adds SHA-256 evidence hashing and redaction helpers.
- Adds schema validation evidence.
- Adds ensemble agreement evidence as an exact stability signal, not truth.
- Adds backend-provided logprob signal evidence and unavailable-logprob
  warnings.
- Adds conservative scoring with hard schema/type failure dominance.
- Adds calibration reports with Brier score, simplified ECE, low-sample
  warnings, and cautious threshold guidance.
- Adds redaction-safe text and JSON report rendering.
- Adds CLI commands:
  - `ledge confidence-eval <fixture.json>`
  - `ledge confidence-eval <fixture.json> --format json`
  - `ledge calibration-report <outcomes.json>`
  - `ledge calibration-report <outcomes.json> --format json`
- Adds low-stakes synthetic confidence examples under `examples/confidence/`.
- Adds SDK evidence interoperability for legacy SDK evidence, audit-ready
  confidence evidence, unknown evidence, and malformed evidence-like objects.
- Corrects legacy compliance-shaped wording to structured evidence-field
  wording.

## 1.6.0 Packaging Checklist

- `pyproject.toml` version: `1.6.0`.
- `ledge_lang._version.__version__`: `1.6.0`.
- Bundled package data still includes `ledge_lang/demos/*.ledge`.
- Studio package data still includes `ledge_lang/studio/templates/*.html` for
  the optional `ledge-lang[studio]` extra.
- Expected wheel contents include:
  - `ledge_lang/confidence/*.py`
  - `ledge_lang/sdk/_evidence_compat.py`
  - `ledge_lang/sdk/*.py`
  - `ledge_lang/python_linter/*.py`
  - bundled demos and pilot templates listed in the 1.5.0 checklist below.
- Root-level `examples/`, including `examples/confidence/`, remain
  source-checkout materials for review and adaptation.

## 1.6.0 Pre-release Verification Checklist

Expected before publication:

- `python -m ledge_lang.cli version`: should report `Ledge 1.6.0`.
- Focused confidence tests:
  `python -m pytest tests/unit/test_confidence_*.py tests/unit/test_sdk_confidence_evidence_compat.py -q`.
- `python -m pytest tests/unit/ -q`.
- `python -m pytest tests/integration/ -q`.
- `python tests/conformance.py`.
- `python scripts/pre_release_check.py`.
- `python examples/sdk_decision_boundary/app.py`.
- `python -m ledge_lang.cli confidence-eval examples/confidence/fixture.json`.
- `python -m ledge_lang.cli confidence-eval examples/confidence/fixture.json --format json`.
- `python -m ledge_lang.cli calibration-report examples/confidence/outcomes.json`.
- `python -m ledge_lang.cli calibration-report examples/confidence/outcomes.json --format json`.
- `python -m ledge_lang.cli lint-python examples/python_linter/safe_usage.py --config examples/python_linter/ledge.toml`: should pass.
- `python -m ledge_lang.cli lint-python examples/python_linter/unsafe_usage.py --config examples/python_linter/ledge.toml`: should fail with `LPY001`, `LPY002`, `LPY003`, and `LPY004`.
- `python -m build`.
- `python -m twine check dist/*`.
- Clean local wheel install verification from outside the repository: pending
  before PyPI upload.
- Real PyPI install verification from outside the repository: pending after
  PyPI upload.
- PyPI page verification after upload: pending.
- PyPI badge SVG verification after upload: pending.
- Git tag and GitHub Release verification: pending.
- Public claims audit: pending before publication.
- No generated artifacts staged.
- Working tree clean before tag/upload/release.

## 1.6.0 Claims Audit Summary

The 1.6.0 Alpha release candidate must not claim:

- production readiness;
- enterprise readiness;
- compliance readiness, legal compliance, or certification;
- model correctness;
- calibrated confidence without representative historical outcomes;
- hallucination prevention;
- truth guarantee;
- formal verification;
- tamper-proof, audit-proof, immutable, or blockchain-secured behavior.

Allowed framing:

- alpha software;
- evidence-backed confidence records;
- redaction-aware reports;
- deterministic schema, ensemble, logprob, scoring, and calibration helpers;
- SDK interoperability for legacy and audit-ready evidence;
- structured evidence review support;
- future tamper-evident decision ledger work.

## 1.6.0 Current Recommendation

Ledge 1.6.0 Alpha is in local release-prep state. Do not upload to PyPI,
create tag `v1.6.0`, or create a GitHub Release until the release candidate is
explicitly approved.

## 1.5.0 Alpha Publication Status

- Released version: `1.5.0 Alpha`.
- Feature: Python Linter / CI Enforcement.
- PyPI 1.5.0 uploaded: yes.
- PyPI project version: `ledge-lang 1.5.0`.
- PyPI URL: https://pypi.org/project/ledge-lang/1.5.0/
- Release commit: `7409f855d541c399a705205a5c79a5ade4105192`.
- Git tag `v1.5.0` created and pushed: yes.
- Tag target commit: `7409f855d541c399a705205a5c79a5ade4105192`.
- GitHub Release `v1.5.0` created: yes.
- GitHub Release marked as pre-release: yes.
- GitHub Release marked as stable/latest: no.
- Real PyPI install verification: passed.
- CLI smoke tests from real PyPI: passed.
- SDK API smoke test from real PyPI: passed.
- SDK validation hardening smoke tests from real PyPI: passed.
- Python linter safe and unsafe tests from real PyPI: passed.
- JSON linter output verification from real PyPI: passed.
- PyPI badge verification: passed.
- Ledge remains alpha.
- Python linter / CI enforcement is available in 1.5.0 Alpha.
- Linter scope remains AST-based and local for common unsafe Python SDK
  decision-boundary patterns.
- This release adds `ledge lint-python <paths...>`.
- This release adds `ledge_lang/python_linter`.
- This release adds linter rules:
  - `LPY001`: `unsafe_unwrap` requires a non-empty reason.
  - `LPY002`: direct `.value` access on tracked `Uncertain`.
  - `LPY003`: configured critical action receives an unhandled uncertain value.
  - `LPY004`: `DecisionResult.value` is used in a configured critical action
    outside an allow guard.
- This release adds `ledge.toml` support for configured critical actions.
- This release adds text and JSON linter output.
- This release adds low-stakes safe and unsafe Python linter examples.
- This release adds a GitHub composite action for CI usage.
- This release adds unit and integration tests for Python linter behavior.
- Current limitations: no complete Python semantic verification; no mypy or
  Pyright plugin; no complete cross-file or interprocedural dataflow analysis;
  aliasing coverage is limited; framework behavior may require configuration
  and code review.
- Confidence Evidence Engine remains future work.
- Framework adapters remain future work.
- Evidence Pack remains future work.
- No production, enterprise, or compliance guarantees.
- No hallucination-prevention claim.
- No formal verification claim.
- No complete Python semantic verification claim.

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
- Ledge 1.5.0 Alpha has been published on PyPI.
- Git tag `v1.5.0` exists and points at the 1.5.0 release commit.
- GitHub Release `Ledge 1.5.0 Alpha - Python Linter CI Enforcement` exists as
  a pre-release.
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

## 1.5.0 Packaging Checklist

- `pyproject.toml` version: `1.5.0`.
- `ledge_lang._version.__version__`: `1.5.0`.
- `vscode-ledge/package.json`: not modified for this PyPI package release.
- Bundled package data includes `ledge_lang/demos/*.ledge`.
- Studio package data includes `ledge_lang/studio/templates/*.html` for the
  optional `ledge-lang[studio]` extra.
- Expected wheel contents include:
  - `ledge_lang/sdk/*.py`
  - `ledge_lang/python_linter/*.py`
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

## 1.5.0 Pre-release Verification Checklist

Expected before publication:

- `python -m ledge_lang.cli version`: should report `Ledge 1.5.0`.
- `python examples/sdk_decision_boundary/app.py`: passed.
- `python -m ledge_lang.cli demo`: passed.
- `python -m ledge_lang.cli demo medical_triage`: passed.
- `python -m ledge_lang.cli demo loan_approval`: passed.
- `python -m ledge_lang.cli pilot-dry-run loan_approval`: passed.
- `python -m ledge_lang.cli python-integration-demo`: passed.
- `python -m ledge_lang.cli ci-check ledge_lang/demos examples/python_integration`:
  passed.
- `python -m ledge_lang.cli lint-python examples/python_linter/safe_usage.py
  --config examples/python_linter/ledge.toml`: should pass.
- `python -m ledge_lang.cli lint-python examples/python_linter/unsafe_usage.py
  --config examples/python_linter/ledge.toml`: should fail with `LPY001`,
  `LPY002`, `LPY003`, and `LPY004`.
- `python -m pytest tests/unit/ -q`: passed.
- `python -m pytest tests/integration/ -q`: passed.
- `python tests/conformance.py`: passed.
- `python scripts/pre_release_check.py`: passed.
- `python -m build`: passed.
- `python -m twine check dist/*`: passed.
- Clean local wheel install verification from outside the repository: pending
  before PyPI upload.
- Real PyPI install verification from outside the repository: pending after
  PyPI upload.

## Claims Audit Summary

The 1.5.0 Alpha release candidate does not claim:

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
- AST-based Python linting/CI enforcement for common unsafe SDK patterns;
- future Confidence Evidence Engine work.

## Remaining Risks

- Ledge remains alpha software.
- The Python linter is AST-based and intentionally scoped.
- The Python linter does not provide complete Python semantic verification.
- No mypy or Pyright plugin is included.
- Cross-function aliasing, dynamic flows, and framework-specific behavior may
  require configuration and code review.
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

Ledge 1.5.0 Alpha is ready for review as a release candidate if validation
passes. Do not upload to PyPI, create tag `v1.5.0`, or create a GitHub Release
until the release candidate is explicitly approved.
