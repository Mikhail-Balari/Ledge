# Confidence Evidence Examples

These examples use synthetic customer support refund routing data.

Run confidence evidence evaluation:

```bash
ledge confidence-eval examples/confidence/fixture.json
ledge confidence-eval examples/confidence/fixture.json --format json
```

Run calibration reporting:

```bash
ledge calibration-report examples/confidence/outcomes.json
ledge calibration-report examples/confidence/outcomes.json --format json
```

The confidence report shows evidence sources, warnings, redaction posture, and a final conservative score. The calibration report shows Brier score, simplified ECE, sample-size warnings, and cautious threshold guidance when enough historical outcomes exist.

These reports do not provide a truth guarantee, legal compliance guarantee, production readiness claim, or formal verification. The future tamper-evident ledger is a later phase.
