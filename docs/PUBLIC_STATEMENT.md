# Ledge — Technical Public Statement
## Authorized Release Text (v1.1.0)

This document contains the ONLY claims authorized for use in:
- README, blog posts, social media
- Talks, demos, conference submissions
- Documentation and tutorials

---

## What Ledge is (permitted claims)

Ledge is an experimental DSL for making AI uncertainty explicit in
program flow. It ships an interpreter, a static checker, a SHA-256
chained audit log, and reference documentation. The grammar and runtime
behavior are described in `docs/GRAMMAR.md` and `docs/SEMANTICS.md`;
those documents are references for implementors, not formal
specifications with mechanized proofs.

**Permitted claims:**

✓ "Ledge makes AI uncertainty a first-class type — `Uncertain[T]` is enforced by the typechecker"
✓ "Without an AI backend, all AI operations return confidence=0.0, never fabricated results"
✓ "Every AI call is automatically logged with input hashes — zero manual audit code needed"
✓ "Contracts (requires:/ensures:) are runtime-verified, not decorative"
✓ "The formatter is idempotent — run it twice, get the same result"
✓ "284 conformance tests define the language behavior independently of the implementation"
✓ "FFI: `import 'python:numpy'` gives access to the full Python ecosystem"
✓ "A LLVM IR compiler is in development — native binary compilation requires clang"

## What Ledge is NOT (prohibited claims)

✗ DO NOT CLAIM: "Ledge runs faster than Python" (requires clang, v1.2)
✗ DO NOT CLAIM: "Ledge supports WASM/ARM32/serverless" (architecture ready, toolchain pending)
✗ DO NOT CLAIM: "Ledge is production-ready for critical systems" (v2.0 with sandbox/GC)
✗ DO NOT CLAIM: "Ledge has a package ecosystem" (0 native packages exist)
✗ DO NOT CLAIM: "Ledge replaces Python" (different target: AI-first code, not general purpose)

## Recommended public framing

> "Ledge is an experimental DSL that makes AI uncertainty explicit in
> program flow. The static checker rejects direct use of uncertain
> values; the runtime records every AI call in a hash-chained audit
> log. It's designed for developers who want a narrower surface area
> than a Python library for the AI-decision layer. Try it:
> `pip install ledge-lang`."

## Score context

Ledge v1.1.0 scores 974/1000 on the World-Class Audit Protocol (previous protocol).
This audit is ongoing against the 970+ Public Release Protocol.
