# Ledge Type System — Formal Specification
## Version 1.1.0

---

## 1. Type Universe

```
T ::= number | text | truth | nothing | list | map | any
    | Uncertain[T]                   -- AI result with confidence
    | function(T₁,...,Tₙ) → T       -- callable
    | python_module                  -- FFI module
```

## 2. Typing Judgment

We write `Γ ⊢ e : T` to mean "in environment Γ, expression e has type T".

Environment Γ maps variable names to types: `Γ = {x₁:T₁, ..., xₙ:Tₙ}`

---

## 3. Type Inference Rules

### Literals

```
─────────────────── [NUM]      ─────────────────── [TEXT]
Γ ⊢ n : number                 Γ ⊢ s : text

─────────────────── [BOOL]     ─────────────────── [NOTHING]
Γ ⊢ true/false : truth         Γ ⊢ nothing : nothing
```

### Variables

```
x : T ∈ Γ
─────────── [VAR]
Γ ⊢ x : T
```

### Define (variable binding)

```
Γ ⊢ e : T    (T compatible with annotation τ if present)
────────────────────────────────────────────────────────── [DEF]
Γ, x:T ⊢ define x as e
```

Compatibility rules:
- `T compatible with any` — always true
- `T compatible with T` — same type
- `Uncertain[T] compatible with Uncertain[any]` — true
- `T compatible with Uncertain[T]` — FALSE (this is an ERROR)

### Arithmetic

```
Γ ⊢ e₁ : number    Γ ⊢ e₂ : number
──────────────────────────────────── [ARITH]
Γ ⊢ e₁ ⊕ e₂ : number   (⊕ ∈ {+,-,*,/})

Γ ⊢ e₁ : text    Γ ⊢ e₂ : any
──────────────────────────────── [CONCAT]
Γ ⊢ e₁ + e₂ : text
```

### Uncertain operations — THE CRITICAL RULES

```
─────────────────────────────────────────── [ANALYZE]
Γ ⊢ analyze(e) using mode : Uncertain[map]

─────────────────────────────────────────────────── [CLASSIFY]
Γ ⊢ classify(e) using labels : Uncertain[text]

────────────────────────────────────────────── [GENERATE]
Γ ⊢ generate(e) using mode : Uncertain[text]

──────────────────────────────── [ASK]
Γ ⊢ ask(e) : Uncertain[text]

──────────────────────────────── [EMBED]
Γ ⊢ embed(e) : Uncertain[list]
```

### Uncertain elimination (safe extraction rules)

```
Γ ⊢ r : Uncertain[T]
────────────────────────────── [WHEN]
Γ ⊢ when(r, θ, fallback) : T    (θ : number, fallback : T)

Γ ⊢ r : Uncertain[T]
─────────────────────── [VALUE_OF]
Γ ⊢ value_of(r) : T

Γ ⊢ r : Uncertain[T]
──────────────────────────── [CONFIDENCE_OF]
Γ ⊢ confidence_of(r) : number

Γ ⊢ r : Uncertain[T]
──────────────────────────── [IS_CONFIDENT]
Γ ⊢ is_confident(r) : truth
```

### Flow narrowing (the key safety rule)

```
Γ ⊢ r : Uncertain[T]
Γ, r:T ⊢ body : S      (r is narrowed to T inside the guarded block)
────────────────────────────────────────────────────────────────────── [NARROW-CONFIDENT]
Γ ⊢ if is_confident(r): body : S

Γ ⊢ r : Uncertain[T]    Γ ⊢ θ : number
Γ, r:T ⊢ body : S
────────────────────────────────────────────────────────────────────── [NARROW-THRESHOLD]
Γ ⊢ if confidence_of(r) >= θ: body : S
```

### The prohibition rule (makes Ledge unique)

```
Γ ⊢ r : Uncertain[T]    f not in {when, value_of, confidence_of, is_confident, is_uncertain, type}
──────────────────────────────────────────────────────────────────────────────────────────────────── [UNSAFE-USE — ERROR]
Γ ⊢ f(r) : ⊥   (type error: must extract from Uncertain before passing to f)
```

---

## 4. Subtyping

```
T <: any       (any is the top type)
nothing <: T   (nothing is the bottom type)
Uncertain[T] ≮: T   (critical: no implicit coercion)
```

---

## 5. Soundness Property (Partial)

**Theorem (Informal):** If Γ ⊢ e : T and T ≠ Uncertain[_], then evaluating e
will not produce an Uncertain value that was not explicitly extracted.

**Status:** Heuristic enforcement — the typechecker implements these rules
as checks, not a full formal proof. Gaps exist for:
- Higher-order functions passing Uncertain through function arguments
- Collections containing Uncertain values
- Dynamic dispatch via `any` type

**Evidence of correctness:** 615 tests, 0 false positives in 50-program benchmark.

---

## 6. Confidence Semantics

Without a backend, confidence is **always exactly 0.0** — not 0.5, not 1.0.
This is an invariant enforced by the runtime, not just a convention:

```
∀ AI instruction without backend: confidence = 0.0 ∧ value = nothing
```

With a backend:
```
confidence ∈ [0.0, 1.0]   (clamped — cannot be fabricated > 1.0)
```
