# Ledge Formal Operational Semantics
## Version 1.0 — Normative Reference

This document defines the meaning of Ledge programs independently of any
implementation. A conforming implementation must produce exactly the results
described here for all valid programs.

---

## 1. Notation

```
e       expression
s       statement
σ       environment (variable store): Name → Value
v       value
τ       type
C       confidence level ∈ [0.0, 1.0]
⊥       nothing (bottom value)
⟦e⟧σ   evaluation of expression e in environment σ
⟦s⟧σ   execution of statement s, producing new environment σ'
```

---

## 2. Value Domain

```
Value ::= ⊥                          -- nothing
        | n ∈ ℝ                      -- number (IEEE 754 double)
        | s ∈ String                 -- text (UTF-8)
        | true | false               -- truth
        | List[Value]                -- ordered sequence
        | Map[String → Value]        -- string-keyed dictionary
        | Function(params, body, σ)  -- closure
        | Type(name, fields)         -- type descriptor
        | Instance(type, fields)     -- type instance
        | Uncertain(v, C)            -- value with confidence
        | Stream(gen)                -- lazy sequence generator
        | Pipeline(stages)           -- composable transformation
```

Key invariants:
- `true ≠ 1`, `false ≠ 0` (strict boolean/number separation)
- `⊥ ≠ false`, `⊥ ≠ 0`, `⊥ ≠ ""` (nothing is unique)
- `C ∈ [0.0, 1.0]` always (confidence is clamped)

---

## 3. Environment

An environment σ is a linked chain of frames:
```
σ ::= ∅               -- empty (global frame)
    | σ[x ↦ (v, τ?)] -- frame binding x to v with optional type annotation
```

**Lookup:** `σ(x)` walks the chain from innermost to outermost.
If not found: `LedgeError("'x' is not defined")`.

**Define:** `σ[x ↦ (v, τ?)]` adds x to the current frame.
If τ is given and `v ≠ ⊥ ∧ ¬compatible(v, τ)`: `LedgeError`.

**Assign (set):** Finds x in any enclosing frame and updates it in place.
If x not found: `LedgeError("'x' is not defined")`.
If x has annotation τ and `¬compatible(v, τ)`: `LedgeError`.

---

## 4. Expression Semantics

### 4.1 Literals

```
⟦n⟧σ      = n           -- number
⟦"s"⟧σ    = s           -- string (with interpolation applied)
⟦true⟧σ   = true
⟦false⟧σ  = false
⟦nothing⟧σ = ⊥
```

**String interpolation:** `"{e}"` evaluates `e` in σ, converts to text, and splices.

### 4.2 Arithmetic

```
⟦e₁ + e₂⟧σ  where ⟦e₁⟧σ = n₁, ⟦e₂⟧σ = n₂, both ∈ ℝ\Bool  = n₁ + n₂
⟦e₁ + e₂⟧σ  where either ∈ String                          = repr(e₁) ++ repr(e₂)
⟦e₁ - e₂⟧σ                                                  = n₁ - n₂
⟦e₁ * e₂⟧σ                                                  = n₁ × n₂
⟦e₁ / e₂⟧σ  where n₂ = 0                                   = ⊥   -- never crashes
⟦e₁ / e₂⟧σ  where n₂ ≠ 0                                   = n₁ ÷ n₂
```

**Critical invariant:** Division by zero returns `⊥`, never raises an error.
This is the foundational safety guarantee of Ledge.

### 4.3 Comparison

```
⟦e₁ = e₂⟧σ   = ⊥_eq(⟦e₁⟧σ, ⟦e₂⟧σ)
⟦e₁ != e₂⟧σ  = ¬⊥_eq(⟦e₁⟧σ, ⟦e₂⟧σ)
```

Where `⊥_eq` is defined:
```
⊥_eq(⊥, ⊥)           = true
⊥_eq(⊥, v) where v≠⊥ = false
⊥_eq(true, 1)         = false   -- strict: booleans ≠ numbers
⊥_eq(false, 0)        = false   -- strict: booleans ≠ numbers
⊥_eq(v₁, v₂)          = (v₁ = v₂) by value
```

### 4.4 Logic (short-circuit)

```
⟦e₁ and e₂⟧σ = let v₁ = ⟦e₁⟧σ in if truthy(v₁) then ⟦e₂⟧σ else v₁
⟦e₁ or e₂⟧σ  = let v₁ = ⟦e₁⟧σ in if truthy(v₁) then v₁ else ⟦e₂⟧σ
⟦not e⟧σ     = ¬truthy(⟦e⟧σ)
```

**Truthiness:**
```
truthy(⊥)     = false
truthy(false) = false
truthy(0)     = false
truthy("")    = false
truthy([])    = false
truthy({})    = false
truthy(v)     = true  for all other v
```

### 4.5 The Fallback Operator

```
⟦e₁ or e₂⟧σ  (in fallback position, after fallible operation)
  = let v = ⟦e₁⟧σ in if v ≠ ⊥ then v else ⟦e₂⟧σ
```

**Fallback position** is after expressions that may return ⊥:
- `divide(a, b) or default`
- `list[i] or default`
- `map[key] or default`
- `number("string") or default`
- Any function call with `or` immediately following

**Evaluation guarantee:** `e₁` is evaluated exactly once. If it returns ⊥,
`e₂` is evaluated and returned. Otherwise `e₂` is never evaluated.

### 4.6 Function Call

```
⟦f(a₁, ..., aₙ)⟧σ
  = let v = σ(f) in
    let args = [⟦a₁⟧σ, ..., ⟦aₙ⟧σ] in
    apply(v, args, σ)
```

**Apply for LedgeFunction:**
```
apply(Function(params, body, σ_closure), args, σ_call)
  = let σ' = σ_closure[p₁↦a₁, ..., pₙ↦aₙ] in
    check_preconditions(body.contract, σ') in    -- if contract exists
    let result = eval_body(body, σ') in
    check_postconditions(body.contract, result) in  -- if contract exists
    result
```

**Parameter arity:** Missing required parameter → `LedgeError`.
Extra keyword arguments are allowed and bound in scope.

### 4.7 Uncertain Type

```
⟦analyze(e) using mode⟧σ
  = let text = ⟦e⟧σ in
    let (result, confidence) = ai_backend.analyze(text, mode) in
    audit_trail.record("analyze", text, result, confidence) in
    Uncertain(result, confidence)

⟦classify(e) using [l₁,...,lₙ]⟧σ
  = let text = ⟦e⟧σ in
    let (label, confidence) = ai_backend.classify(text, [l₁,...,lₙ]) in
    audit_trail.record("classify", text, label, confidence) in
    Uncertain(label, confidence)
```

**When no AI backend is connected:**
```
⟦analyze(e) using mode⟧σ  = Uncertain(⊥, 0.0)
⟦classify(e) using labels⟧σ = Uncertain(labels[0], 0.0)
```

**Key property:** AI instructions never raise errors. They always return
`Uncertain(⊥, 0.0)` on failure. Programs must handle low-confidence results
explicitly using `when(result, threshold, fallback)`.

### 4.8 Stream Semantics

A `Stream[T]` is a potentially infinite lazy sequence:

```
Stream(gen) where gen: unit → (T | done) is a coroutine
```

**Operations:**
```
stream_where(s, pred) = Stream(λ. for each item in s: if pred(item) then yield item)
stream_map(s, fn)     = Stream(λ. for each item in s: yield fn(item))
stream_take(s, n)     = Stream(λ. take first n items from s)
stream_collect(s)     = [v₁, v₂, ..., vₙ] for finite s (or error for infinite without take)
stream_first(s)       = first item of s, or ⊥ if empty
```

**Laziness guarantee:** Streams do not evaluate more elements than consumed.
`stream_take(s, 0)` evaluates zero elements of s.

**Re-iteration:** Streams created from lists are re-iterable.
Streams created from external sources (file, network) are consumed once.

---

## 5. Statement Semantics

### 5.1 Define

```
⟦define x as e⟧σ  = σ[x ↦ (⟦e⟧σ, none)]
⟦define x: τ as e⟧σ
  where ⟦e⟧σ = v and compatible(v, τ)  = σ[x ↦ (v, τ)]
  where ¬compatible(v, τ)              = LedgeError
```

### 5.2 Assign

```
⟦set x to e⟧σ
  where x ∈ dom(σ) and no type annotation  = σ{x ↦ ⟦e⟧σ}
  where x ∈ dom(σ), annotation τ, compatible(⟦e⟧σ, τ)  = σ{x ↦ ⟦e⟧σ}
  where x ∈ dom(σ), annotation τ, ¬compatible(⟦e⟧σ, τ) = LedgeError
  where x ∉ dom(σ)                                       = LedgeError
```

### 5.3 Show

```
⟦show e⟧σ = let v = ⟦e⟧σ in output(repr(v)); σ
```

### 5.4 If

```
⟦if e: b₁ else: b₂⟧σ
  = if truthy(⟦e⟧σ) then ⟦b₁⟧σ else ⟦b₂⟧σ

⟦if e: b₁⟧σ
  = if truthy(⟦e⟧σ) then ⟦b₁⟧σ else σ
```

### 5.5 For

```
⟦for each x in e: body⟧σ
  = let items = collect(⟦e⟧σ) in
    fold over items: λ σ' item. ⟦body⟧(σ'[x↦item])
    (break terminates fold, continue skips to next)
```

### 5.6 While / Repeat

```
⟦while e: body⟧σ
  = if truthy(⟦e⟧σ) then ⟦while e: body⟧(⟦body⟧σ) else σ

⟦repeat n times: body⟧σ
  = ⟦for each _ in range(⟦n⟧σ): body⟧σ

⟦repeat until e: body⟧σ
  = ⟦while not e: body⟧σ
```

### 5.7 Match

```
⟦match e: case v₁: b₁ ... case vₙ: bₙ otherwise: b⟧σ
  = let subject = ⟦e⟧σ in
    find first i where ⊥_eq(subject, ⟦vᵢ⟧σ) → ⟦bᵢ⟧σ
    if none match → ⟦b⟧σ (or σ if no otherwise)
```

### 5.8 Check (Error Handling)

```
⟦check: b recover x: r always: a⟧σ
  = try:
      result ← ⟦b⟧σ
      ⟦a⟧σ
      result
    catch LedgeError(msg):
      ⟦a⟧(σ[x↦msg])  -- always runs
      ⟦r⟧(σ[x↦msg])
```

**Error propagation rule:** Any LedgeError propagates up the call stack
until caught by a `check` block. Uncaught errors terminate with a message.

### 5.9 Contracts

```
⟦define f(params): requires: req ensures: ens body⟧σ
  = σ[f ↦ Function(params, body, σ, contract=Contract(req, ens))]

apply(Function(..., contract=c), args, σ')
  = for each r in c.requires:
      if ¬truthy(⟦r⟧σ'): raise LedgeError("Precondition failed: " + repr(r))
    let result = eval_body(body, σ') in
    for each e in c.ensures:
      let σ'' = σ'[result ↦ result] in
      if ¬truthy(⟦e⟧σ''): raise LedgeError("Postcondition failed: " + repr(e))
    result
```

### 5.10 When (Reactive)

```
⟦when stream has new item as x: body⟧σ
  = for each item in ⟦stream⟧σ:
      ⟦body⟧(σ[x ↦ item])

⟦when condition: body⟧σ
  = if truthy(⟦condition⟧σ): ⟦body⟧σ
```

### 5.11 Parallel

```
⟦parallel [e₁, ..., eₙ]⟧σ
  = concurrently evaluate all eᵢ in σ
    collect results in order: [v₁, ..., vₙ]
    if any eᵢ raises LedgeError: propagate first error
```

**Ordering guarantee:** Results are returned in declaration order regardless
of evaluation order. Errors from any parallel branch propagate immediately.

---

## 6. Type Compatibility

```
compatible(v, "text")    ⟺  v ∈ String
compatible(v, "number")  ⟺  v ∈ ℝ \ Bool
compatible(v, "truth")   ⟺  v ∈ {true, false}
compatible(v, "list")    ⟺  v ∈ List[Value] ∨ v ∈ Stream
compatible(v, "map")     ⟺  v ∈ Map[String → Value]
compatible(v, "any")     ⟺  true
compatible(⊥, τ)          ⟺  true   -- nothing is always compatible
```

---

## 7. Audit Trail Semantics

The audit trail is a global append-only log:

```
AuditTrail = List[AuditEntry]
AuditEntry = { id: String, operation: String, input_hash: String,
               confidence: C, model: String, timestamp: ℝ }
```

**Invariants:**
1. Every AI instruction (analyze, classify, generate, ask, embed) appends
   exactly one entry to the audit trail.
2. The input is stored as a hash (SHA-256 prefix), never plaintext — privacy by design.
3. The audit trail is monotonically growing within a session.
4. `audit_query(op, limit)` returns the most recent `limit` entries for operation `op`.

---

## 8. Semantics of nothing (⊥)

`⊥` (nothing) is distinct from all other values. Operations that "fail safely":

| Operation | Condition | Returns |
|---|---|---|
| `divide(a, b)` | `b = 0` | `⊥` |
| `list[i]` | `i ≥ len(list) ∨ i < 0` | `⊥` |
| `map[k]` | `k ∉ dom(map)` | `⊥` |
| `number("x")` | `x` is not numeric | `⊥` |
| `sqrt(x)` | `x < 0` | `⊥` |
| `log(x)` | `x ≤ 0` | `⊥` |
| `Uncertain.when(v, t)` | `confidence < t` | fallback |

**Nothing propagation rule:** Operations on `⊥` return `⊥` silently.
The `or` operator is the canonical way to provide a fallback.

---

## 9. Generator Semantics

A generator function is a function containing `yield`:

```
⟦define f(params): ... yield v ... ⟧σ = σ[f ↦ GeneratorFunction(params, body, σ)]

apply(GeneratorFunction, args, σ')
  = Stream(coroutine executing body, emitting values at each yield)
```

**Laziness:** The body does not execute until the stream is consumed.
**Termination:** When the body returns (or falls off the end), the stream ends.
**Infinite generators:** Legal. `stream_take` is required to bound them.

---

## 10. Conformance Requirements

A conforming Ledge implementation MUST:

1. Implement all types in §2 with the exact truthiness rules in §4.4
2. Return `⊥` (never crash) for all operations in §8
3. Enforce `true ≠ 1` and `false ≠ 0` in equality
4. Record every AI instruction in the audit trail
5. Return `Uncertain` from all AI instructions
6. Support lazy stream semantics (infinite generators must not hang)
7. Support re-iteration of list-based streams
8. Enforce contracts at runtime (preconditions before, postconditions after)
9. Execute `parallel` concurrently (not sequentially)
10. Reject `yield` outside a function body with `LedgeError`
11. Reject `break` and `continue` outside loops with `LedgeError`
12. Pass all 284 conformance tests in `tests/conformance.py`

A conforming implementation MUST NOT:
- Raise unhandled exceptions for any valid Ledge program
- Allow `true = 1` or `false = 0`
- Allow `nothing = false` or `nothing = 0`
- Execute more stream elements than consumed
- Evaluate both branches of a short-circuit `and`/`or`
