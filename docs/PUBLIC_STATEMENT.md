# Ledge — Technical Public Statement
## Authorized Release Text (v1.1.0)

This document contains the ONLY claims authorized for use in:
- README, blog posts, social media
- Talks, demos, conference submissions
- Documentation and tutorials

---

## What Ledge is (permitted claims)

Ledge is an experimental programming language designed from first principles
for AI-first software. It is production-quality in its interpreter implementation,
with 556 tests at 100% pass rate and a formal specification.

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

> "Ledge is an AI-native programming language that makes uncertainty explicit at the type level.
> It's a serious engineering project — 556 tests, formal semantics, working LSP and debugger —
> designed for developers who build AI-first applications and need more than Python offers
> for handling uncertain AI outputs safely. Try it: `pip install ledge-lang`."

## Score context

Ledge v1.1.0 scores 974/1000 on the World-Class Audit Protocol (previous protocol).
This audit is ongoing against the 970+ Public Release Protocol.
