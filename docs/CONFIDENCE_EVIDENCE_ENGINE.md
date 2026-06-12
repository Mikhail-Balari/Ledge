# Confidence Evidence Engine

## What it is

The Confidence Evidence Engine treats confidence as a conclusion backed by
explicit evidence, not as a magic number. It gives Python applications and CLI
workflows a structured way to record why a confidence score exists before an AI
output crosses into a decision or action boundary.

This is an alpha feature. It is designed for local inspection, CI checks,
examples, and shadow-mode review workflows.

## What it records

Confidence evidence records can include:

- boundary id
- evidence id
- score
- evidence sources
- warnings
- schema version
- policy id and policy hash where available
- input and output hashes where available
- redaction posture
- evidence hash

The evidence hash is computed from canonical evidence serialization and excludes
the `evidence_hash` field itself.

## Evidence sources

Phase 3 includes deterministic evidence helpers for:

- schema validation evidence
- ensemble agreement evidence
- logprob signal evidence
- conservative scoring evidence
- calibration report evidence

Ensemble agreement measures exact output stability, not truth. Logprob evidence
uses backend-provided logprobs when available and records when they are
unavailable. Conservative scoring does not boost above the base score and hard
schema/type failures dominate the final score.

## CLI usage

```bash
ledge confidence-eval examples/confidence/fixture.json
ledge confidence-eval examples/confidence/fixture.json --format json
ledge calibration-report examples/confidence/outcomes.json
ledge calibration-report examples/confidence/outcomes.json --format json
```

The example data is synthetic customer support refund routing data. It requires
no API keys and no external service.

## SDK interoperability

Legacy SDK evidence remains supported:

```python
from ledge_lang.sdk import ConfidenceEvidence
```

The audit-ready evidence object is available from:

```python
from ledge_lang.confidence import ConfidenceEvidence
```

`Uncertain(..., evidence=...)` normalizes evidence through a private SDK
interoperability layer. Legacy SDK evidence, audit-ready confidence evidence,
unknown evidence objects, and malformed evidence-like objects are handled
explicitly. Unknown or malformed evidence is not silently trusted.

## Redaction posture

Reports do not expose raw source details or source metadata by default. They
prefer hashes, safe metadata, source summaries, warning names, and key lists.
Raw-like metadata is redacted or warning-marked so reviewers can see that
storage controls should be checked.

The helper APIs hash raw input/output-like values instead of storing them.
Unsupported objects are rejected rather than hashed through Python `repr()`.

## Calibration limitations

Calibration requires historical outcomes. If there are not enough outcomes, the
report emits `low_sample_size` and avoids calibrated-confidence claims.

Brier score and simplified ECE are diagnostic reports. They are not proof of
truth, not proof of future correctness, and not legal or compliance evidence by
themselves.

## What it does not claim

The Confidence Evidence Engine:

- does not guarantee truth
- does not prevent hallucinations
- does not certify legal compliance
- is not production-ready or enterprise-ready as an alpha
- is not formal verification
- is not an audit-proof or immutable ledger
- is not blockchain-secured

The future tamper-evident decision ledger is Phase 4 work.

## Relationship to future ledger

Phase 3 produces audit-ready confidence evidence objects and redaction-aware
reports. Phase 4 may turn those evidence objects into tamper-evident decision
logs with explicit event hashes and previous-event hashes.

Phase 3 does not persist hidden logs and does not create a decision ledger.
