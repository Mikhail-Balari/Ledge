# Ledge Feature Matrix
## Version 1.1.0 — Normative Reference

This document is the authoritative record of every feature in Ledge.
Status definitions are strict and verifiable:

| Status | Meaning |
|---|---|
| **[SHIPPED]** (shipped) | Passes the 7×1 standard: syntax, grammar, semantics, runtime, typechecker, tests, working example |
| **[EXPERIMENTAL]** | Implemented in runtime but not all 7 checks pass — may change |
| **[ROADMAP]** | Planned (roadmap), not implemented. Not available in any current release |
| **removed** | Was experimental, removed for design reasons |

**Rule:** If a feature is not in this matrix, it does not exist in Ledge.

---

## Core Language

| Feature | Status | Notes |
|---|---|---|
| Number literals (int, float) | **[SHIPPED]** | IEEE 754 double |
| String literals with interpolation | **[SHIPPED]** | `{expr}` inside `""` |
| Boolean literals (`true`, `false`) | **[SHIPPED]** | Strict: `true ≠ 1` |
| `nothing` literal | **[SHIPPED]** | Single null-like value |
| List literals `list [...]` | **[SHIPPED]** | |
| Map literals `map {...}` | **[SHIPPED]** | String keys |
| `define x as value` | **[SHIPPED]** | Creates binding |
| `define x: type as value` | **[SHIPPED]** | Type-annotated binding |
| `set x to value` | **[SHIPPED]** | Mutates existing binding |
| `show value` | **[SHIPPED]** | Output with format options |
| `if / else if / else` | **[SHIPPED]** | |
| `for each x in iterable` | **[SHIPPED]** | Lists, maps, strings |
| `for each k, v in map` | **[SHIPPED]** | Key-value iteration |
| `while condition` | **[SHIPPED]** | |
| `repeat N times` | **[SHIPPED]** | |
| `repeat until condition` | **[SHIPPED]** | |
| `break` / `continue` | **[SHIPPED]** | Loop control |
| `pass` | **[SHIPPED]** | No-op placeholder |
| `match / case / otherwise` | **[SHIPPED]** | Pattern matching on equality |
| `check / recover / always` | **[SHIPPED]** | Structured error handling |
| `return` | **[SHIPPED]** | |
| `yield` (generators) | **[SHIPPED]** | Lazy via thread+queue |
| Lambda `given x: expr` | **[SHIPPED]** | Single-expression |
| Function definition `define f(params):` | **[SHIPPED]** | With closures |
| Recursion | **[SHIPPED]** | Direct and mutual |
| User types `type T has:` | **[SHIPPED]** | Immutable field records |
| `import "module" as alias` | **[SHIPPED]** | Stdlib modules |
| `from "module" import name` | **[SHIPPED]** | Selective import |
| `or` fallback operator | **[SHIPPED]** | `expr or default` |
| `is` / `is not` identity check | **[SHIPPED]** | |
| Type annotations (optional) | **[SHIPPED]** | Checked at define/set |

---

## Arithmetic and Operations

| Feature | Status | Notes |
|---|---|---|
| `+` `-` `*` `/` | **[SHIPPED]** | `/` returns `nothing` on zero |
| `divide(a, b)` safe division | **[SHIPPED]** | Returns `nothing` on zero, never crashes |
| `modulo(a, b)` | **[SHIPPED]** | Returns `nothing` if b=0 |
| `power(a, b)` | **[SHIPPED]** | |
| `sqrt(x)` | **[SHIPPED]** | Returns `nothing` if x < 0 |
| `abs`, `floor`, `ceil`, `round` | **[SHIPPED]** | |
| `log`, `sin`, `cos`, `tan` | **[SHIPPED]** | Via `math` stdlib |
| String concatenation `+` | **[SHIPPED]** | Auto-converts numbers |
| List concatenation `+` | **[SHIPPED]** | `merge` is preferred |

---

## AI-Native Features

| Feature | Status | Notes |
|---|---|---|
| `analyze(text) using mode` | **[SHIPPED]** | Returns `Uncertain[Map]` |
| `classify(text) using [labels]` | **[SHIPPED]** | Returns `Uncertain[text]` |
| `generate(prompt) using mode` | **[SHIPPED]** | Returns `Uncertain[text]` |
| `ask(question)` | **[SHIPPED]** | Returns `Uncertain[text]` |
| `embed(text)` | **[SHIPPED]** | Returns `Uncertain[list]` |
| `Uncertain[T]` type | **[SHIPPED]** | First-class AI result type |
| `confidence_of(uncertain)` | **[SHIPPED]** | Returns float in [0.0, 1.0] |
| `value_of(uncertain)` | **[SHIPPED]** | Extracts value |
| `is_confident(uncertain)` | **[SHIPPED]** | confidence >= 0.8 |
| `is_uncertain(uncertain)` | **[SHIPPED]** | |
| `when(uncertain, threshold, fallback)` | **[SHIPPED]** | Safe extraction |
| Zero confidence without backend | **[SHIPPED]** | **CRITICAL**: never fake confidence |
| `nothing` value without backend | **[SHIPPED]** | **CRITICAL**: never invent labels |
| `AuditTrail` automatic logging | **[SHIPPED]** | Every AI call logged |
| `audit_query(op?, limit?)` | **[SHIPPED]** | Query the audit log |
| `audit_export()` | **[SHIPPED]** | Export as JSON |
| AI backend injection | **[SHIPPED]** | `run(src, ai_backend={...})` |
| Custom AI providers | **[SHIPPED]** | Via `ai_backend` dict |
| Uncertain typechecker errors | **[SHIPPED]** | Unsafe use = ERROR |
| `Uncertain` flow typing (static) | **[ROADMAP]** | Union types needed |
| Model versioning in audit | **[ROADMAP]** | |
| Distributed audit storage | **[ROADMAP]** | |

---

## Streams

| Feature | Status | Notes |
|---|---|---|
| `stream_of(list)` | **[SHIPPED]** | Re-iterable |
| `stream_where(s, predicate)` | **[SHIPPED]** | Lazy filter |
| `stream_map(s, fn)` | **[SHIPPED]** | Lazy transform |
| `stream_take(s, n)` | **[SHIPPED]** | First n items |
| `stream_collect(s)` | **[SHIPPED]** | Force to list |
| `stream_first(s)` | **[SHIPPED]** | First item or nothing |
| `collect(generator)` | **[SHIPPED]** | Force generator to list |
| `when s has new item as x:` | **[SHIPPED]** | Reactive iteration |
| Infinite generators | **[SHIPPED]** | Via `yield`, lazy queue |
| `stream from "url"` | **[EXPERIMENTAL]** | Parses but URL not connected |
| WebSocket streams | **[ROADMAP]** | |
| MQTT/IoT streams | **[ROADMAP]** | |
| File tail streams | **[ROADMAP]** | |
| Window aggregation | **[ROADMAP]** | |
| `subscribe to / emit to` | **[EXPERIMENTAL]** | Basic syntax only |

---

## Contracts

| Feature | Status | Notes |
|---|---|---|
| `requires:` preconditions | **[SHIPPED]** | Checked before body |
| `ensures:` postconditions | **[SHIPPED]** | Checked after body |
| `result` binding in ensures | **[SHIPPED]** | |
| Contract violation = LedgeError | **[SHIPPED]** | Body never runs on fail |
| Contracts on recursive fns | **[SHIPPED]** | |
| Contracts on nested calls | **[SHIPPED]** | |
| Static contract verification | **[ROADMAP]** | Requires type inference |
| Contracts on types | **[ROADMAP]** | |

---

## Parallel Execution

| Feature | Status | Notes |
|---|---|---|
| `parallel [e1, e2, ...]` | **[SHIPPED]** | Real threading |
| Result order preserved | **[SHIPPED]** | Same order as declaration |
| Error from any branch propagates | **[SHIPPED]** | |
| `parallel` with empty list | **[SHIPPED]** | Returns `[]` |
| Distributed parallel | **[ROADMAP]** | Multiple machines |
| `async` modifier | **[ROADMAP]** | Non-blocking I/O |

---

## Python FFI

| Feature | Status | Notes |
|---|---|---|
| `import "python:module" as alias` | **[SHIPPED]** | Full Python ecosystem |
| Calling Python functions | **[SHIPPED]** | Args auto-converted |
| Returning Python objects | **[SHIPPED]** | Wrapped as PythonObject |
| Python dicts → LedgeMap | **[SHIPPED]** | Auto-converted |
| Python lists → LedgeList | **[SHIPPED]** | Auto-converted |
| Python None → nothing | **[SHIPPED]** | |
| Error handling on FFI fail | **[SHIPPED]** | LedgeError with message |
| C FFI (ctypes) | **[EXPERIMENTAL]** | Via Python interop |
| Direct C bindings | **[ROADMAP]** | |

---

## Tooling

| Feature | Status | Notes |
|---|---|---|
| `ledge run file.ledge` | **[SHIPPED]** | |
| `ledge check file.ledge` | **[SHIPPED]** | Syntax check |
| `ledge fmt file.ledge` | **[SHIPPED]** | Canonical formatter |
| `ledge fmt --check` | **[SHIPPED]** | Check without modifying |
| `ledge debug file.ledge` | **[SHIPPED]** | Step-through debugger |
| `ledge version` | **[SHIPPED]** | |
| Interactive REPL | **[SHIPPED]** | `ledge` with no args |
| LSP server | **[SHIPPED]** | Diagnostics, completion, hover |
| VS Code extension | **[SHIPPED]** | Syntax highlighting, snippets |
| Browser playground | **[ROADMAP]** | Planned for v1.3, not yet available |
| `ledge test` command | **[SHIPPED]** | Runs test suite |
| Formatter idempotency | **[SHIPPED]** | Checked on the project corpus |
| Type checker (`ledge check --types`) | **[SHIPPED]** | AI-aware |
| Profiler | **[ROADMAP]** | |
| Package manager | **[ROADMAP]** | |
| Documentation generator | **[ROADMAP]** | |

---

## Compilation and Deployment

| Feature | Status | Notes |
|---|---|---|
| Tree-walker interpreter | **[SHIPPED]** | Reference implementation |
| Bytecode compiler | **[SHIPPED]** | Core subset only |
| Bytecode VM | **[SHIPPED]** | Core subset; generates IR for native compilation |
| VM differential testing | **[SHIPPED]** | 40 tests, 0 divergences |
| `--target native` | **[ROADMAP]** | LLVM backend |
| `--target wasm` | **[ROADMAP]** | Browser deployment |
| `--target arm32` | **[ROADMAP]** | Embedded deployment |
| `--target serverless` | **[ROADMAP]** | AWS Lambda / Cloud Functions |
| Universal runtime | **[ROADMAP]** | Single binary, any platform |

---

## NOT IN LEDGE (by design)

These are deliberate absences, not missing features:

| Absent Feature | Design Reason |
|---|---|
| Multiple assignment operators (`=` for assign) | `=` is always comparison. `set x to` is mutation. Eliminates entire bug class. |
| `null` AND `undefined` | One bottom value `nothing`. No Tony Hoare billion-dollar mistake. |
| Implicit type coercions | `true + 1` is an error. No silent coercions. |
| Exception hierarchy (raise/throw) | `check/recover/always` is the only mechanism. Visible error handling. |
| Multiple string formats | One way: `"text {expr}"`. No `%`, no `.format()`, no f-strings variants. |
| Inheritance | Types have fields. No inheritance. Composition is favored. |
| `null` references | Every access returns `nothing` or raises `LedgeError`. Never segfault. |
| Mutable default arguments | Python's most famous gotcha. Not possible in Ledge. |
| Ternary operator `? :` | `if/else` blocks only. One way to express conditionals. |
| `++` / `--` operators | `set x to x + 1` only. Explicit mutation. |

---

## Version history

| Version | Status |
|---|---|
| 0.1.0 | Core language, basic tooling |
| 0.2.0 | Lazy generators, Python FFI, real parallel |
| 1.0.0 | AI-native types, Uncertain[T], Stream, Contracts, AuditTrail, 7×1 compliance |

---

*This document is normative. If code diverges from this matrix, the code is wrong.*
*If this matrix diverges from intent, update the matrix and the code together.*
