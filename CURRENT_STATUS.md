# Ledge Current Status

## Public Release

Current public release: `ledge-lang==1.6.0`

Ledge 1.6.0 Alpha is published as the Confidence Evidence Engine release.

## Phase Status

- Phase 1: Python SDK Core released.
- Phase 2: Python Linter / CI Enforcement released.
- Phase 3: Confidence Evidence Engine released in 1.6.0 Alpha.
- Phase 4: Slice 0 architecture is defined. Slice 1 adds the local
  `DecisionEvent` core. Slice 2 adds append-oriented JSONL storage and a
  `LedgerManifest` foundation. Slice 3 adds verifier core results for the
  planned Tamper-Evident Decision Ledger.

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
- `ledge_lang.ledger.DecisionLedger` provides append-oriented local JSONL
  storage for validated decision events.
- `ledge_lang.ledger.LedgerManifest` provides a local summary and anchor point
  for later verification.
- `ledge_lang.ledger.LedgerVerifier` verifies local ledger JSONL files and
  optional manifests with structured findings, deterministic JSON output, and
  human-readable summaries.

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

## Phase 4 Slice 2 Scope

Slice 2 adds local storage and manifest primitives only:

- append-oriented JSONL event storage;
- sequence continuity checks;
- previous-event hash continuity checks;
- strict rejection of blank or malformed ledger lines;
- local manifest summary for event count, first event hash, and last event hash.

No CLI ledger commands are added in Slice 2.

No full verifier output contract, export package, AI review pack generation, or
SDK integration is added in Slice 2.

No version bump or release action is part of Slice 2.

## Phase 4 Slice 3 Scope

Slice 3 adds local verifier primitives only:

- human-readable verification summaries;
- deterministic machine-readable verification JSON;
- stable finding severities and codes;
- ledger JSONL parsing findings;
- event schema and event hash findings;
- sequence and previous-hash continuity findings;
- optional manifest consistency findings.

No CLI ledger commands are added in Slice 3.

No export package, AI review pack generation, or SDK integration is added in
Slice 3.

No version bump or release action is part of Slice 3.

## Important Limits

Ledge does not guarantee truth.

Ledge does not prevent hallucinations.

Ledge does not provide legal compliance certification.

Ledge is not production-ready or enterprise-ready as an alpha.

The planned ledger is tamper-evident, not tamper-proof.

The planned ledger uses append-oriented local records, not immutable storage or
blockchain.

## Next Slice

The next recommended slice is Phase 4 Slice 4: public verification operation
surface.

Expected scope:

- CLI command for ledger verification;
- text and JSON verifier output from the command;
- examples for local source-checkout ledger verification;
- no SDK auto-persistence yet;
- no export package or AI review pack generation yet.
