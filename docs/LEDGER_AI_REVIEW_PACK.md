# Ledger AI Review Pack

The Ledger AI Review Pack is a machine-readable package for another AI, agent,
reviewer, CI job, or governance workflow to consume Ledge verification results
without parsing human prose.

It must not ask the reviewing AI to trust the original AI output. It should ask
the reviewing AI to inspect the boundary, evidence hashes, policy result,
action, warnings, and ledger integrity.

## Purpose

The review pack should help reviewers answer:

- Which decision boundaries were exercised?
- Which actions were allowed, blocked, or escalated?
- Which evidence hashes and policy hashes were attached?
- Which warnings were present?
- Did the ledger chain verify?
- What should a human reviewer inspect first?

## Fields

- `review_schema`
- `generated_at_utc`
- `source_ledger`
- `manifest_used`
- `boundary_filter`
- `ledger_status`
- `events_checked`
- `events_in_scope`
- `decision_boundaries`
- `integrity_summary`
- `policy_results_count`
- `warnings_count`
- `actions_count`
- `critical_findings_count`
- `findings_summary`
- `recommended_review_focus`
- `event_summaries`
- `limitations`

`event_summaries` contain safe event-level fields such as event id, sequence,
boundary id, policy hash, evidence hash, input/output hashes, confidence score,
policy result, action, warning count, redaction profile, and event hashes. They
do not include raw prompts, completions, messages, inputs, outputs, responses,
or payloads.

When a boundary filter is used, `event_summaries` includes only matching
events. The `integrity_summary` still comes from the full source ledger because
filtering breaks full-chain continuity.

## CLI

Slice 7 adds:

```bash
ledge ledger-review-pack --store ledge_audit.jsonl --out ai_review_pack.json
ledge ledger-review-pack --store ledge_audit.jsonl --manifest ledger_manifest.json --out ai_review_pack.json
ledge ledger-review-pack --store ledge_audit.jsonl --boundary refund_decision --out ai_review_pack.json
ledge ledger-review-pack --store ledge_audit.jsonl --manifest ledger_manifest.json --boundary refund_decision --out ai_review_pack.json
ledge ledger-review-pack --store ledge_audit.jsonl --out ai_review_pack.json --force
```

## Example JSON

```json
{
  "review_schema": "ledge.ai_review_pack.v1",
  "generated_at_utc": "2026-06-13T12:00:00Z",
  "source_ledger": "ledge_audit.jsonl",
  "manifest_used": "ledger_manifest.json",
  "boundary_filter": null,
  "ledger_status": "passed_with_warnings",
  "events_checked": 3,
  "events_in_scope": 3,
  "decision_boundaries": [
    "refund_routing"
  ],
  "integrity_summary": {
    "chain_valid": true,
    "manifest_valid": true,
    "schema_valid": true,
    "redaction_posture_valid": true,
    "first_event_hash": "sha256:first_event_hash_example",
    "last_event_hash": "sha256:last_event_hash_example"
  },
  "policy_results_count": {
    "allow_with_warning": 1,
    "block": 1,
    "escalate": 1
  },
  "actions_count": {
    "block_refund": 1,
    "route_to_manual_review": 1,
    "ship_refund_response": 1
  },
  "warnings_count": 2,
  "critical_findings_count": 0,
  "findings_summary": [],
  "recommended_review_focus": [
    "Inspect blocked actions and confirm they were not executed downstream.",
    "Inspect escalated actions and confirm human-review handoff behavior.",
    "Review event warnings by boundary, policy result, action, and evidence hash."
  ],
  "event_summaries": [
    {
      "event_id": "evt_refund_0001",
      "sequence": 1,
      "boundary_id": "refund_routing",
      "policy_hash": "sha256:policy",
      "evidence_hash": "sha256:evidence",
      "confidence_score": 0.82,
      "policy_result": "allow_with_warning",
      "action": "ship_refund_response",
      "warnings_count": 1,
      "redaction_profile": "hash_only",
      "current_event_hash": "sha256:event_hash_example"
    }
  ],
  "limitations": [
    "not compliance certification",
    "tamper-evident, not tamper-proof",
    "append-oriented local records, not immutable storage",
    "does not guarantee truth",
    "does not prevent hallucinations",
    "reviewing AI must not trust original AI output blindly"
  ]
}
```

## Review Guidance

A reviewing AI should not treat `allowed_actions` as correct actions. It should
treat them as actions that crossed a declared policy boundary and should inspect
the policy result, evidence hash, confidence score, warnings, and ledger
integrity.

If the ledger status is `failed`, the reviewing system should prioritize
integrity findings before making any judgment about policy behavior.

The review pack is not legal compliance certification, not a production-ready
governance system, not audit-proof, not tamper-proof, and not immutable
storage. It is a machine-readable review contract over local ledger evidence.
