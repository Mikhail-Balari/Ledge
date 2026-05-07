# Documentation Truth Matrix — Ledge v1.1.0

| Claim | Status | Evidence |
|-------|--------|----------|
| Uncertain[T] typechecker enforced | VERIFIED | test_typechecker.py |
| analyze() no backend → confidence=0 | VERIFIED | test_install_smoke.py |
| Formatter idempotent | VERIFIED | 7 examples + property tests |
| 284 conformance tests | VERIFIED | conformance.py → 284/284 |
| 0 differential divergences | VERIFIED | tests/differential/ 1500 programs |
| WASM target = roadmap | ACCURATE | FEATURE_MATRIX.md roadmap |
| LLVM IR codegen works | VERIFIED | tests/compiler/ 27 tests |
| Contracts runtime-verified | VERIFIED | test_core_language.py |
| n-1 in function args works | VERIFIED | Fixed this cycle — lexer context check |
| declare_type for classify | VERIFIED | Fixed this cycle — uncertain[text] |
