# Ledge Comparative Positioning

## Version 1.2.0

This document explains where Ledge is useful today and where it is not
competitive. It does not claim that Ledge is better than Python, JavaScript, Go,
or existing AI frameworks in general.

Ledge is an experimental uncertainty-aware execution layer for programs where
AI model outputs affect control flow. Its useful surface is narrow: make
uncertainty explicit, reject direct use of `Uncertain[T]` values on checked
execution paths, record AI decisions, and provide calibration/audit utilities.

## The Niche

Ledge is aimed at AI decision paths where a program should not silently treat a
model answer as a fact:

- triage, classification, review, routing, and escalation workflows;
- agent or tool paths where model output controls an action;
- systems that need a durable record of AI decisions and confidence values;
- prototypes that need to make confidence-handling mistakes visible early.

It is not a general-purpose Python replacement and it is not a sandbox,
compliance product, or formal verification system.

## Ordinary Python

In ordinary Python, confidence handling is usually a convention:

```python
result = model.classify(text)
label = result["label"]

if label == "urgent":
    escalate()
```

This may be perfectly reasonable when the surrounding application has its own
policy engine, typed wrapper, evals, monitoring, and review process. The common
failure mode is that the confidence path is implicit and easy to skip.

## Ledge

In Ledge, AI primitives return `Uncertain[T]`:

```ledge
define result as classify(text) using ["urgent", "normal"]

if confidence_of(result) >= 0.85:
    show value_of(result)
else:
    show "human review"
```

The checked execution paths are:

- `ledge check --types file.ledge`, which reports static type issues;
- `ledge run file.ledge`, which runs the same static check before execution;
- `checked_run(source)`, the Python API helper that typechecks before running.

The low-level Python `run(source)` API and `ledge run --unsafe` intentionally
execute directly. They exist for interpreter work, tests, experiments, and
explicit unsafe escape hatches.

## What Ledge Adds

| Area | What Ledge provides today |
|---|---|
| Uncertainty handling | `Uncertain[T]`, `confidence_of`, guarded `value_of`, `when(...)`, and explicit `unsafe_value_of` |
| Checked execution | CLI and Python helpers that refuse to run programs with unsafe `Uncertain` use |
| Runtime default | No backend means `confidence=0.0` and `value=nothing` for AI calls |
| Audit trail | Local SHA-256 hash chain with a documented threat model |
| Calibration | Brier score, ECE, and outcome-based threshold utilities |

These are implementation properties backed by tests and demos, not a claim of
formal soundness.

## Where Ledge Is Weaker

| Dimension | Current state |
|---|---|
| Ecosystem | Small, early, no mature package ecosystem |
| Performance | Reference interpreter; unsuitable for compute-heavy hot paths |
| Static analysis | Intraprocedural and intentionally limited |
| Security boundary | Not a sandbox; Python FFI must be governed by the host environment |
| Production maturity | No known production deployments or third-party audit |
| Community | Early project with a small contributor base |

## Relationship To Existing Tools

Ledge complements, rather than replaces, existing tools:

- Python libraries can implement equivalent policies with discipline and tests.
- Mypy/Pyright plugins or custom linters could enforce similar patterns in
  Python codebases.
- Evals, monitoring, incident review, and human oversight remain necessary.
- Security-sensitive deployments still need OS/container isolation, key
  management, logging infrastructure, and review.

Ledge's current value is that it packages one narrow contract into a runnable
language and CLI: on checked execution paths, AI outputs must be handled through
recognized uncertainty patterns before the program runs.
