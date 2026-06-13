# Tamper-Evident Decision Ledger

## What It Is

The Tamper-Evident Decision Ledger is the planned Phase 4 record layer for
Ledge decision boundaries. It is designed to record the moment an uncertain AI
output becomes, or is prevented from becoming, a system action.

This is a semantic decision boundary ledger, not a generic log. A generic log
records that something happened. A Ledge ledger event records why an AI-derived
or AI-adjacent action crossed a boundary, what policy governed it, what
confidence evidence supported it, what result was produced, and how the event
links to the surrounding evidence chain.

The core chain is:

```text
Uncertain[T] -> ConfidenceEvidence -> DecisionPolicy -> DecisionResult
-> DecisionEvent -> Tamper-Evident Decision Ledger -> Verifier / Export / AI Review Pack
```

## Why It Records Boundary Crossings

Ledge exists to convert the risk "the AI said something and the system acted"
into an explicit, checkable, auditable, and blockable boundary. The ledger is
not meant to record every application event. It is meant to record semantic
decision boundary events, not generic logs.

A `DecisionEvent` should exist when a policy decision produces an action such
as:

- allowing an AI-derived value to proceed;
- allowing with warnings;
- blocking an action;
- escalating to human review;
- preserving evidence that a risky action did not occur.

## Relationship To Ledge Concepts

`Uncertain[T]` represents a value that cannot safely cross into action without
an explicit policy decision.

`ConfidenceEvidence` records the evidence, warnings, limitations, hashes, and
redaction posture behind a confidence score.

`DecisionPolicy` defines the boundary rule: thresholds, missing-value behavior,
required warnings, escalation behavior, and the permitted action surface.

`DecisionResult` is the immediate SDK result: allowed or blocked, action,
reason, confidence, warnings, metadata, and value handling.

`DecisionEvent` is the proposed ledger event: a canonical, hash-linked summary
of the boundary crossing, preserving enough structure for later verification
without storing raw sensitive data.

## Tamper-Evident, Not Tamper-Proof

The ledger is intended to be tamper-evident, not tamper-proof.

Tamper-evident means that changes to recorded events should be detectable by a
verifier when ledger files and manifests are preserved. Editing an event,
deleting an event, inserting a new event, reordering events, or changing hashes
should break verification.

Tamper-evident does not mean the local files cannot be deleted or rewritten by
an attacker with enough access. Stronger guarantees require infrastructure
controls outside this slice, such as access control, append-only storage,
object lock, signatures, remote anchoring, backups, or independent custody.

## Local Append-Oriented Records

Phase 4 is planned as append-oriented local records, not immutable storage.

The first implementation should favor clear local files and deterministic
verification over distributed complexity. It should not introduce blockchain,
hidden persistence, or remote attestation by default. The ledger should be
plain enough that humans can inspect it and strict enough that automated
verifiers can reject broken chains.

## Human And AI Review

The ledger should support both human audit review and AI-assisted review.

For humans, it should make the boundary decision legible: what was allowed,
blocked, or escalated; which policy applied; which evidence hash was attached;
which warnings were present; and whether the event chain verifies.

For AI reviewers, it should provide a structured review package that asks the
reviewing system to inspect the boundary, evidence, policy result, action,
warnings, and integrity findings. It must not ask a reviewing AI to trust the
original AI output.

## Verification CLI Surface

Phase 4 Slice 4 exposes the local verifier through:

```bash
ledge ledger-verify --store ledge_audit.jsonl
ledge ledger-verify --store ledge_audit.jsonl --manifest ledger_manifest.json
ledge ledger-verify --store ledge_audit.jsonl --manifest ledger_manifest.json --format json
ledge ledger-verify --store ledge_audit.jsonl --strict
```

It also exposes local manifest generation through:

```bash
ledge ledger-manifest --store ledge_audit.jsonl --out ledger_manifest.json
ledge ledger-manifest --store ledge_audit.jsonl --out ledger_manifest.json --force
```

The CLI is intended for humans, CI, shell scripts, and future governance
workflows. JSON output is designed for machine readers and other AI systems.
`--strict` can make warnings nonzero when a CI pipeline requires a manifest.
Local audit review export packages, AI review pack generation, and SDK
integration remain future work.

## Init And Append CLI Surface

Phase 4 Slice 5 adds operational commands for creating local ledger files and
appending semantic decision events:

```bash
ledge ledger-init --store ledge_audit.jsonl
ledge ledger-append --store ledge_audit.jsonl --event decision_event.json
ledge ledger-append --store ledge_audit.jsonl --event decision_event.json --init
ledge ledger-append --store ledge_audit.jsonl --event decision_event.json --format json
```

`ledger-init` creates an append-oriented local ledger file if it is missing and
does not truncate an existing valid ledger.

`ledger-append` accepts completed `DecisionEvent` JSON or draft event JSON that
omits `current_event_hash`. Draft events are validated and hashed through the
same canonical event path before append. Raw payload fields such as `input`,
`output`, `raw_input`, `raw_output`, `prompt`, `completion`, `messages`,
`response`, and `payload` are rejected.

These commands make the local ledger operational for humans, CI jobs, shell
scripts, and structured event producers. They do not add SDK auto-persistence,
remote anchoring, export packages, or AI review pack generation.

## Local Audit Review Export Packages

Phase 4 Slice 6 adds a local review package command:

```bash
ledge ledger-export --store ledge_audit.jsonl --out audit_export/
ledge ledger-export --store ledge_audit.jsonl --manifest ledger_manifest.json --out audit_export/
ledge ledger-export --store ledge_audit.jsonl --manifest ledger_manifest.json --boundary refund_decision --out audit_export/
ledge ledger-export --store ledge_audit.jsonl --out audit_export/ --force
```

`ledger-export` writes a local audit review package containing copied ledger
events, a manifest, machine-readable verification JSON, a human-readable
verification report, a safe aggregate decision summary, and a README with
limitations.

When `--boundary` is used, the exported `ledger_events.jsonl` is filtered to
matching events only. The verification report still describes the full source
ledger because filtering breaks full-chain continuity. Full-ledger verification
remains the integrity source for the package.

The export package is a review aid, not compliance certification. It does not
add AI review pack generation, SDK integration, remote anchoring, immutable
storage, or production readiness.

## What It Is Not

The ledger is an audit review package, not compliance certification.

It is tamper-evident, not tamper-proof.

It uses append-oriented local records, not immutable storage.

It records semantic decision boundary events, not generic logs.

It does not guarantee truth, prevent hallucinations, certify legal compliance,
provide production readiness, or replace human review for high-stakes systems.
