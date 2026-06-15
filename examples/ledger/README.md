# Ledger SDK Workflow Example

This is a source checkout example for the Phase 4 decision ledger workflow.

It demonstrates a low-stakes support-ticket routing scenario:

```text
DecisionResult -> record_decision_result(...) -> DecisionEvent -> DecisionLedger
-> ledger-verify -> ledger-export -> ledger-review-pack
```

## Run From A Source Checkout

From the repository root:

```bash
python examples/ledger/sdk_decision_result_to_ledger.py
```

To write outputs somewhere else:

```bash
python examples/ledger/sdk_decision_result_to_ledger.py --out .tmp_ledger_example
```

## Files Created

The example writes:

- `support_ticket_ledger.jsonl`: local decision ledger events.
- `ledger_manifest.json`: local ledger manifest.
- `audit_export/`: local audit review package.
- `ai_review_pack.json`: AI-readable review pack.

The expected ledger verification status is `passed` because the example builds
and verifies a matching manifest.

## Inspect With CLI

```bash
ledge ledger-verify --store examples/ledger/out/support_ticket_ledger.jsonl --manifest examples/ledger/out/ledger_manifest.json
ledge ledger-export --store examples/ledger/out/support_ticket_ledger.jsonl --manifest examples/ledger/out/ledger_manifest.json --out examples/ledger/out/audit_export --force
ledge ledger-review-pack --store examples/ledger/out/support_ticket_ledger.jsonl --manifest examples/ledger/out/ledger_manifest.json --out examples/ledger/out/ai_review_pack.json --force
```

The `audit_export/` folder is a local audit review package. The
`ai_review_pack.json` file is an AI-readable review pack for agents,
governance workflows, CI jobs, or reviewers that need structured ledger
integrity and decision-boundary data.

## Safety Posture

The example uses only safe hashes and references:

- `input_hash`
- `output_hash`
- `evidence_hash`

It does not store raw prompts, completions, messages, inputs, outputs,
responses, payloads, customer data, or PII.

## Limitations

This example is not compliance certification.

The ledger is tamper-evident, not tamper-proof.

The ledger is append-oriented local storage, not immutable storage.

Ledge does not guarantee truth.

Ledge does not prevent hallucinations.

The example is low-stakes and synthetic. It does not replace human review,
security controls, compliance review, or operational monitoring.
