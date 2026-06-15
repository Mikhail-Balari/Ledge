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
  planned Tamper-Evident Decision Ledger. Slice 4 adds public CLI verification
  and manifest commands. Slice 5 adds ledger init and append commands. Slice 6
  adds local audit review export packages. Slice 7 adds AI-readable review
  packs. Slice 8 adds an SDK-facing ledger recorder. Slice 9 defines the SDK
  `DecisionResult` ledger mapping contract. Slice 10 adds a safe
  `DecisionResult` ledger adapter within that contract. Slice 11 adds an
  end-to-end source checkout SDK ledger workflow example.

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
- `ledge ledger-verify` exposes ledger verification for humans, CI, shell
  scripts, and JSON-consuming workflows.
- `ledge ledger-manifest` writes local manifest summaries for valid ledger
  JSONL files.
- `ledge ledger-init` creates or validates append-oriented local ledger files.
- `ledge ledger-append` appends completed or draft semantic `DecisionEvent`
  JSON while enforcing hash and sequence continuity.
- `ledge ledger-export` generates local audit review packages with copied
  ledger events, manifest JSON, verification reports, safe summaries, and
  limitations.
- `ledge ledger-review-pack` writes a single machine-readable JSON review pack
  for AI, governance, CI, or reviewer workflows.
- `ledge_lang.ledger.LedgerRecorder` appends semantic decision events while
  managing sequence numbers, previous hashes, timestamps, event ids, event
  hashes, and local ledger append behavior.
- `ledge_lang.ledger.record_decision_result` records SDK `DecisionResult`
  objects only when explicit ledger context, hashes, and policy result are
  supplied.
- `examples/ledger/sdk_decision_result_to_ledger.py` demonstrates
  `DecisionResult -> record_decision_result(...) -> ledger verification ->
  local audit review export -> AI-readable review pack`.

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

## Phase 4 Slice 4 Scope

Slice 4 adds CLI operation commands only:

- `ledge ledger-verify --store <ledger.jsonl>`;
- optional `--manifest <manifest.json>`;
- `--format text|json`;
- `--strict` warning handling for CI;
- `ledge ledger-manifest --store <ledger.jsonl> --out <manifest.json>`;
- manifest overwrite protection with `--force`.

No SDK integration, export package, AI review pack generation, remote anchoring,
version bump, or release action is part of Slice 4.

## Phase 4 Slice 5 Scope

Slice 5 adds local ledger operation commands only:

- `ledge ledger-init --store <ledger.jsonl>`;
- `ledge ledger-append --store <ledger.jsonl> --event <decision_event.json>`;
- optional `--init` for append-time initialization;
- `--format text|json` for append output;
- draft event support when `current_event_hash` is omitted;
- raw payload field rejection before append.

No SDK integration, export package, AI review pack generation, remote anchoring,
version bump, or release action is part of Slice 5.

## Phase 4 Slice 6 Scope

Slice 6 adds a local audit review export package only:

- `ledge ledger-export --store <ledger.jsonl> --out <audit_export/>`;
- optional manifest verification with `--manifest`;
- optional boundary filtering with `--boundary`;
- overwrite protection with `--force`;
- generated `ledger_events.jsonl`, `ledger_manifest.json`,
  `verification_report.json`, `verification_report.md`,
  `decision_summary.json`, and `README.md`.

Full-ledger verification remains the integrity source for filtered exports.
The package is a local audit review aid, not compliance certification.

No SDK integration, AI review pack generation, remote anchoring, version bump,
or release action is part of Slice 6.

## Phase 4 Slice 7 Scope

Slice 7 adds AI-readable ledger review packs only:

- `ledge ledger-review-pack --store <ledger.jsonl> --out <ai_review_pack.json>`;
- optional manifest verification with `--manifest`;
- optional boundary filtering with `--boundary`;
- overwrite protection with `--force`;
- integrity summary, decision boundaries, policy result counts, action counts,
  warnings, critical findings, recommended review focus, safe event summaries,
  and limitations.

The review pack is a machine-readable review contract. It does not ask another
AI to trust the original AI output. It asks reviewers to inspect boundary ids,
evidence hashes, policy results, actions, warnings, and integrity status.

No SDK integration, remote anchoring, version bump, or release action is part
of Slice 7.

## Phase 4 Slice 8 Scope

Slice 8 adds an SDK-facing recorder API only:

- `LedgerRecordContext` for boundary id, boundary version, policy hash,
  redaction profile, and optional correlation fields;
- `LedgerRecorder` for appending validated `DecisionEvent` records without
  manual sequence, previous-hash, timestamp, event id, or event-hash handling;
- `record_decision_event` as a small helper.

The recorder requires explicit evidence/input/output hashes or references. It
does not store raw prompts, completions, messages, inputs, outputs, responses,
or payloads.

A direct `DecisionResult` adapter is deferred because current SDK result fields
do not include enough stable ledger context to infer policy hashes,
evidence hashes, input hashes, or output hashes safely.

No remote anchoring, version bump, or release action is part of Slice 8.

## Phase 4 Slice 9 Scope

Slice 9 adds docs-only SDK ledger mapping contracts:

- `docs/LEDGER_SDK_INTEGRATION.md`;
- `docs/LEDGER_DECISION_RESULT_MAPPING.md`;
- a table classifying ledger fields as auto-managed, SDK-available, explicit
  context, or not safely inferable;
- a future `record_decision_result(...)` adapter shape;
- fail-closed behavior for missing or ambiguous mappings.

Slice 9 does not implement automatic `DecisionResult` recording and does not
modify SDK runtime behavior.

No remote anchoring, version bump, or release action is part of Slice 9.

## Phase 4 Slice 10 Scope

Slice 10 adds a safe `DecisionResult` adapter:

- `record_decision_result(...)` in `ledge_lang.ledger`;
- explicit `LedgerRecordContext`;
- explicit `evidence_hash`, `input_hash`, `output_hash`, and `policy_result`;
- confidence from `DecisionResult.confidence`;
- action from explicit override or `DecisionResult.action`;
- warnings from explicit override or `DecisionResult.warnings`;
- fail-closed behavior for missing or ambiguous mappings.

The adapter does not serialize `DecisionResult.value`, `Uncertain.value`,
prompts, completions, messages, inputs, outputs, responses, or payloads.

No remote anchoring, version bump, or release action is part of Slice 10.

## Phase 4 Slice 11 Scope

Slice 11 adds a source checkout SDK ledger workflow example only:

- low-stakes support-ticket routing scenario;
- current SDK `DecisionResult` construction;
- explicit `LedgerRecordContext`, `evidence_hash`, `input_hash`,
  `output_hash`, and `policy_result`;
- local ledger JSONL file;
- local manifest;
- local audit review package;
- AI-readable review pack;
- integration test coverage for the generated artifacts and public CLI.

The example does not store raw prompts, completions, messages, inputs, outputs,
responses, payloads, `Uncertain.value`, or `DecisionResult.value`.

No remote anchoring, version bump, or release action is part of Slice 11.

## Important Limits

Ledge does not guarantee truth.

Ledge does not prevent hallucinations.

Ledge does not provide legal compliance certification.

Ledge is not production-ready or enterprise-ready as an alpha.

The planned ledger is tamper-evident, not tamper-proof.

The planned ledger uses append-oriented local records, not immutable storage or
blockchain.

## Next Slice

The next recommended slice is Phase 4 Slice 12: final Phase 4 technical review
or the next narrow ledger capability before `1.7.0 Alpha` release prep.

Expected scope:

- no version bump or release action unless explicitly requested;
- preserve the tamper-evident, not tamper-proof boundary;
- keep SDK integration, AI review pack, or remote anchoring work scoped to one
  slice.
