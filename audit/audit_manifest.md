# Audit Manifest — Ledge v1.1.0
Generated: 2026-03-29T03:53:51Z

## Coverage by domain

| Domain | Tests | Passed | Status |
|--------|-------|--------|--------|
| A Identity | 6 | 6 | ✓ FULL |
| B Spec/Grammar | 6 | 6 | ✓ FULL |
| C Static types | 6 | 5 | ~ PARTIAL (C5) |
| D Dynamic semantics | 6 | 6 | ✓ FULL |
| E Errors/Uncertainty | 6 | 6 | ✓ FULL |
| F Compiler/VM | 6 | 5 | ~ PARTIAL (F3) |
| G Concurrency | 6 | 6 | ✓ FULL |
| H Memory/Resources | 6 | 5 | ~ PARTIAL (H5 no sandbox) |
| I Security | 6 | 4 | ~ PARTIAL (I1/I3 FFI open) |
| J Interop/Packaging | 6 | 6 | ✓ FULL |
| K Tooling/DX | 6 | 6 | ✓ FULL |
| L Documentation | 6 | 5 | ~ PARTIAL (L3 no user study) |
| M Performance | 6 | 5 | ~ PARTIAL (M3 VM overhead) |
| N Testing/Release | 6 | 5 | ~ PARTIAL (N6 manual gates) |
| O AI-native | 6 | 6 | ✓ FULL |

## Evidence artifacts

| Artifact | Lines | Status |
|----------|-------|--------|
| tests/test_ledge.py | 150 tests | ✓ 100% |
| tests/conformance.py | 284 tests | ✓ 100% |
| tests/unit/ | 155 tests | ✓ 100% |
| tests/differential/ | 47 tests | ✓ 0 divergences |
| tests/compiler/ | 27 tests | ✓ 100% |
| tests/integration/ | 13 tests | ✓ 100% |
| tests/fuzz_suite/ | 10 tests | ✓ 0 crashes |
| examples/ | 7 programs | ✓ all run |
| docs/ | 14 docs | ✓ all present |
| ledge_lang/compiler/ | 3 modules | ✓ IR generation verified |
| audit/ | 10 artifacts | ✓ this manifest |

## Hard gates

G1 ✓ G2 ✓ G3 ✓ G4 ✓ G5 ✓ G6 ✓ G7 ✓ G8 ✓ G9 ✓ G10 ✓

All 10 hard gates pass. No score cap applies.

## Fixes applied in this audit cycle

1. **Parser/Lexer**: `f(n-1)` ParseError — context check in lexer
2. **O2**: `classify()` type `uncertain[nothing]` → `uncertain[text]`  
3. **VM**: `for each x in list:` fell back to tree-walker — compiled now
4. **Compiler**: Two-pass compilation preserves `@main` function structure
5. **Compiler**: `divide()` builtin generates safe-division IR
6. **Compiler**: Recursive functions register in scope before body compilation
7. **SPEC.md**: Edge Cases section added
8. **Compiler**: Full LLVM IR + targets infrastructure built
