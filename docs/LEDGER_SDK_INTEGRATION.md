# Ledger SDK Integration Contract

Phase 4 Slice 9 defined the contract for SDK-to-ledger integration. Phase 4
Slice 10 implements the narrow `record_decision_result(...)` adapter within
that contract.

The goal is to preserve Ledge's boundary principle: an AI-derived value should
cross into action only through explicit, checkable, auditable, and blockable
decision handling. Ledger integration must make that boundary clearer. It must
not invent missing facts.

## Current SDK Surface

The SDK currently exposes:

- `Uncertain[T]`: value, confidence, source, metadata, warnings, and optional
  evidence.
- `DecisionPolicy`: threshold and policy action choices.
- `DecisionResult`: action, allowed flag, value, confidence, reason, optional
  policy name, warnings, and metadata.
- SDK evidence compatibility metadata, including normalized confidence evidence
  fields when available.
- `LedgerRecorder`: explicit recording API that manages sequence numbers,
  previous hashes, timestamps, event ids, event hashes, and append behavior.
- `record_decision_result(...)`: safe adapter that records a `DecisionResult`
  only when ledger context, hashes, and policy result are explicit.

This is enough for a user or application to record decision events when it has
explicit boundary context and safe hashes. It is still not enough for Ledge to
infer all ledger fields from `DecisionResult` alone.

## Safe Integration Principle

A `DecisionResult` can only be recorded into the ledger when the following
fields are explicitly available or explicitly supplied:

- `boundary_id`
- `boundary_version`
- `policy_hash`
- `evidence_hash`
- `input_hash`
- `output_hash`
- `confidence_score`
- `action`
- `policy_result`
- `warnings`
- `redaction_profile`

The adapter must never guess these values.

If any required field is ambiguous or unavailable, the adapter must fail
closed, require an explicit parameter, and avoid creating a ledger event.

## What Can Be Used Today

`DecisionResult.confidence` is an explicit confidence score and can be used as
`confidence_score`.

`DecisionResult.action` is explicit, but it is an SDK action such as `allow`,
`human_review`, or `block`. The ledger `policy_result` vocabulary is `allow`,
`allow_with_warning`, `block`, and `escalate`. The Slice 10 adapter requires
`policy_result` explicitly and does not infer it from SDK action.

`DecisionResult.warnings` is explicit and can be used as ledger warnings.

`DecisionResult.metadata` may contain normalized evidence metadata. It may help
populate `evidence_hash` only when a validated hash field is present and
unambiguous. It must not be searched for raw payloads or arbitrary objects.

`DecisionResult.value` must never be serialized into the ledger.

## What Requires Explicit Context

The following fields are not safely inferable from the current SDK result by
itself:

- `boundary_id`
- `boundary_version`
- `policy_hash`
- `evidence_hash`, unless a validated normalized evidence hash is present
- `input_hash`
- `output_hash`
- `redaction_profile`
- optional correlation fields

These must come from `LedgerRecordContext`, explicit adapter parameters, or a
future SDK object that carries validated ledger-safe references.

## Adapter Shape

Slice 10 adds an adapter shaped like:

```python
record_decision_result(
    ledger,
    result,
    *,
    context: LedgerRecordContext,
    evidence_hash: str,
    input_hash: str,
    output_hash: str,
    action: str | None = None,
    policy_result: str,
    warnings: list[str] | None = None,
    initialize: bool = False,
) -> DecisionEvent
```

Rules:

- required hashes are explicit;
- action may come from `DecisionResult.action` only when the caller does not
  provide an explicit override;
- policy result is always explicit;
- confidence score comes from `DecisionResult.confidence`;
- warnings may come from `DecisionResult.warnings` when no explicit warnings
  are supplied;
- raw values from `Uncertain.value` or `DecisionResult.value` must never be
  serialized.

## Fail-Closed Behavior

SDK ledger adapters must follow these rules:

- missing mapping field means no event is recorded;
- ambiguous SDK field means no event is recorded;
- raw payload fields are rejected;
- invalid hash or reference fields are rejected;
- no silent fallback;
- no partial ledger append;
- no hidden persistence.

## Raw Data Boundary

Ledger integration must not store raw prompts, completions, messages, inputs,
outputs, responses, payloads, customer data, secrets, API keys, or direct
personal data. The ledger records hashes, references, warnings, policy results,
actions, and integrity metadata.

## Implementation Tests

The adapter implementation tests that it:

- records only when all required fields are explicit or validated;
- rejects missing evidence hash;
- rejects missing input hash;
- rejects missing output hash;
- rejects ambiguous action;
- rejects ambiguous policy result;
- never serializes `Uncertain.value`;
- returns an event that verifies;
- leaves the ledger verifying after append;
- works through existing `LedgerRecorder`;
- fails closed without adding a ledger line.

## Source Checkout Example

Slice 11 adds `examples/ledger/sdk_decision_result_to_ledger.py` as a
source-checkout workflow example. It constructs a low-stakes SDK
`DecisionResult`, records it with explicit hashes and `LedgerRecordContext`,
builds a manifest, verifies the ledger, exports a local audit review package,
and writes an AI-readable review pack.

The example is deliberately hash-only for evidence, input, and output. It does
not serialize `DecisionResult.value` or raw SDK metadata into the ledger.

## Anti-Claims

SDK ledger integration does not guarantee truth, prevent hallucinations, certify
legal compliance, make local files immutable, provide production readiness, or
replace human review.
