# Ledge Type System — Static Analysis Rules
## Version 1.2.0

> This document describes the rules the static checker implements. It is
> not a formal type-system specification — there is no mechanized proof
> and no judgment-style soundness theorem. The "Theorem (Informal)"
> further down is a paragraph claim, not a formal result.

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

### The prohibition rule (the central check)

Note: the checker rejects bare `value_of` outside a recognized guard.
`unsafe_value_of` is the explicit escape hatch — see README.

```
Γ ⊢ r : Uncertain[T]    f not in {when, unsafe_value_of, confidence_of, is_confident, is_uncertain, type}
──────────────────────────────────────────────────────────────────────────────────────────────────── [UNSAFE-USE — ERROR]
Γ ⊢ f(r) : ⊥   (analysis error: must extract from Uncertain before passing to f)
```

---

## 4. Subtyping

```
T <: any       (any is the top type)
nothing <: T   (nothing is the bottom type)
Uncertain[T] ≮: T   (critical: no implicit coercion)
```

---

## 5. Intended static-analysis property (informal)

**Informal claim:** If the checker assigns Γ ⊢ e : T with T ≠ Uncertain[_]
and reports no errors, the program does not use an Uncertain value at e
without going through one of the extraction constructs above.

**Status:** This is a description of what the checker tries to enforce,
not a theorem. There is no mechanized proof, and known gaps include:
- Higher-order functions passing Uncertain through function arguments
- Collections containing Uncertain values (only `list[uncertain[T]]` from
  literal-lambda `map` is recognized)
- Dynamic dispatch via `any` type
- Early-return guards (`if confidence_of(x) < t: return; ...`)
- Inverted operators (`0.85 <= confidence_of(x)`)
- `not is_uncertain(x)` is not recognized

The runtime escape hatch is `unsafe_value_of(x)`; the deliberately ugly
name signals to readers that confidence was not checked.

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
