# Decision Ledger Schema

This document defines the proposed Phase 4 `DecisionEvent` schema. It is a
contract document only. Runtime ledger code is not implemented in Slice 0.

Slice 1 implemented the `DecisionEvent` core. Slice 2 adds append-oriented
JSONL storage and a local `LedgerManifest` foundation. The store remains local
append-oriented storage; it is not immutable storage, blockchain, or a
compliance certification mechanism.

## Required Fields

Every `DecisionEvent` should include:

- `schema_version`: ledger event schema version.
- `event_id`: stable unique event identifier.
- `sequence`: monotonic integer sequence within the ledger.
- `timestamp_utc`: normalized UTC timestamp.
- `boundary_id`: decision boundary identifier.
- `boundary_version`: version of the decision boundary contract.
- `policy_hash`: hash of the decision policy used for the boundary.
- `evidence_hash`: hash of the attached confidence evidence.
- `input_hash`: hash of the redacted or canonicalized input posture.
- `output_hash`: hash of the redacted or canonicalized output posture.
- `confidence_score`: final confidence score used by the decision boundary.
- `action`: action requested or produced by the decision result.
- `policy_result`: normalized policy result.
- `warnings`: stable list of warnings present at the boundary.
- `redaction_profile`: redaction posture used for event material.
- `previous_event_hash`: previous canonical event hash, or `null` for the
  first event.
- `current_event_hash`: hash of the canonical event excluding
  `current_event_hash` itself.

## Optional Correlation Fields

The following fields may be included when available and safe:

- `trace_id`
- `span_id`
- `request_id`
- `actor_id_hash`
- `service_name`
- `environment`

These fields are correlation helpers. They must not contain raw prompts,
model outputs, customer data, secrets, API keys, or direct personal data.

## Allowed Values

`policy_result` examples:

- `allow`
- `allow_with_warning`
- `block`
- `escalate`

`redaction_profile` examples:

- `hash_only`
- `redacted_summary`
- `external_reference`

## Canonicalization Rules

Decision events should be canonicalized before hashing.

Rules:

- JSON keys are ordered stably.
- Timestamps use normalized UTC format.
- Hash inputs are deterministic.
- Raw sensitive input and output are not stored in the event.
- Redaction happens before event persistence, and the redaction posture is
  recorded.
- `current_event_hash` excludes `current_event_hash` itself.
- `previous_event_hash` links to the previous canonical event hash.
- Numeric values use JSON-compatible finite numbers only.
- Warnings are deduplicated while preserving order.
- Unknown or unsupported values should fail validation or be represented by
  safe summaries, never by object representations.

## Example Event

```json
{
  "schema_version": "ledge.decision_event.v1",
  "event_id": "evt_refund_0001",
  "sequence": 1,
  "timestamp_utc": "2026-06-12T15:04:05Z",
  "boundary_id": "refund_routing",
  "boundary_version": "refund_routing.v1",
  "policy_hash": "sha256:policy_hash_example",
  "evidence_hash": "sha256:evidence_hash_example",
  "input_hash": "sha256:input_hash_example",
  "output_hash": "sha256:output_hash_example",
  "confidence_score": 0.82,
  "action": "route_to_manual_review",
  "policy_result": "escalate",
  "warnings": [
    "low_sample_size",
    "logprobs_unavailable"
  ],
  "redaction_profile": "hash_only",
  "previous_event_hash": null,
  "current_event_hash": "sha256:current_event_hash_example",
  "trace_id": "trace_refund_demo_001",
  "request_id": "req_refund_demo_001",
  "actor_id_hash": "sha256:actor_hash_example",
  "service_name": "refund-routing-worker",
  "environment": "staging"
}
```

This example is synthetic and low stakes. The hashes are placeholders, not
computed values.

## JSONL Ledger Store

Slice 2 stores decision events as JSONL:

- one canonical `DecisionEvent` JSON object per line;
- no raw input or output payloads;
- each line must validate through the `DecisionEvent` schema;
- blank or malformed lines are treated as corruption, not silently ignored;
- appends enforce monotonic sequence continuity;
- appends enforce `previous_event_hash` continuity.

This is append-oriented local storage. It is append-only by convention plus
verification, not immutable storage.

## Ledger Manifest Foundation

Slice 2 defines a local `LedgerManifest` summary with schema version
`ledge.ledger_manifest.v1`.

Manifest fields:

- `schema_version`
- `ledger_path`
- `event_count`
- `first_event_hash`
- `last_event_hash`
- `created_at_utc`
- `updated_at_utc`
- `ledge_version`

An empty ledger manifest is allowed with `event_count` set to `0` and both
event hashes set to `null`.

For a non-empty ledger:

- `event_count` equals the number of validated ledger events;
- `first_event_hash` equals the first event `current_event_hash`;
- `last_event_hash` equals the last event `current_event_hash`.

The manifest is a local summary and anchor point for later verification. It is
not a security boundary by itself and does not contain raw inputs or outputs.
