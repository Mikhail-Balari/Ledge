# Python Integration Example

This example shows how a normal Python application can delegate only an
AI decision boundary to Ledge.

It is synthetic demo code only. It does not use real data, does not call a real
AI backend, does not touch production systems, and is not a credit model or a
lending decision system.

Run from the repository root:

```bash
python examples/python_integration/app.py
```

The Python app handles ordinary workflow tasks:

- loading a JSON fixture;
- preparing deterministic inputs;
- choosing a synthetic backend response for each case;
- printing an application-level summary.

Ledge handles the boundary where an AI-derived classification could become an
action. The app calls `ledge_lang.checked_run(...)`, so the static Uncertain
checker runs before each boundary program executes.

This is not a full SDK, gateway, sidecar, hosted service, or production
integration pattern. It is a minimal alpha example for reviewing the boundary
between normal Python code and checked Ledge execution.
