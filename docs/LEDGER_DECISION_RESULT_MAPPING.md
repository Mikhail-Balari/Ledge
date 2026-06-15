# DecisionResult Ledger Mapping

This document defines the safe mapping contract between SDK `DecisionResult`
objects and ledger `DecisionEvent` records. Slice 9 defined the contract.
Slice 10 implements the narrow `record_decision_result(...)` adapter without
changing the fail-closed mapping rules.

## Mapping Table

| Ledger field | Source | Required? | Can be inferred today? | Notes |
| --- | --- | --- | --- | --- |
| `event_id` | Auto-managed by recorder | Yes | Yes | `LedgerRecorder` can generate a safe unique event id. Explicit ids may also be supplied. |
| `sequence` | Auto-managed by recorder | Yes | Yes | Derived from `DecisionLedger.next_sequence()`. |
| `timestamp_utc` | Auto-managed by recorder | Yes | Yes | Generated as UTC ending in `Z` unless explicitly supplied. |
| `boundary_id` | Explicit user/system context | Yes | No | Must identify the decision boundary contract. Not present on `DecisionResult`. |
| `boundary_version` | Explicit user/system context | Yes | No | Must identify the boundary contract version. Not present on `DecisionResult`. |
| `policy_hash` | Explicit user/system context | Yes | No | `DecisionPolicy.name` is not a policy hash. A canonical policy hash must be supplied. |
| `evidence_hash` | Explicit hash or validated evidence metadata | Yes | Sometimes | Can only be used from normalized evidence metadata when `evidence_hash` is present and validated. Otherwise explicit. |
| `input_hash` | Explicit user/system hash/reference | Yes | No | Raw input must not be serialized. The hash or reference must be supplied. |
| `output_hash` | Explicit user/system hash/reference | Yes | No | Raw output must not be serialized. The hash or reference must be supplied. |
| `confidence_score` | Available from SDK | Yes | Yes | `DecisionResult.confidence` is explicit and normalized by the SDK. |
| `action` | Available from SDK or explicit override | Yes | Partly | `DecisionResult.action` is explicit, but adapters must document how SDK actions map to ledger action semantics. |
| `policy_result` | Explicit user/system value | Yes | No | Current SDK actions do not exactly match ledger policy result values. Require explicit value until a stable mapping exists. |
| `warnings` | Available from SDK or explicit override | Yes | Yes | `DecisionResult.warnings` is explicit. Explicit override may be useful when the caller adds recorder warnings. |
| `redaction_profile` | Explicit user/system context | Yes | No | Comes from `LedgerRecordContext`. |
| `previous_event_hash` | Auto-managed by recorder | Yes | Yes | Derived from `DecisionLedger.expected_previous_hash()`. |
| `current_event_hash` | Auto-managed by recorder | Yes | Yes | Computed by `DecisionEvent.create(...)`. |
| `trace_id` | Explicit optional correlation | No | No | Optional correlation field; must be safe string if supplied. |
| `span_id` | Explicit optional correlation | No | No | Optional correlation field; must be safe string if supplied. |
| `request_id` | Explicit optional correlation | No | No | Optional correlation field; must be safe string if supplied. |
| `actor_id_hash` | Explicit optional correlation | No | No | Must be a hash or safe identifier, not raw actor data. |
| `service_name` | Explicit optional correlation | No | No | Optional safe service name. |
| `environment` | Explicit optional correlation | No | No | Optional safe environment label. |

## Safe Today

The following fields are safely available from current SDK objects:

- `confidence_score` from `DecisionResult.confidence`;
- warnings from `DecisionResult.warnings`;
- action from `DecisionResult.action`, as an SDK action string;
- evidence hash only if normalized evidence metadata contains a validated
  `evidence_hash`.

The following fields are auto-managed by `LedgerRecorder`:

- `event_id`;
- `sequence`;
- `timestamp_utc`;
- `previous_event_hash`;
- `current_event_hash`.

## Explicit Required Inputs

The following fields must be explicitly supplied today:

- `boundary_id`;
- `boundary_version`;
- `policy_hash`;
- `input_hash`;
- `output_hash`;
- `redaction_profile`;
- `policy_result`;
- `evidence_hash` when not already present as a validated evidence hash;
- optional correlation fields when needed.

## Action And Policy Result

The SDK currently uses actions such as:

- `allow`
- `human_review`
- `block`

The ledger uses policy results such as:

- `allow`
- `allow_with_warning`
- `block`
- `escalate`

These vocabularies are related but not identical. The Slice 10 adapter does not
silently translate `human_review` into `escalate`; `policy_result` is explicit.

## Evidence Hash

Phase 3 evidence compatibility can place a safe `evidence_hash` in
`DecisionResult.metadata` when audit-ready confidence evidence is attached.
Future adapters may use that field only when it is present as a string and has
passed the SDK evidence normalization path.

The Slice 10 adapter keeps this conservative and requires `evidence_hash`
explicitly.

## Input And Output Hashes

`input_hash` and `output_hash` are ledger identity fields. They must be hashes
or safe external references. A future adapter must never derive them by
serializing `Uncertain.value`, `DecisionResult.value`, raw prompts, model
outputs, messages, completions, responses, or payloads.

## Fail-Closed Mapping

The adapter must not record an event when:

- a required field is missing;
- a required field is ambiguous;
- an SDK field has multiple plausible ledger meanings;
- a raw payload is supplied;
- a hash/reference is invalid;
- warnings or metadata cannot be normalized safely.

No event should be partially appended. If mapping fails, the ledger file should
not gain a new line.

## Adapter Test Plan

The implementation tests prove:

- records only when all required fields are explicit;
- rejects missing evidence hash;
- rejects missing input hash;
- rejects missing output hash;
- rejects ambiguous action;
- rejects ambiguous policy result;
- never serializes `Uncertain.value`;
- returned event verifies;
- ledger verifies after append;
- works with existing `LedgerRecorder`;
- fail-closed behavior produces no new ledger line.

Slice 11 also adds an end-to-end source checkout example proving the mapped
result can flow through ledger verification, local audit review export, and AI
review pack generation without storing raw decision values.

## Non-Goals

This mapping contract is not hidden persistence, automatic audit logging,
compliance certification, remote anchoring, immutable storage, or blockchain.
It does not guarantee truth or prevent hallucinations.
