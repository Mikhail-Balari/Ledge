# Ledge Demo Guide

This guide is a public, reproducible path for evaluating Ledge as an alpha AI
decision-boundary tool.

## What This Demo Shows

- AI outputs represented as `Uncertain[T]`.
- Checked execution that rejects unchecked uncertain values before execution.
- Confidence thresholds and human-review fallbacks in source code.
- Deterministic rules kept separate from AI-derived decisions.
- Hash-chained audit entries and chain verification.
- Safe failure without an AI backend: confidence is 0, so AI-derived actions
  escalate instead of auto-approving.

## What This Demo Does Not Show

- It does not prove model correctness.
- It does not demonstrate legal or regulatory compliance.
- It does not replace evals, monitoring, or human review.
- It does not show a production deployment.
- It does not claim that confidence is calibrated.
- The loan demo is synthetic. It is not a credit model and not a lending
  decision system.

## Requirements

- Python 3.9 or newer.
- `pip install ledge-lang`.
- No API key is required for the bundled demos.
- No repository clone is required for the published `medical_triage` demo.
- The `loan_approval` demo and installed pilot/Python/CI commands are included
  in the unreleased 1.3.0 alpha candidate source checkout and locally built
  wheel. They should not be described as available from PyPI until 1.3.0 is
  uploaded.

## Quick Start

From the currently published PyPI package:

```bash
pip install ledge-lang
ledge demo
ledge demo medical_triage
```

From a source checkout containing the unreleased 1.3.0 alpha candidate work,
or from a locally built 1.3.0 candidate wheel:

```bash
python -m build
pip install dist/ledge_lang-1.3.0-py3-none-any.whl
ledge demo
ledge demo loan_approval
ledge pilot-dry-run loan_approval
ledge python-integration-demo
```

## Demo 1: Medical Triage

From the published package or a source checkout, run:

```bash
ledge demo medical_triage
```

Expected shape:

```text
=== MEDICAL TRIAGE DEMO ===
PATIENT P001: ESCALATE TO HUMAN (confidence=0)
PATIENT P002: ESCALATE TO HUMAN (confidence=0)
PATIENT P003: ESCALATE TO HUMAN (confidence=0)

Decisions logged in audit trail: 3
Cryptographic chain intact: true
```

Interpretation:

- The AI classification is uncertain.
- With no backend configured, confidence is 0.
- The demo escalates instead of acting on fabricated certainty.
- AI calls are recorded in the audit trail.

## Demo 2: Synthetic Loan Approval Boundary

Run:

```bash
ledge demo loan_approval
```

Expected shape:

```text
=== SYNTHETIC LOAN APPROVAL DECISION BOUNDARY DEMO ===
Synthetic demo only. Not a credit model. Not a lending decision system.
Pattern: deterministic DTI rule + confidence-gated AI risk signal + human review fallback
Backend: none; AI confidence is 0 unless a backend is configured
Confidence threshold: 0.85
```

Interpretation:

- Deterministic debt-to-income checks are labeled separately from AI-derived
  risk classification.
- AI-derived approval is only possible after a confidence guard.
- With no backend, AI confidence is 0 and AI-assessed applications go to human
  review.
- The audit count and chain verification are printed at the end.

## Synthetic Pilot Dry Run

After installing the 1.3.0 alpha candidate wheel, run:

```bash
ledge pilot-dry-run loan_approval
```

From a source checkout, the wrapper command remains available:

```bash
python scripts/run_pilot_dry_run.py pilot_templates/loan_approval
```

This loads a synthetic fixture and policy, evaluates each case, and prints a
shadow-mode pilot summary. It is not a credit model, not a lending decision
system, and not production or compliance software.

## Python Integration Example

After installing the 1.3.0 alpha candidate wheel, run:

```bash
ledge python-integration-demo
```

From a source checkout, the wrapper command remains available:

```bash
python examples/python_integration/app.py
```

This shows a normal Python app loading a synthetic fixture and delegating only
the AI decision boundary to Ledge through `checked_run(...)`. It is not a full
SDK, gateway, sidecar, hosted service, or production integration pattern.

## Five-Minute Technical Walkthrough

1. Install and list bundled demos:

   ```bash
   pip install ledge-lang
   ledge demo
   ```

2. Run medical triage:

   ```bash
   ledge demo medical_triage
   ```

3. From a locally built 1.3.0 alpha candidate wheel or source checkout, run
   the synthetic loan boundary:

   ```bash
   ledge demo loan_approval
   ```

4. Run the installed Python integration demo:

   ```bash
   ledge python-integration-demo
   ```

   From a source checkout, the wrapper is also available:

   ```bash
   python examples/python_integration/app.py
   ```

5. Confirm checked execution blocks unsafe use by creating a temporary file:

   ```ledge
   define r as classify("invoice") using ["release_payment", "hold_payment"]
   show value_of(r)
   show "PAYMENT_RELEASED"
   ```

   Then run:

   ```bash
   ledge run unsafe_example.ledge
   ```

   The command should fail before printing `PAYMENT_RELEASED`.

## Fifteen-Minute Extended Technical Walkthrough

1. Read the checker contract:

   ```bash
   python -c "import webbrowser; webbrowser.open('https://github.com/Mikhail-Balari/Ledge/blob/main/docs/STATIC_CHECKER.md')"
   ```

2. Test unsafe interpolation:

   ```ledge
   define r as classify("invoice") using ["release_payment", "hold_payment"]
   show "AI decision: {value_of(r)}"
   show "PAYMENT_RELEASED"
   ```

   Run:

   ```bash
   ledge run unsafe_interpolation.ledge
   ```

3. Compare with the explicit bypass:

   ```bash
   ledge run unsafe_interpolation.ledge --unsafe
   ```

   This bypass is intentionally dangerous and exists so unsafe behavior is
   visible and named.

4. Inspect the bundled demo source from Python:

   ```bash
   python -c "from ledge_lang import demos; print(open(demos.demo_path('loan_approval')).read())"
   ```

5. Review:

   - [`docs/STATIC_CHECKER.md`](docs/STATIC_CHECKER.md)
   - [`docs/THREAT_MODEL.md`](docs/THREAT_MODEL.md)
   - [`docs/AUDIT_ANCHORING.md`](docs/AUDIT_ANCHORING.md)
   - [`docs/UNCERTAINTY_MODEL.md`](docs/UNCERTAINTY_MODEL.md)

## Basic Troubleshooting

- If `ledge` is not found, try:

  ```bash
  python -m ledge_lang.cli demo
  ```

- If `ledge demo loan_approval` is not listed, you are probably using an
  installed package that does not include the unreleased candidate demo rather
  than a source checkout containing the latest demo work. To check the
  installed version:

  ```bash
  ledge version
  ```

- If demos show confidence 0, that is expected without a configured backend.
  The demos are designed to fail closed.

## Limitations

Ledge is alpha software. These demos are not production systems. They
show a narrow checked-execution contract and audit trail behavior. They do not
establish model accuracy, calibrated confidence, legal compliance, security
certification, or production-critical readiness.
