# Python Integration

This page describes Ledge 1.5.0 Alpha integration surfaces.

Ledge can be used around a narrow AI decision boundary without rewriting an
entire Python application.

The current integration path is intentionally small: a Python caller invokes
`ledge_lang.checked_run(...)` on a Ledge boundary program. That call runs the
static Uncertain checker before execution. If the boundary program uses an
AI-derived `Uncertain[T]` value without a recognized confidence guard,
`when(...)`, or an explicit unsafe escape hatch, execution is refused.

This is alpha integration guidance. It is not a full SDK, enterprise gateway,
sidecar, hosted service, production deployment pattern, or compliance workflow.

## Python SDK Core

The Python SDK Core, available from Ledge 1.4.0 Alpha onward, provides a
minimal way to model uncertain values and decision policies in normal Python
code:

```python
from ledge_lang.sdk import DecisionPolicy, Uncertain

policy = DecisionPolicy(min_confidence=0.8, name="refund-routing")
result = Uncertain("refund_route_allowed", confidence=0.91).handle(policy)

if result.allowed:
    print(result.value)
```

This SDK surface is API-level and runtime-level handling. It does not replace
the DSL static checker, and it does not statically enforce Python code yet.
Ledge 1.5.0 Alpha adds `ledge lint-python` for AST-based CI enforcement of
common unsafe Python decision-boundary patterns, but it is not complete Python
semantic verification and it is not a mypy or Pyright plugin.
`ConfidenceEvidence` is currently a minimal metadata container, not a calibrated
confidence engine.

For a deterministic example, run:

```bash
python examples/sdk_decision_boundary/app.py
```

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

## Installed Demo Command

After installing the package, run:

```bash
ledge python-integration-demo
```

The installed command loads packaged synthetic resources and runs the boundary
through `ledge_lang.checked_run(...)`. It requires no source checkout, no API
key, and no real data.

## Source-Checkout Example

See [`examples/python_integration/`](../examples/python_integration/) in a
source checkout.

Run:

```bash
python examples/python_integration/app.py
```

The wrapper loads the same synthetic example through the package module, passes
each decision boundary through `checked_run(...)`, and uses a synthetic backend
response so the example requires no API key and no real data.

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

After installing the package, use `ledge ci-check` to check
`.ledge` files in a repository:

```bash
ledge ci-check path/to/your/ledge/files
```

From a source checkout, the repository example paths and wrapper remain
available:

```bash
ledge ci-check ledge_lang/demos examples/python_integration
python scripts/ledge_check_ci.py ledge_lang/demos examples/python_integration
```

Both forms recursively find `.ledge` files, run:

```bash
python -m ledge_lang.cli check --types <file>
```

and exits nonzero if any file fails.

## Python SDK Linting

Use `ledge lint-python` to scan Python files for common unsafe SDK patterns:

```bash
ledge lint-python src tests --config ledge.toml
```

The linter is AST-based. It tracks straightforward local uses of
`Uncertain(...)`, `uncertain_from_validation(...)`, deterministic fake client
predictions, and `DecisionResult` values returned by `.handle(...)`.

It detects patterns such as:

- `unsafe_unwrap()` without a non-empty reason;
- direct `.value` access on tracked `Uncertain` values;
- configured critical actions receiving an unhandled uncertain value;
- `DecisionResult.value` passed to a configured critical action outside an
  `if decision.allowed:` or `if decision.action == "allow":` guard.

It is intended to catch meaningful unsafe patterns before merge. It does not
provide complete semantic verification for arbitrary Python, and it does not
yet perform complete cross-file or interprocedural dataflow analysis. Dynamic
flows, aliasing, and framework-specific behavior may require additional
configuration or review.

For a source-checkout example, run:

```bash
ledge lint-python examples/python_linter/safe_usage.py --config examples/python_linter/ledge.toml
ledge lint-python examples/python_linter/unsafe_usage.py --config examples/python_linter/ledge.toml
```

## What This Does Not Demonstrate

- A full Python SDK beyond the minimal SDK Core.
- A gateway, sidecar, hosted service, or policy runtime.
- Complete Python semantic verification.
- A mypy or Pyright plugin.
- Production deployment.
- Legal or regulatory compliance.
- Model correctness.
- Calibrated confidence.
- Security isolation for untrusted code.

This is a minimal alpha integration example around one checked decision
boundary.
