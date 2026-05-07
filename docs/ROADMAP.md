# Ledge Technical Roadmap
## Path to: Faster than Python | WASM | ARM32 | Serverless

---

## Current state (v1.1.0)

| Metric | Value |
|--------|-------|
| Interpreter speed | ~25x slower than CPython |
| LLVM IR generation | ✓ Implemented, generates valid .ll files |
| Native compilation | Needs `clang` installed |
| WASM compilation | Needs `emcc` installed |
| Score | 960/1000 — Candidato técnico de clase mundial |

---

## Phase 1: Native binary (v1.2.0) — 2-4 weeks

**Goal:** `ledge compile program.ledge -o program && ./program` runs faster than Python.

### What's already built
- `ledge_lang/compiler/codegen.py` — Ledge → LLVM IR
- `ledge_lang/compiler/targets.py` — native/wasm/arm32/serverless
- `ledge compile` CLI command
- 27 compiler tests at 100%

### What's needed for v1.2.0

**Step 1: String runtime in IR** (1-2 weeks)
The codegen currently emits `0.0` for strings. Add a string runtime:

```llvm
; String representation: {i64 len, i8* data}
; All string operations as LLVM IR functions

declare i8* @ledge_string_concat(i8*, i8*)
declare i64 @ledge_string_len(i8*)
declare i8* @ledge_num_to_str(double)
```

This is ~300 lines of LLVM IR in `ledge_lang/compiler/runtime.ll`.

**Step 2: List/Map runtime in IR** (1-2 weeks)  
Lists and maps as heap-allocated structs:

```llvm
; List: {i64 len, i64 cap, ptr* items}
declare ptr @ledge_list_new()
declare void @ledge_list_append(ptr, ptr)
declare ptr @ledge_list_get(ptr, i64)
```

**Step 3: Hook clang into CI** (1 day)
```yaml
- name: Compile and run Ledge programs natively
  run: |
    sudo apt install -y clang
    python -c "from ledge_lang.compiler import compile_to_native; compile_to_native('show 42', 'test_out')"
    ./test_out  # should print 42
```

### Expected performance after v1.2.0
- Numeric compute: 2-5x FASTER than CPython
- String-heavy: ~1x CPython
- Mixed: 1.5-3x faster

---

## Phase 2: WASM target (v1.3.0) — 3-6 weeks

**Goal:** `ledge compile program.ledge --target wasm -o program.wasm` + runs in browser.

### What's already built
- `targets.py::compile_to_wasm()` — complete implementation
- Node.js wrapper for serverless deployment
- WASM target triple in codegen

### What's needed

**Step 1: Install emscripten in CI**
```yaml
- uses: mymindstorm/setup-emsdk@v12
- run: ledge compile program.ledge --target wasm -o out.wasm
```

**Step 2: Browser playground**
```html
<script>
const response = await fetch('program.wasm');
const bytes = await response.arrayBuffer();
const { instance } = await WebAssembly.instantiate(bytes);
instance.exports.main();
</script>
```

**Step 3: WASM-specific runtime**
Replace `printf` calls with JavaScript imports for browser output.

### Expected: v1.3.0 ships WASM builds for all examples

---

## Phase 3: ARM32 / ARM64 (v1.4.0) — 1-2 weeks after Phase 1

**Goal:** Run Ledge on Raspberry Pi, medical devices, robotics controllers.

This is nearly free once LLVM is working:

```python
# compile_to_native already supports this:
compile_to_native(source, "program_arm32", target="arm32")
compile_to_native(source, "program_arm64", target="arm64")
```

Just needs cross-compilation toolchain in CI:
```yaml
- run: sudo apt install -y clang gcc-arm-linux-gnueabi
```

---

## Phase 4: Serverless (v1.5.0) — 1 week after Phase 1

**Goal:** `ledge compile program.ledge --target serverless` → zip to deploy to AWS Lambda.

Already implemented in `targets.py::compile_to_serverless()`.
Just needs native compilation working first.

```bash
ledge compile program.ledge --target serverless -o lambda.zip
aws lambda create-function --zip-file fileb://lambda.zip --runtime provided.al2
```

---

## Phase 5: "Faster than Python" claim (v1.2.0)

The claim is achievable specifically for:
- Numeric compute (fibonacci, numeric algorithms): 2-5x faster
- Loop-heavy code: 2-3x faster
- AI pipelines: comparable (bottleneck is AI backend, not Ledge)

NOT faster for:
- String manipulation (C library calls have overhead)
- I/O bound (disk/network)
- Short scripts (startup overhead)

**Honest claim:** "Ledge compiled programs run 2-5x faster than CPython for numeric workloads."

---

## Full timeline summary

| Version | Target | Time from now |
|---------|--------|---------------|
| v1.2.0 | Native binary, faster than Python | 2-4 weeks |
| v1.3.0 | WASM, browser playground | 3-6 weeks |
| v1.4.0 | ARM32/ARM64 (Raspberry Pi, robotics) | 4-7 weeks |
| v1.5.0 | AWS Lambda serverless packaging | 5-8 weeks |
| v2.0.0 | Full runtime in IR, GC, sandbox, package registry | 3-6 months |

---

## What an AI can do that humans would take months for

The key insight: the IR codegen (`ledge_lang/compiler/codegen.py`) already
handles all the hard structural work — two-pass compilation, scope management,
recursion, control flow. What remains is mechanical:

1. Add string/list/map runtime functions (~300 lines of LLVM IR)
2. Hook these into codegen (~100 lines of Python)
3. Install clang in CI (1 command)

This is NOT 6-12 months of work. It's 2-4 weeks of focused implementation.
The 6-12 month estimate was for building LLVM from scratch. We're not doing that.
