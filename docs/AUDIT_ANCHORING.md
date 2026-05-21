# Audit Anchoring Design

Ledge 1.2.0 records AI decisions in a hash-chained local audit log and writes
periodic anchors to a separate local file. This document describes that current
model and a future roadmap for stronger external anchoring. It is design
documentation only; Ledge does not implement remote anchoring, signed
checkpoints, transparency logs, or institutional audit-grade storage today.

## Current Model

The current audit system has two local pieces:

- A SQLite audit log containing AI decision records.
- A local external anchor file, by default `~/.ledge/anchors.jsonl`, containing
  periodic chain hashes and entry counts.

Each audit event stores a `prev_hash` and `chain_hash`. Verification recomputes
the chain and checks whether each event points to the expected previous hash.
The anchor file records selected chain roots outside the SQLite database so a
database rewrite can be compared against an independently stored local file.

This detects:

- accidental corruption of stored event fields;
- simple modification of an existing event;
- insertion, deletion, or reordering that breaks the stored hash chain;
- a database rewrite that no longer matches existing local anchors.

It does not detect:

- an attacker who can rewrite both the database and the anchor file;
- a malicious local operator who controls the host and can replace all local
  evidence consistently;
- deleted audit history if no independent anchor or backup remains;
- false or misleading input data supplied to the audited program;
- model correctness, policy correctness, or legal compliance.

The current design is useful for local traceability and regression testing. It
is not a substitute for append-only infrastructure, access control, external
timestamping, signed provenance, or organizational audit controls.

## Threat Model

### Attacker With Database Access Only

If an attacker can modify the SQLite audit database but cannot modify the
anchor file, Ledge can detect many post-hoc changes. Event modifications,
hash corruption, reordering, insertion, and deletion can break the chain or
cause anchor mismatches.

This is the current strongest case for the local anchor model.

### Attacker With Database and Anchor Access

If an attacker can modify both the database and the local anchor file, they can
potentially recompute a clean chain and matching local anchors. Ledge 1.2.0
does not prevent or reliably detect that scenario.

Future external anchoring is intended to move at least one checkpoint outside
the operator's local control.

### Malicious Local Operator

Ledge is not a security boundary against a malicious local operator. A local
operator with sufficient host access can alter files, suppress logs, replay
old state, change clocks, run with unsafe flags, or bypass Ledge entirely.

Production-critical deployments would need OS isolation, access control,
remote logging, key management, monitoring, and organizational process around
the Ledge runtime.

### Accidental Corruption

The current chain is useful for detecting accidental corruption: partial writes,
manual edits, bad migrations, truncated files, and inconsistent backups can
become visible during verification.

That value should be preserved even if stronger anchoring is added later.

## Future Anchoring Options

These options are not mutually exclusive. A practical design may combine
several, depending on deployment risk and operational maturity.

### Append-Only Storage

Write audit events or checkpoints to an append-only store rather than relying
only on mutable local SQLite files. Examples include append-only databases,
event streams, object stores with retention controls, or managed audit-log
services.

Questions:

- What append-only guarantee is provided by the storage layer?
- Who administers the store?
- Can retention or deletion policies be changed silently?
- How are partial writes and retries represented?

### Remote Timestamping

Periodically submit chain roots to a remote timestamping service. This can
establish that a checkpoint existed at or before a particular time.

Questions:

- What trust model does the timestamping service require?
- How are service outages handled?
- Are timestamps enough, or are signatures also required?
- How are private inputs protected when submitting checkpoints?

### Signed Checkpoints

Sign periodic chain roots with a key held outside the local audit database.
The signing key could live in a local key store, cloud KMS, HSM, or another
controlled signing service.

Questions:

- Who controls the signing key?
- Can signing be performed without exposing raw prompts or outputs?
- How are key rotation, compromise, and revocation recorded?
- What is the minimum checkpoint frequency for useful detection?

### Merkle Roots

Group events into batches and publish Merkle roots instead of one linear
checkpoint per event. This can support compact proofs for subsets of records
and cleaner batch anchoring.

Questions:

- Are event order and event inclusion both represented?
- How are deletions or redactions handled?
- Does the proof format remain stable across versions?
- Can independent verifiers reconstruct the tree from exported evidence?

### Transparency Log

Publish checkpoints to a transparency log or similar public or organization-wide
append-only ledger. This can make retroactive rewriting harder if independent
monitors observe the log.

Questions:

- Is the log public, private, or consortium-operated?
- What privacy metadata is exposed by publishing checkpoints?
- Who monitors the log and alerts on inconsistencies?
- What happens if a checkpoint is missing?

### Cloud KMS or HSM Signing

Use a managed key service or hardware-backed signing module to sign checkpoint
records. This can reduce the risk that local process compromise automatically
means signing-key compromise.

Questions:

- Does the application have direct signing authority, or is signing mediated
  by policy?
- Are key-use logs available and independently reviewable?
- Can keys be scoped per environment, domain, or tenant?
- How are emergency disablement and recovery handled?

### WORM or Object-Lock Storage

Write checkpoint records or exported evidence bundles to storage configured for
write-once-read-many behavior or object retention locks.

Questions:

- Are retention settings enforceable against administrators?
- What jurisdictional or organizational controls govern deletion?
- How are mistakes corrected without silently rewriting evidence?
- Can test environments avoid polluting long-retention stores?

## Redaction and Minimization

Audit evidence can contain sensitive data. Stronger anchoring must not force
teams to publish raw prompts, user records, model outputs, or regulated data
when a hash or minimized evidence reference is enough.

Design requirements:

- Prefer hashing or content-addressed references for sensitive inputs.
- Keep raw prompts and outputs out of public anchors by default.
- Support retention and redaction workflows without silently preserving
  misleading integrity claims.
- Distinguish "this exact private record existed" from "this redacted export is
  structurally consistent with a prior checkpoint."
- Make redaction explicit in exported evidence so reviewers can see what was
  removed and why.

Open question: if a record must be deleted for privacy or legal reasons, how
should Ledge preserve evidence that a deletion occurred without preserving the
deleted content itself?

## Non-Claims

The current Ledge audit model is not:

- tamper-proof;
- institutional audit-grade by itself;
- legal compliance evidence by itself;
- a security boundary against local operators;
- a replacement for access control, monitoring, backups, or incident response;
- proof that an AI decision was correct.

Future anchoring could strengthen traceability, but it would still need to be
interpreted within a documented threat model and deployment process.

## Proposed Phased Roadmap

### Phase 1: Stronger Local Invariants and Tests

- Keep deterministic invariant tests for modification, insertion, deletion,
  reordering, hash corruption, anchor mismatch, empty stores, and corrupt stores.
- Document exactly which local attacks are detectable.
- Keep verification outputs machine-readable enough for CI and review tools.

Exit criteria:

- Local audit-chain behavior is continuously tested.
- Known local limitations are documented and not described as stronger than
  they are.

### Phase 2: Signed Checkpoints

- Define a stable checkpoint payload.
- Sign checkpoint payloads with a key outside the audit database.
- Document key ownership, rotation, and revocation.
- Add verification tooling for signed checkpoints.

Exit criteria:

- A verifier can distinguish unsigned local anchors from signed checkpoints.
- Key compromise and rotation behavior is documented.

### Phase 3: Remote or External Anchoring

- Submit signed checkpoints or Merkle roots to a remote system.
- Define outage and retry behavior.
- Add independent reconciliation between local records and remote checkpoints.
- Keep sensitive content out of remote anchors by default.

Exit criteria:

- A local database rewrite cannot silently match a previously observed remote
  checkpoint.
- Operators can explain what the remote anchor proves and what it does not.

### Phase 4: Transparency Log or Institutional Deployment Pattern

- Evaluate a transparency log, organization-wide append-only ledger, or
  managed audit-log service.
- Define monitor responsibilities and alerting.
- Publish a deployment pattern for higher-assurance environments.
- Document privacy, retention, redaction, and legal review requirements.

Exit criteria:

- The anchoring model can be reviewed by security and governance teams without
  implying compliance certification or production-critical readiness by default.

## Open Design Questions

- What checkpoint payload should become stable across Ledge versions?
- Should checkpoints be per program, per store, per tenant, or per deployment?
- How should clock trust be represented?
- How often should checkpoints be written for different risk levels?
- How should failed anchoring attempts affect program execution?
- Can anchoring policy be configured without hiding unsafe defaults?
- What evidence bundle format should independent reviewers receive?
- How should deleted or redacted records remain accountable without retaining
  sensitive content?
