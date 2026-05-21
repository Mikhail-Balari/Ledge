# Uncertainty Model

This document describes the current Ledge 1.2.0 uncertainty model and sketches
future semantics for richer uncertainty handling. It is design documentation,
not an implemented runtime contract beyond the current `Uncertain[T]` behavior.

Ledge remains alpha software. This document does not claim calibrated
correctness, formal probability semantics, compliance certification, or
production-critical readiness.

## Current Model

Today, AI operations in Ledge return values typed as `Uncertain[T]`.

The implemented model has four main parts:

- `Uncertain[T]`: a wrapper around an AI-derived value and its uncertainty
  metadata.
- Confidence score: a numeric signal exposed through `confidence_of(x)`.
- Confidence guards: recognized static patterns such as
  `if confidence_of(x) >= threshold:` and `if is_confident(x):`.
- Safe extraction and fallback:
  - `value_of(x)` is accepted only inside a recognized confidence guard.
  - `when(x, threshold, fallback)` extracts only when confidence meets the
    threshold and otherwise returns the fallback.
  - `unsafe_value_of(x)` is an explicit escape hatch for code that deliberately
    bypasses confidence handling.

The static checker rejects direct use of uncertain values in checked execution
paths until one of the recognized handling patterns is visible. The runtime also
records AI calls in the audit trail and supports calibration workflows that
compare declared confidence with observed outcomes.

## What Confidence Does Not Mean

The current confidence score is a signal, not a guarantee.

In particular:

- Confidence is not correctness.
- Confidence is not a calibrated probability by default.
- Confidence may come from different backend-specific mechanisms.
- Ledge does not prove that a model output is true.
- Ledge does not prove that a chosen threshold is appropriate for a domain.
- Calibration reports measure observed behavior; they do not make future model
  outputs correct.

The current safety contract is narrower: checked execution rejects unchecked use
of AI-derived values before the program runs.

## Proposed Future Uncertainty States

Future versions may distinguish several uncertainty states instead of treating
all AI-derived results as one category:

- `unknown`: no reliable value is available.
- `unverifiable`: a value was produced, but the system cannot verify it with the
  available evidence.
- `conflicting`: multiple sources or model calls disagree in a material way.
- `observed`: derived from direct observation or an authoritative input source.
- `inferred`: derived by reasoning from other facts or evidence.
- `predicted`: a forecast or model projection about future behavior.
- `estimated`: an approximate value computed from incomplete data.

These names are design placeholders. They should not be treated as implemented
language keywords or stable API names yet.

## Proposed Future Metadata

A richer uncertainty value may need metadata beyond a single confidence number:

- Source: the system, document, user, sensor, model, or service that produced
  the value.
- Evidence reference: a pointer to the document, record, audit entry, trace, or
  retrieval result supporting the value.
- Model/backend: the AI backend and model identifier.
- Timestamp: when the value or evidence was produced.
- Confidence signal type: for example self-reported confidence, token-derived
  estimate, classifier score, retrieval score, calibrated empirical score, or
  human assertion.
- Calibration bucket: the empirical bucket or domain measurement used to
  interpret the confidence signal.
- Policy threshold: the threshold or policy rule applied when deciding whether
  to use, block, or escalate the value.

Future APIs should preserve enough metadata for audit and calibration without
turning sensitive input data into unnecessary logs.

## Propagation Questions

A stronger model must define how uncertainty moves through programs:

- When a transformation consumes one uncertain input, does the output keep the
  same uncertainty state, produce a new state, or require an explicit policy?
- How should uncertainty compose across multiple uncertain inputs?
- How should conflicting evidence be represented and surfaced to the program?
- When should low confidence, conflict, or unverifiability force human review?
- When can deterministic business rules block an AI-derived result regardless
  of confidence?
- When can deterministic rules safely override, narrow, or ignore AI-derived
  evidence?
- How should uncertainty propagate through lists, maps, function calls,
  pipelines, and agent/tool boundaries?
- How should backend confidence signals be calibrated before they influence
  policy decisions?

These questions should be resolved before richer uncertainty states are exposed
as stable language or API behavior.

## Deterministic Rules and AI-Derived Decisions

Ledge should continue to distinguish deterministic business rules from
AI-derived decisions.

For example, a payment workflow might deterministically block a sanctioned
country, duplicate invoice, or contract mismatch even if an AI classifier reports
high confidence. Conversely, an AI-derived "low risk" label should not authorize
payment unless the deterministic rules also permit the action and the AI result
passes the configured confidence policy.

This distinction is part of Ledge's design direction: confidence handling should
make decision sources clearer, not blend deterministic and AI-derived authority
into one opaque score.

## Non-Goals

This design direction does not claim:

- calibrated correctness by default;
- formal probability semantics;
- whole-program soundness;
- production-critical readiness;
- legal, security, or compliance certification;
- replacement of evals, monitoring, policy review, or human review.

## Open Design Questions

- Should richer uncertainty states be explicit language-level variants,
  metadata fields on `Uncertain[T]`, or separate domain-specific policy
  annotations?
- Which states should be required in the core language, and which should belong
  in adapters or policy layers?
- How should uncertainty metadata survive serialization, audit export, and
  Python embedding?
- How should Ledge represent disagreement between model calls, retrieval
  evidence, and deterministic data sources?
- What is the minimum calibration interface needed before confidence can be
  interpreted consistently across backends?
- How should policies express "must escalate" conditions without making normal
  Ledge programs verbose?
- Which parts of the model can be tested deterministically, and which require
  empirical evaluation on real model behavior?

Implementation should proceed incrementally, with tests and documentation for
each new state before it is recommended for consequential workflows.
