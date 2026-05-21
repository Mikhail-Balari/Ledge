# Expert Review Guide

Ledge is an experimental DSL for making unchecked AI uncertainty a static
error. Its central idea is small: AI operations return `Uncertain[T]`, and the
checked execution path rejects programs that use those values before confidence
handling is explicit.

## What To Test First

Install the published alpha package and run the bundled demo:

```bash
pip install ledge-lang
ledge demo medical_triage
```

With no backend configured, the demo should escalate every patient to human
review with confidence 0 and report that the audit chain verifies.

## Core Claim To Review

Checked execution rejects unchecked `Uncertain[T]` use before execution.

Relevant checked paths:

- `ledge check --types file.ledge`
- `ledge run file.ledge`
- `ledge_lang.checked_run(source)`

Explicit bypass paths:

- `ledge run file.ledge --unsafe`
- `ledge_lang.run(source)`, the low-level interpreter API

## Suggested Review Path

1. Read [`README.md`](README.md).
2. Run `ledge demo medical_triage`.
3. Inspect [`docs/STATIC_CHECKER.md`](docs/STATIC_CHECKER.md).
4. Try an unsafe `value_of(...)` extraction outside a confidence guard.
5. Try unsafe interpolation such as `show "decision: {value_of(r)}"`.
6. Inspect audit trail behavior with the demo scripts or `ledge audit`.
7. Read [`docs/THREAT_MODEL.md`](docs/THREAT_MODEL.md) and the limitations in
   the README.

## Minimal Unsafe Checks

This should be rejected before execution:

```ledge
define r as classify("invoice") using ["release_payment", "hold_payment"]
show value_of(r)
show "PAYMENT_RELEASED"
```

This should also be rejected before execution:

```ledge
define r as classify("invoice") using ["release_payment", "hold_payment"]
show "AI decision: {value_of(r)}"
show "PAYMENT_RELEASED"
```

Run either file with:

```bash
ledge run unsafe_example.ledge
```

The sentinel line should not print. Running the same file with `--unsafe`
intentionally skips the static checker.

## What Ledge Does Not Claim

- No formal soundness proof.
- No readiness for production-critical use.
- No compliance certification.
- No guarantee that confidence is calibrated correctness.
- No resistance to a malicious administrator who controls both the audit store
  and the local anchor file.
- No replacement for evals, monitoring, policy review, sandboxing, or human
  review.

## Specific Feedback Requested

Useful expert feedback includes:

- static checker design and edge cases;
- uncertainty model semantics;
- audit trail threat model and anchoring roadmap;
- language design and ergonomics;
- related work and adjacent tools;
- whether Ledge is useful as an AI decision-boundary layer;
- places where the documentation overstates or understates the current system.

## Relevant Docs

- [`README.md`](README.md)
- [`docs/STATIC_CHECKER.md`](docs/STATIC_CHECKER.md)
- [`docs/THREAT_MODEL.md`](docs/THREAT_MODEL.md)
- [`docs/UNCERTAINTY_MODEL.md`](docs/UNCERTAINTY_MODEL.md)
- [`docs/AUDIT_ANCHORING.md`](docs/AUDIT_ANCHORING.md)
- [`docs/ROADMAP.md`](docs/ROADMAP.md)
- [`docs/SUPPLY_CHAIN.md`](docs/SUPPLY_CHAIN.md)
- [`docs/RELEASE_PROVENANCE.md`](docs/RELEASE_PROVENANCE.md)

## Review Posture

Please treat Ledge 1.2.0 as an alpha core with a narrow checked-execution
contract. The right review question is not whether it is ready for critical
deployment today; it is whether the contract is useful, honestly documented,
testable, and worth hardening.
