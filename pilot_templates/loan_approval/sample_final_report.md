# Sample Final Report: Synthetic Loan Approval Boundary

This is a sample report shape for a shadow-mode pilot. It uses synthetic data
only and does not establish production, credit, lending, legal, or compliance
readiness.

## Executive Summary

The dry run evaluated five synthetic loan-approval boundary cases against a
small policy. The exercise demonstrated how deterministic rules and AI-derived
risk signals can be separated, how confidence thresholds can be made explicit,
and how fallback to human review can be recorded.

## Boundary Analyzed

- Workflow: synthetic loan approval review.
- AI-derived signal: synthetic risk label and confidence.
- Possible dry-run actions: `APPROVE_ALLOWED`, `ROUTE_TO_HUMAN_REVIEW`,
  `REJECT_ALLOWED`.
- Production action taken: none.

## Policy Used

- Approve only when label is `low_risk` and confidence is at least `0.85`.
- Reject only when label is `high_risk` and confidence is at least `0.85`.
- Route to human review for missing evidence, deterministic review flags,
  ambiguous labels, or low confidence.

## Cases Evaluated

- `high_confidence_approve`
- `low_confidence_review`
- `high_confidence_reject`
- `ambiguous_case`
- `missing_evidence_case`

## Deterministic Rule Findings

The dry run showed that missing evidence and hard review flags route to human
review before an AI-derived approval can be considered.

## AI-Derived Signal Findings

High-confidence low-risk and high-risk signals can reach simulated allow/reject
paths when deterministic rules pass. Low-confidence and ambiguous signals route
to review.

## Fallback/Human Review Summary

Three of five cases route to human review in the sample fixture. This includes
low confidence, ambiguity, and missing evidence.

## Audit/Calibration Note

This dry run does not write a Ledge audit database and does not evaluate real
model calibration. A real pilot would need approved data handling, audit sample
collection, outcome tracking, and calibration review.

## What Ledge Demonstrated

- A pilot can define a decision boundary as fixture plus policy.
- Deterministic checks can be separated from AI-derived signals.
- Confidence thresholds and fallback behavior can be reviewed.
- The resulting report can document what happened and what was not proven.

## What Ledge Did Not Demonstrate

- Model correctness.
- Calibrated probability.
- A valid credit model.
- A real lending decision system.
- Production-critical readiness.
- Legal or regulatory compliance.

## Recommendation

Use this dry-run format only as a starting point for technical review. A real
pilot should remain shadow-mode unless additional integration, monitoring,
security review, legal review, and domain review are explicitly scoped.

## Next Steps

- Replace synthetic fixtures with approved pilot fixtures, if available.
- Review policy thresholds with domain reviewers.
- Decide what audit evidence should be collected.
- Decide whether outcome data is available for calibration.
- Document limitations before any real workflow integration is considered.
