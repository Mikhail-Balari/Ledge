# Ledger Slice 0 Readiness

Phase 4 Slice 0 defines the architecture and contract for the planned
Tamper-Evident Decision Ledger. It does not implement runtime ledger code.

## Readiness Checklist

- [ ] Schema contract approved.
- [ ] Canonicalization contract approved.
- [ ] Threat model approved.
- [ ] Anti-claims present.
- [ ] Verifier output contract approved.
- [ ] AI review pack contract approved.
- [ ] No runtime code added yet.
- [ ] No version bump.
- [ ] No release action.
- [ ] Next slice clearly defined as Ledger Core implementation.

## Slice 0 Deliverables

- `docs/DECISION_LEDGER.md`
- `docs/LEDGER_SCHEMA.md`
- `docs/LEDGER_THREAT_MODEL.md`
- `docs/LEDGER_VERIFICATION_CONTRACT.md`
- `docs/LEDGER_AI_REVIEW_PACK.md`
- `docs/LEDGER_LIMITATIONS.md`
- `docs/LEDGER_SLICE_0_READINESS.md`

## Gate To Slice 1

Slice 1 should begin only after the schema, canonicalization rules, verifier
contract, AI review pack contract, and limitations are reviewed together.

The expected next slice is Ledger Core implementation:

- `DecisionEvent` data model;
- canonical event serialization;
- current and previous event hash computation;
- append-oriented local writer;
- verifier core for sequence and hash-chain integrity;
- unit tests for tamper detection.

Slice 1 should still avoid release actions unless explicitly requested.
