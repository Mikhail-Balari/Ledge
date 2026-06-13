# Ledge Current Status

## Public Release

Current public release: `ledge-lang==1.6.0`

Ledge 1.6.0 Alpha is published as the Confidence Evidence Engine release.

## Phase Status

- Phase 1: Python SDK Core released.
- Phase 2: Python Linter / CI Enforcement released.
- Phase 3: Confidence Evidence Engine released in 1.6.0 Alpha.
- Phase 4: Slice 0 architecture is defined. Slice 1 adds the local
  `DecisionEvent` core for the planned Tamper-Evident Decision Ledger.

The likely next implementation release target is `1.7.0 Alpha`.

## What Works Today

- `Uncertain[T]` represents values that require explicit decision handling.
- `DecisionPolicy` and `DecisionResult` provide SDK decision-boundary behavior.
- `ledge lint-python` detects common unsafe SDK decision-boundary patterns.
- `ledge confidence-eval` renders redaction-aware confidence evidence reports.
- `ledge calibration-report` renders calibration diagnostics from historical
  outcomes.
- `ledge_lang.confidence.ConfidenceEvidence` provides audit-ready confidence
  evidence records with canonical serialization and evidence hashing.
- `ledge_lang.ledger.DecisionEvent` provides a strict, canonical, hashable
  event model for semantic AI decision boundary events.

## Phase 4 Slice 0 Scope

Slice 0 defines docs only:

- ledger architecture;
- proposed `DecisionEvent` schema;
- canonicalization contract;
- threat model;
- verifier output contract;
- AI review pack contract;
- limitations and anti-claims;
- readiness checklist for Ledger Core implementation.

No runtime ledger code is added in Slice 0.

No CLI ledger commands are added in Slice 0.

No version bump or release action is part of Slice 0.

## Phase 4 Slice 1 Scope

Slice 1 adds local runtime primitives only:

- `DecisionEvent` data model;
- canonical event serialization;
- event hash computation and verification;
- previous-event hash linking semantics;
- strict validation for semantic decision boundary events.

No CLI ledger commands are added in Slice 1.

No JSONL ledger store, manifest writer, export flow, or AI review pack
generation is added in Slice 1.

No version bump or release action is part of Slice 1.

## Important Limits

Ledge does not guarantee truth.

Ledge does not prevent hallucinations.

Ledge does not provide legal compliance certification.

Ledge is not production-ready or enterprise-ready as an alpha.

The planned ledger is tamper-evident, not tamper-proof.

The planned ledger uses append-oriented local records, not immutable storage or
blockchain.

## Next Slice

The next recommended slice is Phase 4 Slice 2: append-oriented ledger storage
and manifest foundation.

Expected scope:

- append-oriented local writer;
- manifest schema and writer;
- sequence and previous-hash continuity checks;
- storage-focused tamper detection tests.
