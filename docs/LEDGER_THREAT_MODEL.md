# Decision Ledger Threat Model

This document defines the planned threat model for the Phase 4
Tamper-Evident Decision Ledger. It is a contract document only. Runtime ledger
code is not implemented in Slice 0.

## Designed To Detect

The ledger verifier should be designed to detect:

- edited historical event;
- deleted event;
- inserted event;
- reordered event;
- broken sequence;
- changed policy hash;
- changed evidence hash;
- changed action;
- changed confidence score;
- changed previous hash;
- manifest mismatch;
- schema mismatch;
- invalid redaction posture;
- non-canonical event encoding.

These findings depend on preserved ledger files, preserved manifests, and
deterministic canonicalization.

## Not Designed To Prevent

The ledger does not claim to prevent:

- full filesystem compromise;
- deletion of the entire ledger;
- complete ledger rewrite plus manifest rewrite by an attacker with total
  control;
- lying upstream systems before Ledge receives the event;
- legal compliance failure;
- hallucinations;
- unsafe deployment by itself;
- exfiltration of data before Ledge receives it;
- policy design mistakes.

## Explicit Anti-Claims

The Phase 4 ledger is not tamper-proof.

It is not audit-proof.

It is not legal compliance certification.

It is not production-ready.

It is not enterprise-ready.

It is not blockchain.

It is not remote attestation.

It does not guarantee truth and does not prevent hallucinations.

## Trust Boundaries

The ledger can only record what reaches the Ledge decision boundary. It cannot
prove that upstream systems were honest, that input data was correct, that an AI
model reasoned correctly, or that a downstream system enforced the recorded
decision.

The ledger should make the boundary inspectable. It should not pretend to make
the whole system safe by itself.

## Stronger Controls Outside Slice 0

Stronger guarantees require controls outside this architecture slice:

- access control;
- backups;
- object lock or append-only storage;
- cryptographic signatures;
- remote anchoring;
- independent custody;
- monitoring and alerting;
- infrastructure change control;
- legal and governance review.
