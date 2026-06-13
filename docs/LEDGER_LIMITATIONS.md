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

Slice 0 is architecture and contract only. It does not add runtime ledger code,
new CLI commands, hidden persistence, release changes, or production-readiness
claims.
