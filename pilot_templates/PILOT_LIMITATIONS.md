# Pilot Limitations

Ledge pilots must keep these limitations explicit:

- Ledge does not prove model correctness.
- Ledge does not guarantee compliance.
- Ledge does not replace monitoring or evals.
- Ledge does not replace human review.
- Ledge does not prevent hallucinations.
- Ledge is not a security boundary against a malicious local operator.
- Synthetic fixtures do not prove production performance.
- Shadow mode does not affect production.
- Confidence can be wrong or poorly calibrated.
- Audit evidence is useful within its documented threat model, not tamper-proof.

Any move beyond shadow mode requires additional integration, testing,
monitoring, security review, domain review, and legal/compliance review where
appropriate.
