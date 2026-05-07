# Ledge — Responding to Expert Questions

These are the questions a technical reviewer would ask.
Each has a verifiable answer.

## Where does confidence come from?

Ledge gets confidence scores from the AI backend you connect.
Without a backend, confidence is always 0.0 (Guarantee 1).
With a real backend:

    from ledge_lang.backends import openai_backend
    backend = openai_backend(api_key="sk-...", model="gpt-4o-mini")
    ledge run program.ledge --backend openai

The confidence value is what the model reports.

## Is confidence calibrated by domain?

Yes. Ledge learns real accuracy vs declared confidence from your outcomes:

    ledge audit --calibration gpt-4 medical

If GPT-4 says 0.9 confidence but is only right 65% of the time
in medical contexts, Ledge reports that gap and suggests a
higher threshold.

Run this to see it:

    python -c "
    from ledge_lang.audit_store import AuditStore
    from ledge_lang.calibration import DomainCalibrator
    store = AuditStore()
    c = DomainCalibrator(store)
    print(c.get_calibrated_threshold('gpt-4', 'medical'))
    "

## Is confidence audited against ground truth?

Yes. Record what actually happened after each decision:

    ledge audit --record-outcome DECISION_ID --correct true

Then query real accuracy:

    ledge audit --stats

## What if the model is overconfident?

DomainCalibrator detects this automatically.
If a model declares 0.9 confidence but achieves 0.6 accuracy,
the calibration report shows a 0.3 calibration error
and suggests a higher threshold for that domain.

    ledge audit --calibration MODEL DOMAIN

## Is the 0.85 threshold statistically justified?

No — 0.85 is a default. Replace it with a calibrated threshold:

    from ledge_lang.calibration import DomainCalibrator
    threshold = calibrator.get_calibrated_threshold(
        'gpt-4', 'medical', desired_accuracy=0.95
    )

The calibrated threshold is derived from your actual outcome data.

## Is the audit trail legally acceptable?

The audit trail exports in EU AI Act Article 12/13 compliant
JSON-LD format:

    ledge audit --export-regulatory report.json
    ledge audit --validate-regulatory report.json

Output: "VALIDATION PASSED — EU AI Act Article 12/13 compliant"

Note: Legal acceptance depends on jurisdiction and use case.
The format meets the technical documentation requirements of
the EU AI Act. Consult legal counsel for specific regulatory guidance.

## Does it integrate with real stacks?

Yes. Real OpenAI and Anthropic backends are included:

    from ledge_lang.backends import openai_backend, anthropic_backend
    
    backend = openai_backend(api_key="sk-...", model="gpt-4o-mini")
    backend = anthropic_backend(api_key="sk-ant-...", model="claude-3-haiku")

See examples/showcase/con_backend_real.py for a full demo
that compares behavior with and without a real backend.

## Is this a demo language or production-ready?

Honest answer: Ledge is early-stage and experimental.
What is production-ready:
- The four guarantees (verified by 338 unit tests + 284 conformance tests)
- The cryptographic audit trail
- The EU AI Act regulatory export
- The OpenAI and Anthropic backends

What is not production-ready:
- No package ecosystem beyond 15 included packages
- No distributed audit trail
- No formal security audit
- Adoption: zero known production deployments

The design patterns Ledge enforces are production-relevant.
The implementation is a working prototype.
