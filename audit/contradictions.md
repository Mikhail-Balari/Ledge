# Contradictions and Resolutions
## Ledge v1.1.0 Audit — All Contradictions Resolved

### Resolved in this audit cycle

**C1: classify/generate declared type vs value type**
- Before: `type(classify("x") using ["a","b"])` returned `uncertain[nothing]`
- Root cause: `_type_of()` used value's type, not declared return type
- Fix: Added `declared_type` field to `Uncertain`; classify→"text", generate→"text", embed→"list"
- Evidence: `show type(classify("x") using ["a","b"])` → `uncertain[text]` ✓

**C2: Parser n-1 in function arguments**
- Before: `fib(n-1)` raised ParseError inside function args
- Root cause: Lexer tokenized `-1` as negative literal after identifier
- Fix: Context check in lexer — `-digit` after IDENT/NUMBER/RPAREN = MINUS+digit
- Evidence: `fib(n - 1) + fib(n - 2)` compiles and runs correctly ✓

**C3: Compiler two-pass structure**
- Before: Functions defined in program overwrote `@main` IR block
- Root cause: `begin_function` reset `_current` mid-main compilation  
- Fix: Two-pass: compile all function defs first, then compile main body
- Evidence: All 27 compiler tests pass ✓

**C4: VM for-each loop**
- Before: `for each x in list [1,2,3]` fell back to tree-walker
- Root cause: VM tried to call `__iter__` as a function (doesn't exist)
- Fix: Compile for-each as index-based while loop using `LOAD_INDEX`
- Evidence: VM differential tests 0 divergences across 1500 programs ✓

### Remaining known gaps (not contradictions — documented limitations)

- FFI opens Python stdlib fully (intentional design for research phase)
- No sandbox/quotas (v2.0 roadmap item)
- VM slower than TW on micro-benchmarks (expected — compilation overhead)
