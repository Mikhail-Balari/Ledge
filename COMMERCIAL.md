# Commercial Positioning

Ledge is open-source alpha software. The commercial opportunity is not selling
access to the code. The commercial opportunity is helping teams evaluate
whether a specific AI-assisted decision boundary can be made more explicit,
auditable, and safer to operate in shadow mode.

## What Ledge Can Support Today

Ledge can support technical evaluations, demos, proofs of concept, and
shadow-mode pilots where the goal is to inspect one decision boundary:

- What AI output is being used?
- What action could follow?
- What confidence threshold is required?
- What fallback or human-review path exists?
- What audit evidence is recorded?
- What limitations remain before production use?

The current 1.2.0 alpha can demonstrate checked execution, explicit unsafe
bypass paths, confidence-gated extraction, audit logging, and basic calibration
workflows.

## What Ledge Cannot Support Today

Ledge 1.2.0 does not provide:

- production-critical readiness;
- legal or regulatory compliance certification;
- a guarantee that model confidence is calibrated;
- proof that model outputs are correct;
- a managed enterprise platform;
- a dashboard, login system, or hosted workflow;
- protection against malicious local administrators;
- replacement for evals, monitoring, human review, security review, or legal
  review.

## What An AI Decision Boundary Pilot Means

An AI Decision Boundary Pilot is a scoped technical exercise. It takes one
workflow where AI output may influence an action and asks whether that boundary
can be represented, checked, audited, and reviewed more explicitly.

Typical pilot questions:

- Which AI output matters?
- Which action could happen after that output?
- What is the confidence signal?
- What happens below threshold?
- What deterministic rules must apply regardless of AI output?
- What audit evidence should be produced?
- What outcomes can be collected later for calibration?

## Who Might Find It Useful

Ledge may be useful for teams exploring AI-assisted workflows in domains such
as triage, routing, review, finance operations, document processing, support,
moderation, or internal decision support.

The best fit is a team that already has or is considering an AI-assisted
workflow, but wants the boundary between "model output" and "business action"
to be more explicit before production use.

## What Shadow Mode Means

In shadow mode, Ledge runs beside an existing workflow or on synthetic/historical
fixtures. It does not affect production decisions. The goal is to observe how
the boundary, thresholds, fallbacks, and audit evidence would behave without
changing live operations.

Shadow mode can reveal:

- unclear confidence thresholds;
- missing fallback paths;
- places where AI output is treated as ordinary data;
- mismatches between deterministic rules and AI-derived labels;
- gaps in audit evidence or outcome collection.

## Why Open Source Does Not Prevent Paid Implementation

The code is open. The work in a pilot is applying it carefully to a real
decision boundary: mapping the workflow, defining fixtures, writing a small
Ledge representation, running it in shadow mode, reviewing audit evidence, and
documenting limitations and next steps.

That implementation and evaluation work can be valuable even when the tool is
open source.

## Current And Future Commercial Shape

Current:

- technical demo;
- scoped proof of concept;
- shadow-mode pilot support;
- workflow adaptation and review.

Future, not current:

- enterprise kit;
- embedded/OEM integration;
- managed policy workflows;
- stronger external audit anchoring;
- signed release provenance and deeper supply-chain evidence.

## Contact

Use the GitHub repository for issues, technical questions, and review feedback:
<https://github.com/Mikhail-Balari/Ledge>

For sensitive security concerns, follow [`SECURITY.md`](SECURITY.md).

## Disclaimers

Ledge is alpha software. It does not prove correctness, prevent hallucinations,
guarantee compliance, or make a workflow production-ready. Any consequential
deployment requires independent evaluation, monitoring, security review, legal
review where appropriate, and human oversight.
