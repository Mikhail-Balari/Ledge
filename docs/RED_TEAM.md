# Ledge Red Team Analysis
## Living document — updated after every major release

This document maintains the strongest criticisms against Ledge and tracks
whether each has been resolved. A criticism is "closed" only when
a neutral reviewer would agree the evidence is sufficient.

**Rule:** No criticism is marked CLOSED without verifiable evidence.

---

## Active criticisms (must resolve)

### C-01: "This is Python with different keywords"

**Strength:** High  
**Status:** Partially mitigated  

**The attack:** `define x as 10` → `x = 10`, `for each item in items` → `for item in items`,
`check/recover/always` → `try/except/finally`. A simple transpiler maps Ledge to Python.

**Evidence for the attack:** The interpreter is Python. The runtime is Python GC.
The types are Python types.

**Rebuttal evidence:**
1. `true ≠ 1`, `false ≠ 0`, `nothing ≠ null` — strict type semantics Python doesn't have
2. `Uncertain[T]` is a first-class type — Python has no equivalent
3. `requires:/ensures:` contracts are built-in — Python needs third-party libraries
4. AI operations always return `Uncertain` with `confidence=0.0` without backend — Python would crash or lie
5. A transpiler to Python cannot preserve these semantics without substantial instrumentation

**Test that decides:** Write the transpiler. Measure lines of instrumentation needed.
If it requires >100 lines of glue code per Ledge feature, the criticism is invalid.

**What still needs doing:** Benchmark showing Ledge AI programs have lower first-run error rate

---

### C-02: "The AI claim is marketing without substance"

**Strength:** Very high  
**Status:** Partially mitigated  

**The attack:** `analyze(text) using sentiment` compiles to a function call.
The "AI as primitive" is syntactic sugar.

**Rebuttal evidence:**
1. `Uncertain[T]` forces error handling at the type level — impossible in Python without mypy + custom types
2. Zero confidence without backend = language-level safety, not convention
3. Audit trail is automatic for every AI call — no Python library does this by default
4. Typechecker errors on unsafe `Uncertain` use — structural AI safety

**Test that decides:** Run 50 tasks asking GPT-4 to implement them in Ledge and Python.
Measure first-run correctness. If Ledge wins significantly (>10%), claim is validated.

**Current state:** Experiment in `experiments/ai_validation.py` — 8 tasks, not statistically significant.

---

### C-03: "Generators are lazy but still limited"

**Strength:** Medium  
**Status:** Resolved  

**The attack:** Infinite generators hang because Ledge uses eager evaluation.

**Evidence of resolution:**
- `naturals(1)[999]` returns `1000` without hanging
- Thread+queue architecture for truly lazy evaluation
- Test: `tests/unit/test_ai_native.py::TestStreams::test_infinite_generator` ✓

---

### C-04: "Without interoperability, Ledge is an island"

**Strength:** Was critical — now mitigated  
**Status:** Mitigated  

**The attack:** Can't use numpy, pandas, requests, or any existing library.

**Evidence of resolution:**
- `import "python:numpy" as np` works
- Full Python ecosystem available in one line
- Test: `tests/unit/test_ai_native.py::TestPythonFFI` ✓

**What remains:** No native Ledge packages yet. Package manager is roadmap.

---

### C-05: "Performance is unacceptable"

**Strength:** High for compute-heavy code  
**Status:** Acknowledged, not resolved  

**The attack:** 28x slower than CPython on loops. 1000x on recursive code.

**Honest response:** This is accurate. Ledge v1.0 is a reference interpreter.
The roadmap (LLVM backend) will close this gap, but that's 6-12 months of work.

**Why it doesn't block adoption:** Python itself is 50-100x slower than C.
AI workloads are I/O bound (model inference), not compute bound.
For AI pipelines, Ledge's overhead is acceptable today.

**Test that decides:** Benchmark AI pipeline (classify 1000 texts) total time including
model inference. If Ledge overhead is <5% of total time, it's not a blocker.

---

### C-06: "The docs don't match the runtime"

**Strength:** Was critical — now resolved  
**Status:** Resolved  

**Evidence of resolution:**
- FEATURE_MATRIX.md explicitly marks shipped vs experimental vs roadmap
- `--target wasm/arm32` moved to roadmap in matrix
- `stream from "url"` marked experimental
- `agent/MCP` marked experimental
- CI job compares docs with feature matrix
- All examples in docs execute correctly

---

### C-07: "The typechecker is advisory and useless"

**Strength:** Was high — now mitigated  
**Status:** Mitigated  

**The attack:** The typechecker only warns, never blocks unsafe code.

**Evidence of resolution:**
- Using `Uncertain` without extraction is now an **ERROR** (not warning)
- Using `analyze()` result as direct value (e.g., `show upper(ai_result)`) is ERROR
- Test: `tests/unit/test_ai_native.py` — typechecker enforcement verified

**What remains:** No static flow typing (after `if is_confident(r):`, type is not narrowed).
This requires union types — roadmap item.

---

### C-08: "The VM is decorative"

**Strength:** Medium  
**Status:** Partially mitigated  

**The attack:** The VM handles only trivial cases. Real programs use the tree-walker.

**Evidence of mitigation:**
- VM official subset documented in `tests/differential/test_vm_vs_treewalker.py`
- 40 differential tests, 0 divergences
- VM is 2.5x faster on recursive code

**What remains:** VM doesn't handle closures, generators, AI operations, or FFI.
These are documented in FEATURE_MATRIX.md under "Bytecode VM — Core subset only".

---

### C-09: "AI confidence is fake without a backend"

**Strength:** Was CRITICAL — now resolved  
**Status:** RESOLVED  

**The attack:** `analyze("text") using sentiment` returns confidence=1.0 even without AI.

**Evidence of resolution:**
- `confidence=0.0` always when no backend is connected
- `value=nothing` always for classify without backend (never picks first label)
- Tests: `TestAIWithoutBackend` class — 9 tests all passing
- CI enforces this with `test_analyze_zero_confidence` and `test_classify_not_first_label`

---

### C-10: "No governance — bus factor = 1"

**Strength:** High  
**Status:** Partially mitigated  

**The attack:** One person abandons the project, it dies.

**Evidence of mitigation:**
- GOVERNANCE.md defines processes
- All design decisions documented
- MIT license allows forking
- Test suite comprehensive enough for new maintainers

**What remains:** Still one primary author. Target is 3+ by v1.2.0.

---

## Closed criticisms

| ID | Criticism | Closed in |
|---|---|---|
| C-03 | Generators hang on infinite sequences | v0.2 |
| C-04 | No interoperability | v0.2 |
| C-06 | Docs don't match runtime | v1.0 |
| C-07 | Typechecker is advisory | v1.0 |
| C-09 | Fake AI confidence | v1.0 |

---

## Score: open critical criticisms

| Severity | Count | Items |
|---|---|---|
| Critical (blocks credibility) | 0 | All resolved |
| High (limits adoption) | 2 | C-02 (AI claim unproven), C-05 (performance) |
| Medium (slows growth) | 2 | C-01 (Python resemblance), C-08 (VM subset), C-10 (bus factor) |

**Next action:** Design and run the AI generation quality experiment (C-02).
This is the single most important remaining validation.
