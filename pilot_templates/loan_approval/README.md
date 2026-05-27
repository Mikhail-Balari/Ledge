# Synthetic Loan Approval Pilot Dry Run

This folder is a synthetic shadow-mode dry-run for an AI decision boundary.
It uses fake loan-approval cases to show how a fixture, policy, evaluation
output, and final report could support a pilot conversation.

It is not a credit model. It is not a lending decision system. It does not use
real credit data, does not touch a production system, and does not establish
legal or regulatory compliance.

## Run

From the repository root:

```bash
python scripts/run_pilot_dry_run.py pilot_templates/loan_approval
```

## Files Loaded

- `fixture.json`: synthetic cases.
- `policy.json`: synthetic thresholds and action rules.
- `expected_results.md`: expected case-by-case outcomes.
- `sample_final_report.md`: sample report shape for a shadow-mode pilot.

## What The Output Demonstrates

- Deterministic rule checks are evaluated before AI-derived signals.
- Missing evidence and hard review flags route to human review.
- AI-derived approve/reject actions require high confidence.
- Low-confidence and ambiguous cases fall back to review.
- The result is a dry-run summary, not a production action.

## Limitations

- No real model is called.
- No API key is used.
- No audit database is written.
- No production workflow is touched.
- Synthetic cases do not prove model performance or credit-policy validity.
