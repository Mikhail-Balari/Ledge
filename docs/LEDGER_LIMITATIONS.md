# Decision Ledger Limitations

The Phase 4 Tamper-Evident Decision Ledger is planned as an auditability layer
for AI decision boundaries. It has important limits.

## Required Limitations

Ledge does not guarantee truth.

Ledge does not prevent hallucinations.

Ledge does not provide legal compliance certification.

Ledge does not make local files immutable.

Ledge does not provide secure storage by itself.

Ledge does not replace SIEM, observability, compliance teams, or human review.

Tamper evidence depends on the preservation of ledger files and manifests.

Stronger guarantees require external anchoring, access control, object lock,
signatures, or infrastructure controls outside this slice.

## Local Files Are Not A Security Boundary

Append-oriented local records can make many modifications detectable, but they
do not prevent deletion, replacement, or full rewrite by an attacker with enough
access. The ledger should be paired with normal operational controls when used
in serious environments.

## Evidence Is Not Truth

Confidence evidence, policy hashes, and ledger hashes make decision boundaries
inspectable. They do not prove that input data was correct, that model output
was true, that a policy was well-designed, or that downstream systems behaved
correctly.

## Alpha Scope

Phase 4 is being implemented in narrow slices after the 1.6.0 Alpha release.
The current local ledger work includes event modeling, append-oriented JSONL
storage, manifest summaries, verifier output, CLI init/append/verify/manifest
commands, local audit review export packages, AI-readable review packs, and an
SDK-facing ledger recorder.

These slices do not add SDK auto-persistence, remote anchoring, hidden
persistence, release changes, or production-readiness claims.
The export package and AI review pack are local review aids, not compliance
reports.

The AI review pack does not ask another AI to trust the original AI output. It
is a structured prompt-independent review contract over boundary ids, evidence
hashes, policy results, actions, warnings, and integrity status.

The SDK-facing recorder reduces bookkeeping for sequence numbers, timestamps,
event ids, previous hashes, and event hashes. It does not infer missing policy
or evidence semantics and does not store raw payloads.
