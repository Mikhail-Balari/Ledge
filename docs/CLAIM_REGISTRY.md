# Ledge Claim Registry
## Version 1.1.0

Every public claim about Ledge must appear here with a link to verifiable evidence.
Claims without evidence are prohibited in README, blog posts, CLI output and demos.

---

## Claims about AI-native semantics

| Claim | Evidence | Status |
|-------|----------|--------|
| AI operations never fabricate confidence without a backend | tests/integration/test_install_smoke.py::test_ai_safety_invariant | ✓ VERIFIED |
| classify() returns uncertain[text], never a fabricated label | tests/unit/test_ai_native.py | ✓ VERIFIED |
| Uncertain[T] use without extraction is a typechecker ERROR | tests/unit/test_typechecker.py | ✓ VERIFIED |
| Audit trail logs all AI calls with input hash, not plaintext | tests/integration/test_install_smoke.py::test_audit_trail_works | ✓ VERIFIED |
| After `if is_confident(r):` guard, r is narrowed to safe type | tests/unit/test_typechecker.py (flow typing) | ✓ VERIFIED |

## Claims about language correctness

| Claim | Evidence | Status |
|-------|----------|--------|
| 284 conformance tests pass at 100% | python tests/conformance.py | ✓ VERIFIED |
| 556 total tests pass at 100% | python -m ledge_lang.test_runner tests/ | ✓ VERIFIED |
| 0 divergences between VM and tree-walker (1500 random programs) | tests/differential/ | ✓ VERIFIED |
| true ≠ 1, false ≠ 0, nothing ≠ false (strict semantic invariants) | tests/unit/test_core_language.py | ✓ VERIFIED |
| divide(x, 0) returns nothing, never crashes | tests/conformance.py | ✓ VERIFIED |
| Recursion depth exceeded → LedgeError with actionable message | tests/integration/test_install_smoke.py | ✓ VERIFIED |
| 0 crashes in parser fuzzing (adversarial corpus) | tests/fuzz_suite/test_fuzzer.py | ✓ VERIFIED |

## Claims about tooling

| Claim | Evidence | Status |
|-------|----------|--------|
| Formatter is idempotent on all official examples | tests/unit/test_properties.py | ✓ VERIFIED |
| Formatter preserves program semantics (round-trip) | tests/unit/test_properties.py::test_format_preserves_semantics | ✓ VERIFIED |
| LSP includes AI-native completions (analyze, when, confidence_of) | ledge_lang/lsp.py + manual inspection | ✓ VERIFIED |
| Debugger shows Uncertain values with confidence | ledge_lang/debugger.py | ✓ VERIFIED |

## Claims about performance

| Claim | Evidence | Status |
|-------|----------|--------|
| Tree-walker is ~25x slower than CPython on loop benchmarks | audit/benchmark_results.json | ✓ HONEST |
| LLVM IR generation produces valid .ll files | tests/compiler/test_codegen.py | ✓ VERIFIED |
| Native binary compilation needs clang (v1.2 roadmap) | docs/ROADMAP.md | ✓ ACCURATE |

## Claims about security

| Claim | Evidence | Status |
|-------|----------|--------|
| --restrict-ffi blocks non-allowlisted Python modules | tests/integration (allowed_modules tests) | ✓ VERIFIED |
| Iteration limiter raises LedgeError at N iterations | tests/integration | ✓ VERIFIED |
| Input secrets not logged in plaintext to audit trail | tests/integration::test_audit_trail_works | ✓ VERIFIED |

## PROHIBITED CLAIMS (not yet proven)

The following claims are NOT allowed in public materials:

| Prohibited Claim | Why | When Allowed |
|-----------------|-----|--------------|
| "Ledge runs faster than Python" | Requires clang compilation (v1.2) | After v1.2 release |
| "Supports WASM/ARM32/serverless" | Requires emcc/clang | After v1.3 release |
| "Ready for production critical systems" | No formal sandbox or GC | After v2.0 |
| "Ecosystem of packages" | 0 native packages exist | When packages exist |
