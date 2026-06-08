# SDK Decision Boundary Example

This example shows the minimal Ledge Python SDK Core in ordinary Python code.
It does not use `.ledge` files. It models a small customer-support refund
routing boundary with deterministic fake AI-like outputs.

The example is synthetic and local only:

- no API keys;
- no real customer data;
- no real refund system;
- no production workflow;
- no compliance claim.

Run from a source checkout:

```bash
python examples/sdk_decision_boundary/app.py
```

Expected markers:

- `ALLOW_REFUND_ROUTE`
- `ROUTE_TO_HUMAN_REVIEW`
- `BLOCK_MISSING_VALUE`
- `UNSAFE_UNWRAP_REJECTED`
- `EVIDENCE_RECORDED`

The SDK handles uncertain values at API/runtime level. Python static linting or
type-checker enforcement is planned for a later phase.
