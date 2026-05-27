# Python Integration

Ledge can be used around a narrow AI decision boundary without rewriting an
entire Python application.

The current integration path is intentionally small: a Python caller invokes
`ledge_lang.checked_run(...)` on a Ledge boundary program. That call runs the
static Uncertain checker before execution. If the boundary program uses an
AI-derived `Uncertain[T]` value without a recognized confidence guard,
`when(...)`, or an explicit unsafe escape hatch, execution is refused.

This is alpha integration guidance. It is not a full SDK, enterprise gateway,
sidecar, hosted service, production deployment pattern, or compliance workflow.

## What Remains Normal Python

Keep ordinary application work in Python:

- HTTP handlers, queues, jobs, and orchestration;
- database access;
- request validation;
- deterministic business rules;
- fixture loading and test harnesses;
- logging, monitoring, and deployment glue.

Use Ledge only where an AI-derived value could become an action, such as
approve, reject, escalate, route, write, publish, refund, bill, or trigger a
tool/API.

## What Belongs In Ledge

A Ledge boundary should contain the minimum logic needed to make uncertainty
handling explicit:

- the AI call or AI-derived signal;
- the confidence threshold;
- the safe extraction point;
- fallback or human-review behavior;
- output labels that distinguish deterministic rules from AI-derived choices.

## Checked Python Execution

Use `checked_run(...)` for safety-gated Python embedding:

```python
from ledge_lang import checked_run

source = """
define r as classify("invoice") using ["release_payment", "hold_payment"]
if confidence_of(r) >= 0.85:
    show value_of(r)
else:
    show "ROUTE_TO_HUMAN_REVIEW"
"""

lines, _ = checked_run(source)
```

`checked_run(...)` runs the static checker first. If type issues are present,
it raises `LedgeError` before executing the program.

`run(...)` is different. It is the low-level interpreter entry point used by
tests and embedding code that intentionally wants direct execution. It bypasses
the static checker by design. Production-like callers that want the safety gate
should use `checked_run(...)` or run `ledge check --types` before execution.

## Example

See [`examples/python_integration/`](../examples/python_integration/).

Run:

```bash
python examples/python_integration/app.py
```

The example loads a synthetic JSON fixture in Python, passes each decision
boundary through `checked_run(...)`, and uses a synthetic backend response so
the example requires no API key and no real data.

The output is intentionally labeled:

- synthetic demo only;
- not a credit model;
- not a lending decision system;
- not production or compliance software.

## Handling Checker Failures

When `checked_run(...)` raises `LedgeError`, the caller should treat the
boundary as blocked. The error message includes static checker issues so the
program can be fixed before execution.

Do not catch the error and continue with a business action unless that bypass
is explicit, reviewed, and documented.

## CI Checking

Use `scripts/ledge_check_ci.py` to check `.ledge` files in a repository:

```bash
python scripts/ledge_check_ci.py ledge_lang/demos examples/python_integration
```

The script recursively finds `.ledge` files, runs:

```bash
python -m ledge_lang.cli check --types <file>
```

and exits nonzero if any file fails.

## What This Does Not Demonstrate

- A full Python SDK.
- A gateway, sidecar, hosted service, or policy runtime.
- Production deployment.
- Legal or regulatory compliance.
- Model correctness.
- Calibrated confidence.
- Security isolation for untrusted code.

This is a minimal alpha integration example around one checked decision
boundary.
