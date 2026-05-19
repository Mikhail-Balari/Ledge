# Threat Model

This document describes what Ledge 1.2.0 is designed to catch, what it records, and what remains outside the current boundary.

## In Scope

Ledge is aimed at code paths where an AI output might otherwise be treated as an ordinary trusted value.

The current implementation can help with:

- Rejecting unchecked use of `Uncertain[T]` values before CLI execution.
- Making confidence thresholds and fallbacks visible in source code.
- Recording AI decisions in a hash-chained local audit log.
- Exporting structured evidence artifacts that may support governance review.
- Running deterministic local examples without an API key.

## Out of Scope

Ledge 1.2.0 does not provide:

- A sandbox for untrusted code.
- A security boundary against a malicious local operator.
- A guarantee that model confidence is calibrated or correct.
- Legal or regulatory certification.
- Protection against arbitrary Python code that bypasses Ledge's checked entry points.
- Whole-program static analysis across modules, callbacks, or host-language integrations.

The hash chain can detect accidental or unsophisticated modification when the database and anchor file are not both rewritten consistently. It is not a substitute for append-only infrastructure, external anchoring, access control, or operational monitoring.

## Recommended Use Today

Use Ledge as an experimental uncertainty-aware execution layer for prototypes, research systems, safety demonstrations, and early governance workflows.

For anything production-critical, pair it with:

- Host-language validation and sandboxing.
- CI gates that run `ledge check --types` and `python scripts/pre_release_check.py`.
- Policy review for thresholds and fallbacks.
- Calibration measurements for each domain and model.
- External audit anchoring if records must survive local compromise.
- Human review for consequential decisions.

## Production-Critical Readiness

Before relying on Ledge for high-impact or regulated decisions, the project needs independent review of the checker, runtime, audit storage, calibration workflow, and packaging supply chain. The roadmap tracks this work explicitly in `docs/ROADMAP.md`.
