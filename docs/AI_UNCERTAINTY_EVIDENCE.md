# Ledge AI Uncertainty Evidence
## Current Evidence For AI-First Tasks

This document records current internal evidence for Ledge's AI-uncertainty
workflow. It is not a user study, a proof, or a formal soundness result.

## Hypotheses

**H1:** Generated Ledge programs for AI-first tasks may be less likely to ignore
confidence than equivalent ordinary Python programs.

**H2:** When a program uses an AI result without confidence handling, Ledge's
static checker can reject that pattern before execution.

## Evidence 1: Reference Implementations

File: `experiments/ai_validation.py`

The project includes internal reference implementations for AI-first tasks.
These are useful regression tests for the language patterns, but they are not a
substitute for a blinded LLM study with independent scoring.

## Evidence 2: Checked Uncertainty Handling

The common Python bug is direct use of a model result without first checking
confidence:

```python
result = model.classify(text)
if result["label"] == "spam":
    take_action()
```

In Ledge, equivalent direct use of an `Uncertain[T]` value is rejected by
`ledge check --types` and by default `ledge run` before execution:

```ledge
define r as classify(text) using ["spam", "ok"]
show upper(r)   # TYPECHECKER ERROR: unsafe use of Uncertain value
```

Recognized safe handling patterns include a positive confidence guard,
`when(r, threshold, fallback)`, and the explicit `unsafe_value_of(r)` escape
hatch.

## Evidence 3: Zero Confidence Without A Backend

Without a connected backend, the bundled runtime returns `confidence=0.0` for
AI operations. This is a checked runtime property, not a claim about model
calibration or correctness.

## Limitations

- The current evidence is internal and implementation-focused.
- The checker is single-file and flow-sensitive; it is not a mechanized proof.
- The claim that LLMs generate better Ledge than Python remains future work.
- Real-world adoption claims require third-party usage and independent review.
