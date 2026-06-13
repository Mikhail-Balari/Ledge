# Ledger AI Review Pack

The Ledger AI Review Pack is a proposed machine-readable package for another
AI, agent, reviewer, or governance workflow to consume Ledge verification
results without parsing human prose.

It must not ask the reviewing AI to trust the original AI output. It should ask
the reviewing AI to inspect the boundary, evidence, policy result, action,
warnings, and ledger integrity.

## Purpose

The review pack should help reviewers answer:

- Which decision boundaries were exercised?
- Which actions were allowed, blocked, or escalated?
- Which evidence hashes and policy hashes were attached?
- Which warnings were present?
- Did the ledger chain verify?
- What should a human reviewer inspect first?

## Proposed Fields

- `review_schema`
- `ledger_status`
- `decision_boundaries`
- `events_checked`
- `blocked_actions`
- `allowed_actions`
- `warnings_count`
- `critical_findings`
- `recommended_review_focus`
- `integrity_summary`
- `limitations`

## Example JSON

```json
{
  "review_schema": "ledge.ai_review_pack.v1",
  "ledger_status": "passed_with_warnings",
  "decision_boundaries": [
    "refund_routing"
  ],
  "events_checked": 3,
  "blocked_actions": [
    {
      "boundary_id": "refund_routing",
      "event_id": "evt_refund_0002",
      "policy_result": "block",
      "reason": "confidence below policy threshold"
    }
  ],
  "allowed_actions": [
    {
      "boundary_id": "refund_routing",
      "event_id": "evt_refund_0001",
      "policy_result": "allow_with_warning",
      "warnings": [
        "logprobs_unavailable"
      ]
    }
  ],
  "warnings_count": 2,
  "critical_findings": [],
  "recommended_review_focus": [
    "Inspect all allow_with_warning events.",
    "Confirm blocked actions were not executed downstream.",
    "Review confidence evidence hashes for events with missing logprob signals."
  ],
  "integrity_summary": {
    "chain_valid": true,
    "manifest_valid": true,
    "schema_valid": true,
    "redaction_posture_valid": true,
    "first_event_hash": "sha256:first_event_hash_example",
    "last_event_hash": "sha256:last_event_hash_example"
  },
  "limitations": [
    "The review pack does not prove the original AI output was true.",
    "The review pack is not compliance certification.",
    "The ledger is tamper-evident, not tamper-proof."
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
