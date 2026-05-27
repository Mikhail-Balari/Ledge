# Expected Dry-Run Results

These results are for the synthetic loan approval dry run only. They are not
credit decisions and are not production workflow outcomes.

| Case | Expected action | Why |
| --- | --- | --- |
| `high_confidence_approve` | `APPROVE_ALLOWED` | Deterministic checks pass, label is `low_risk`, and confidence is `0.91`, above the `0.85` approve threshold. |
| `low_confidence_review` | `ROUTE_TO_HUMAN_REVIEW` | Deterministic checks pass, but confidence is `0.61`, below the `0.65` review minimum. |
| `high_confidence_reject` | `REJECT_ALLOWED` | Deterministic checks pass, label is `high_risk`, and confidence is `0.89`, above the `0.85` threshold. |
| `ambiguous_case` | `ROUTE_TO_HUMAN_REVIEW` | A deterministic contract mismatch/hard review flag is present, and the model label is ambiguous. |
| `missing_evidence_case` | `ROUTE_TO_HUMAN_REVIEW` | Missing evidence overrides the high-confidence low-risk AI signal. |

The important behavior is not that any case is a correct credit decision. The
important behavior is that deterministic checks, confidence thresholds, AI
labels, fallback behavior, and human review are visible in the dry-run output.
