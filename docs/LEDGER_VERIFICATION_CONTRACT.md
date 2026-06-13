# Ledger Verification Contract

This document defines expected verifier behavior before implementation. It is a
contract for Phase 4 Slice 1 and later.

Slice 2 adds append-oriented JSONL storage and a local manifest foundation, but
does not implement the full verifier output contract. Full human-readable and
machine-readable verifier reports remain future Slice 3 work.

## Output Modes

The verifier must produce:

- human-readable output for operators, reviewers, and incident responders;
- machine-readable JSON output for CI, governance tools, and AI review packs.

The JSON output should be deterministic enough for tests and automation.

## Verification Statuses

Allowed verification statuses:

- `passed`
- `passed_with_warnings`
- `failed`

`passed` means the ledger chain, schema, manifest, and redaction posture passed
all required checks.

`passed_with_warnings` means no critical integrity failure was found, but review
warnings exist.

`failed` means at least one critical finding was found.

## Finding Severities

Allowed finding severities:

- `info`
- `warning`
- `critical`

Critical findings should fail verification.

## Required Report Fields

The verifier should report:

- event count;
- first event hash;
- last event hash;
- chain validity;
- manifest validity;
- schema validity;
- redaction posture validity;
- critical findings;
- warnings;
- recommended review focus.

## Example JSON Verification Output

```json
{
  "verification_schema": "ledge.ledger_verification.v1",
  "status": "passed_with_warnings",
  "event_count": 3,
  "first_event_hash": "sha256:first_event_hash_example",
  "last_event_hash": "sha256:last_event_hash_example",
  "chain_valid": true,
  "manifest_valid": true,
  "schema_valid": true,
  "redaction_posture_valid": true,
  "critical_findings": [],
  "warnings": [
    {
      "severity": "warning",
      "code": "low_sample_size",
      "message": "Calibration evidence contains fewer outcomes than the configured minimum."
    }
  ],
  "recommended_review_focus": [
    "Review low-sample calibration warnings before relying on threshold guidance.",
    "Confirm blocked and escalated actions match the expected decision policy."
  ],
  "limitations": [
    "tamper-evident, not tamper-proof",
    "audit review package, not compliance certification",
    "append-oriented local records, not immutable storage"
  ]
}
```

## Verification Semantics

The verifier should check the ledger as a chain of semantic decision boundary
events, not generic logs. It should report what failed, where it failed, and
which review path is recommended.

The verifier should not claim legal compliance, production readiness, formal
verification, truth, hallucination prevention, or immutable storage.

Until the full verifier is implemented, the Slice 2 store performs local
structural checks while reading and appending events:

- each JSONL line must parse as JSON;
- each line must validate as a `DecisionEvent`;
- event hashes must verify;
- sequence numbers must be continuous;
- `previous_event_hash` must match the previous event.

These checks are a foundation for the verifier, not a replacement for the full
verification report contract above.
