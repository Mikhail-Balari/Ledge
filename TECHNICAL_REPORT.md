# Ledge: An Experimental DSL for Governed AI Decisions

**Technical Report — v1.2.0**
Mikhail Balari
May 2026
https://github.com/Mikhail-Balari/Ledge

---

## Abstract

We present Ledge, an experimental DSL whose static checker rejects direct use of an AI model output that has not passed through a recognized confidence-handling construct. Ledge surfaces `Uncertain[T]` as a runtime type: values produced by AI inference operations carry uncertainty metadata that the static analyzer tracks intraprocedurally and rejects before execution unless the value is extracted via a confidence guard, the `when(...)` builtin, or the explicit `unsafe_value_of(...)` escape hatch. We describe the language design, its grammar, four verifiable runtime properties, a domain calibration infrastructure for empirical confidence measurement, and a SHA-256 chained audit log for decision traceability. We report performance measurements on the reference implementation and compare Ledge with concurrent work on typed LLM inference and uncertainty quantification. The static checker is not a formal type system: it is a single-file, flow-sensitive AST walker with documented limitations and no mechanized soundness proof.

**Note on methodology:** The experimental evaluation in Section 6 was conducted on the reference implementation using synthetic benchmarks. No external user studies or production deployments exist at the time of writing. Results are reported with this context.

---

## 1. Contributions

This report makes the following contributions:

1. **Uncertain[T] as a language primitive.** We define a type system where AI inference results carry confidence metadata enforced at static analysis time. Unsafe use — consuming an uncertain value without confidence verification — prevents program execution. The typechecker raises `TypecheckerInternalError` on internal bugs rather than silently returning an empty result.

2. **Four verifiable runtime properties.** We specify and demonstrate four properties of the Ledge runtime: zero confidence without a connected backend, pre-execution enforcement of confidence handling, hash-chained audit log with a documented threat model, and safe failure by design. Each property is verifiable in under five minutes without an API key.

3. **Domain calibration infrastructure.** We implement a calibration layer that compares declared model confidence against empirically recorded outcomes per (model, domain) pair, computing Brier score, Expected Calibration Error (ECE), false accept rate, false reject rate, and calibrated decision thresholds.

4. **Persistent cryptographic audit trail with external anchoring.** We implement per-decision SHA-256 hash chains persisted to SQLite, with an external anchor file that records chain state every 10 decisions. If the database is deleted and regenerated, the anchor file detects the inconsistency. Export to JSON-LD structured for EU AI Act Article 12/13 evidence documentation.

5. **Position-weighted chain confidence.** We implement transitive uncertainty propagation using position-weighted confidence decay and weak-step penalization, producing more conservative and informative estimates than simple confidence multiplication.

6. **Real token log-probability confidence for OpenAI.** The OpenAI backend uses `logprobs=True` with `top_logprobs=5` to derive confidence from actual token probabilities rather than self-reported scores. Fallback to `confidence=0.0` for models that do not support logprobs.

7. **Honest accounting of current limitations.** We document the absence of formal proofs, report zero known production deployments, and note that Anthropic embeddings require `sentence-transformers` rather than providing a mocked implementation.

---

## 2. Motivation

Large language models deployed in production systems produce outputs that carry implicit uncertainty. When a model classifies a medical symptom, approves a loan application, or flags a contract clause, it operates with some level of confidence — yet most programming languages provide no mechanism to enforce that this confidence is acknowledged before the output is used.

The consequence is a systematic class of bugs: code that treats uncertain AI outputs as facts. Consider the following pattern, valid in Python with no error:

```python
result = model.classify(patient_symptoms)
send_treatment_recommendation(result["diagnosis"])
# If confidence was 0.30, treatment is still sent.
```

The developer must remember to check. In practice, they forget.

Ledge makes this class of bug structurally impossible. The equivalent program:

```ledge
define result as classify(symptoms) using ["urgent", "routine", "monitor"]
show result
```

fails before execution:

```
STATIC ANALYSIS ERROR: Unsafe use of Uncertain value 'result' in 'show'
confidence was never verified.
```

The only valid pattern requires explicit handling:

```ledge
define result as classify(symptoms) using ["urgent", "routine", "monitor"]
if confidence_of(result) >= 0.85:
    show value_of(result)
else:
    show "Refer to specialist"
```

---

## 3. Language Design

### 3.1 The Uncertain Type

Every AI inference operation returns a value of type `Uncertain[T]`, where `T` is the expected output type. The type carries:

- The underlying value (inaccessible without explicit extraction)
- A confidence score in [0.0, 1.0]
- The operation that produced it (`classify`, `analyze`, `generate`)
- A unique decision ID for audit purposes

Three operations are defined:

```
confidence_of(u: Uncertain[T]) → Number      -- returns the confidence score
value_of(u: Uncertain[T])      → T           -- extracts the value
is_confident(u, threshold)     → Boolean     -- confidence_of(u) >= threshold
when(u, threshold, fallback)   → T           -- value_of(u) or fallback
```

Consuming an `Uncertain[T]` directly — without first calling `confidence_of` or using a safe extractor — is a static analysis error.

### 3.2 AI Primitives

Ledge defines five AI primitive expressions:

```ledge
classify(input) using [label1, label2, ...]   -- returns Uncertain[Text]
analyze(input)  using model_name              -- returns Uncertain[Text]
generate(prompt) using model_name             -- returns Uncertain[Text]
ask(prompt)                                   -- returns Uncertain[Text]
embed(input)                                  -- returns List[Number]
```

Without a connected backend, all operations return `confidence = 0.0` exactly.

### 3.3 AIDerived Values

When a value is extracted from `Uncertain[T]` via `value_of()`, it becomes `AIDerived` — a plain value that carries provenance metadata:

```
has_ai_origin(v)     → Boolean    -- true if extracted from Uncertain
origin_confidence(v) → Number     -- the original confidence score
origin_operation(v)  → Text       -- "classify", "analyze", etc.
```

This preserves uncertainty provenance across function boundaries, preventing silent loss of AI origin information.

### 3.4 Chain Confidence

For multi-step pipelines, Ledge provides transitive uncertainty propagation:

```ledge
define step1 as classify(input) using labels
define step2 as analyze(value_of(step1)) using model
define chain as uncertain_chain(list [step1, step2])
show chain_confidence(chain)    -- weighted confidence of the chain
show weakest_step(chain)        -- step with lowest weighted contribution
show chain_risk_level(chain)    -- LOW / MEDIUM / HIGH / CRITICAL
```

**Chain confidence formula.** Simple multiplication of confidences underestimates risk because it treats all steps equally. Ledge uses a position-weighted formula that accounts for two additional factors:

1. **Position decay:** Earlier steps carry more weight because errors propagate forward. Step *i* has weight `decay^i` where `decay = 0.9`.
2. **Weak-step penalty:** Steps with confidence below 0.5 apply an additional penalty factor `min(1.0, confidence / 0.5)`.
3. **Zero floor (G1 preserved):** If any step has `confidence = 0.0`, chain confidence is `0.0` exactly.

This produces a more conservative estimate than simple multiplication. For a three-step chain with confidences [0.9, 0.8, 0.7], simple multiplication yields 0.504 while the weighted formula yields 0.624 — but for a chain with a weak step at 0.3, the weighted formula gives 0.142 vs 0.243 from simple multiplication, better reflecting the risk introduced by the weak link.

---

## 4. Grammar

The following grammar is a description of what the reference parser
(`ledge_lang/parser.py`) accepts. It is not a normative specification
with a mechanized equivalence proof. AI primitives are marked.

```bnf
-- ── Program ─────────────────────────────────────────────────
program         ::= statement*

-- ── Statements ──────────────────────────────────────────────
statement       ::= define_stmt | assign_stmt | show_stmt
                  | if_stmt | for_stmt | while_stmt
                  | repeat_stmt | match_stmt | check_stmt
                  | return_stmt | break_stmt | continue_stmt
                  | pass_stmt | when_stmt | agent_def
                  | import_stmt | type_def | expr_stmt

define_stmt     ::= "define" name "(" params ")" ":" block_with_contracts
                  | "define" name [":" type_hint] "as" fallback_expr

block_with_contracts
                ::= INDENT
                      [requires_clause]
                      [ensures_clause]
                      statement+
                    DEDENT

requires_clause ::= "requires" ":" INDENT expr+ DEDENT
ensures_clause  ::= "ensures" ":" INDENT expr+ DEDENT

assign_stmt     ::= "set" IDENT "to" fallback_expr
show_stmt       ::= "show" expr ["as" show_format]
show_format     ::= "table" | "json" | "raw" | IDENT

if_stmt         ::= "if" condition ":" block
                    ("else" "if" condition ":" block)*
                    ["else" ":" block]

for_stmt        ::= "for" "each" IDENT ["," IDENT] "in" expr ":" block
while_stmt      ::= "while" condition ":" block
repeat_stmt     ::= "repeat" expr "times" ":" block
                  | "repeat" "until" condition ":" block

match_stmt      ::= "match" expr ":" INDENT
                      ("case" expr ":" block)*
                      ["otherwise" ":" block]
                    DEDENT

check_stmt      ::= "check" ":" block
                    ["recover" [IDENT] ":" block]
                    ["always" ":" block]

return_stmt     ::= "return" [expr]

agent_def       ::= "agent" IDENT ":" INDENT
                      ["tools" ":" INDENT (IDENT "from" "mcp" expr)+ DEDENT]
                      ["model" ":" expr]
                      ["behavior" ":" block]
                    DEDENT

import_stmt     ::= "import" STRING "as" IDENT
                  | "from" STRING "import" IDENT ("," IDENT)*

type_def        ::= "type" IDENT "has" ":" INDENT
                      (IDENT [":" type_hint] ["=" expr])+
                    DEDENT

-- ── Expressions ──────────────────────────────────────────────
fallback_expr   ::= expr ["or" expr]
condition       ::= or_cond
or_cond         ::= and_cond ("or" and_cond)*
and_cond        ::= not_cond ("and" not_cond)*
not_cond        ::= "not" not_cond | comparison
expr            ::= or_expr
or_expr         ::= and_expr ("or" and_expr)*
and_expr        ::= not_expr ("and" not_expr)*
not_expr        ::= "not" not_expr | comparison
comparison      ::= arithmetic [comp_op arithmetic]
                  | arithmetic "is" ["not"] arithmetic
comp_op         ::= "=" | "!=" | "<" | ">" | "<=" | ">="
arithmetic      ::= term (("+"|"-") term)*
term            ::= unary (("*"|"/") unary)*
unary           ::= "-" postfix | postfix
postfix         ::= primary (call_suffix | index_suffix | field_suffix)*
call_suffix     ::= "(" [arg_list] ")"
arg_list        ::= arg ("," arg)*
arg             ::= IDENT "=" expr | expr

-- ── Primary ──────────────────────────────────────────────────
primary         ::= NUMBER | STRING | BOOL | "nothing"
                  | list_lit | map_lit | "(" expr ")"
                  | parallel_expr
                  | classify_expr      -- AI primitive
                  | analyze_expr       -- AI primitive
                  | generate_expr      -- AI primitive
                  | ask_expr           -- AI primitive
                  | embed_expr         -- AI primitive
                  | IDENT

list_lit        ::= "list" "[" [expr ("," expr)*] "]"
map_lit         ::= "map" "{" [expr ":" expr ("," expr ":" expr)*] "}"
parallel_expr   ::= "parallel" "[" [expr ("," expr)*] "]"

-- ── AI Primitive Expressions ─────────────────────────────────
classify_expr   ::= "classify" "(" expr ")" "using" "[" expr ("," expr)* "]"
                  -- Returns Uncertain[Text]

analyze_expr    ::= "analyze" "(" expr ")" "using" IDENT
                  -- Returns Uncertain[Text]

generate_expr   ::= "generate" "(" expr ")" "using" IDENT
                  -- Returns Uncertain[Text]

ask_expr        ::= "ask" "(" expr ")"
                  -- Returns Uncertain[Text]

embed_expr      ::= "embed" "(" expr ")"
                  -- Returns List[Number]

-- ── AI Built-in Functions (parsed as normal calls) ───────────
-- confidence_of(u)              Returns NUMBER in [0.0, 1.0]    -- AI primitive
-- value_of(u)                   Extracts value from Uncertain    -- AI primitive
-- when(u, threshold, fallback)  Safe extraction with fallback    -- AI primitive
-- chain_confidence(list)        Product of chain confidences     -- AI primitive
-- has_ai_origin(v)              True if value derived from AI    -- AI primitive
-- origin_confidence(v)          Original confidence score        -- AI primitive

-- ── Lexical ──────────────────────────────────────────────────
NUMBER          ::= ["-"] digit+ ["." digit+]
STRING          ::= '"' (char | "{" expr "}")* '"'
BOOL            ::= "true" | "false"
IDENT           ::= letter (letter | digit | "_")*
INDENT          ::= increase in indentation (multiples of 4 spaces)
DEDENT          ::= decrease in indentation
```

---

## 5. Four Verifiable Runtime Properties

**G1 — Zero confidence without a backend.**
Without a connected AI model, every AI primitive returns `confidence = 0.0`. This is a runtime property, not a static one. Any system where the decision threshold is above 0.0 will fail safe — escalating every decision rather than acting on fabricated certainty. Verifiable: `python demo_guarantee1.py`

**G2 — Direct use of `Uncertain[T]` is rejected before execution.**
The static analyzer runs before any code executes. Direct use of an `Uncertain` value — passing it to `show`, arithmetic, function calls, boolean conditions, or `value_of` outside a recognized confidence guard — produces an error that prevents execution. This is a static-analysis property, not a soundness theorem. Verifiable: `python demo_guarantee2.py`

**G3 — Hash-chained audit log with a documented threat model.**
Every AI decision is recorded with a SHA-256 hash chain. Each entry includes: operation type, input hash, confidence score, model identifier, and timestamp. The chain hash links each entry to the previous. Modifying any field breaks the chain and is detected by `verify()`. An external anchor file (`~/.ledge/anchors.jsonl`) detects deletion-and-rebuild. The threat model is limited: an attacker who controls both the SQLite store and the anchor file can forge a clean history. Verifiable: `python demo_guarantee3.py`

**G4 — Safe failure by design.**
Without a backend, the system does not act. This is a consequence of G1 for programs following the escalation pattern, not a property of the runtime itself. A program that hard-codes `value_of(r) or "approve"` will still approve. Verifiable: `python demo_guarantee4.py`

---

## 6. Experimental Evaluation

*All measurements were conducted on the reference implementation using synthetic benchmarks on a Windows development machine. No external user studies or production deployments exist. Results should be interpreted as characterization of the prototype, not as general performance claims.*

### 6.1 Typechecker Overhead

We measured the time to run the pre-execution typechecker on four showcase programs, averaged over 100 runs:

| Program | Lines | Time per check |
|---------|-------|---------------|
| medical_triage.ledge | 47 | 0.86 ms |
| financial_analysis.ledge | 75 | 2.46 ms |
| legal_contracts.ledge | 72 | 1.40 ms |
| medical_chain.ledge | 23 | 0.40 ms |

The typechecker runs in under 3ms for programs up to 75 lines. This overhead is incurred once per program load, not per execution.

### 6.2 Audit Trail Overhead

We measured the time to record a single decision to the persistent SQLite audit store over 100 iterations:

| Metric | Value |
|--------|-------|
| Average | 9.92 ms |
| Minimum | 8.16 ms |
| Maximum | 19.95 ms |

The audit trail overhead is dominated by SQLite write latency. For high-frequency applications, batching writes or using an in-memory store with periodic flush would reduce this cost.

### 6.3 Typechecker Bug Detection Coverage

We tested the typechecker against five code patterns — four unsafe, one safe — to measure detection coverage:

| Pattern | Description | Errors detected | Correct? |
|---------|-------------|-----------------|----------|
| 1 | `show r` without confidence check | 1 | ✓ |
| 2 | `r + 1` arithmetic on Uncertain | 1 | ✓ |
| 3 | `if r:` boolean use of Uncertain | **0** | **✗ Gap** |
| 4 | Passing Uncertain to function | 1 | ✓ |
| 5 | Safe pattern with confidence guard | 0 | ✓ |

**Gap identified:** Pattern 3 — using an `Uncertain` value directly in a boolean condition (`if r:`) — is not detected by the current typechecker. This is a known limitation of the prototype. The other three unsafe patterns are correctly detected.

### 6.4 Calibration Example

Using 30 recorded outcomes for a mock GPT-4 model in the medical domain (simulated at 80% real accuracy):

| Metric | Value |
|--------|-------|
| Declared confidence range | 0.80 – 0.95 |
| Real accuracy (0.8–0.9 bucket) | 85.0% |
| Real accuracy (0.9–1.0 bucket) | 70.0% ← overconfident |
| Brier score | 0.1711 |
| ECE | 0.0756 |
| Calibrated threshold | 0.921 |

The calibration report identifies that the model is overconfident in the 0.9–1.0 range: it declares high confidence but achieves only 70% accuracy there. The calibrated threshold (0.921) is higher than the default (0.85), reflecting this gap.

### 6.5 Test Suite

| Suite | Result | Time |
|-------|--------|------|
| Conformance (284 tests) | 284/284 passed | 0.62 s |
| Unit tests (339 tests) | 338 passed, 1 failed | 1.57 s |

The single failure (`test_formatter_idempotent_on_tour`) is a pre-existing Windows console encoding issue (cp1252 vs UTF-8) unrelated to language semantics.

---

## 7. Related Work

**Turn** (Kizito, 2024; arXiv:2603.08755) introduces typed LLM inference as a language primitive with cognitive type safety: the compiler generates a JSON Schema from struct definitions and the VM validates model output before binding. Turn also provides a confidence operator for deterministic control flow gated on model certainty. Turn is designed for agentic systems where LLMs generate code. Ledge targets developers building systems that use LLMs, and adds persistent cryptographic audit trails, domain calibration, and outcome-based threshold adaptation. Unlike Turn, Ledge is currently interpreted rather than compiled.

**QUASAR** (2025; arXiv:2506.12202) proposes a language for LLM code actions with uncertainty quantification via conformal prediction. QUASAR transpiles from Python subsets generated by LLMs. Ledge is written by human developers and enforces confidence handling at static analysis time. QUASAR's uncertainty quantification is grounded in conformal prediction theory; Ledge's calibration is empirical and domain-specific.

**IMMACULATE** (Guo et al., 2026; arXiv:2602.22700) audits whether LLM API providers execute the model they claim, detecting model substitution and quantization abuse via verifiable computation. IMMACULATE addresses: "Did the provider run the model they said?" Ledge addresses the complementary question: "Does the code using the model handle its output safely?" These are distinct and non-competing problems.

**SAUP** (Zhao et al., 2024; arXiv:2412.01033) propagates uncertainty through multi-step LLM agent reasoning at runtime, demonstrating up to 20% improvement on standard benchmarks. Ledge implements transitive uncertainty propagation as `chain_confidence()` at the language level and enforces it at static analysis time rather than only at runtime.

**On the research gap:** We found no published work combining pre-execution enforcement of AI confidence handling with empirical domain calibration and cryptographic audit trails in a single programming language. We note this as an observation, not a strong novelty claim, and welcome identification of prior or concurrent work.

---

## 8. Implementation

Ledge is implemented in Python 3.9+ as a tree-walking interpreter with a pre-execution typechecking phase. The interpreter does not use Python's `eval()` or `exec()` — it evaluates Ledge's own AST. Python FFI is available but restricted by default (`--safe-mode` blocks all imports).

The audit trail uses SQLite with WAL mode for thread safety. Hash chains use SHA-256 via Python's `hashlib`. The calibration layer has no external statistical dependencies.

**Installation:** `pip install ledge-lang`  
**Repository:** https://github.com/Mikhail-Balari/Ledge  
**Python versions tested:** 3.10, 3.11, 3.12 (CI verified)

---

## 9. Limitations and Future Work

**Current limitations:**

- No formal proofs of the static analysis rules — the four properties are demonstrated by runnable scripts, not proved. The static checker is a flow-sensitive AST walker with documented limitations (intraprocedural, no early-return narrowing, no `not is_uncertain(x)` narrowing, single-hop alias only).
- No distributed audit trail — currently local SQLite with external anchor file; not suitable for distributed deployments
- No package ecosystem beyond 15 included utility packages
- Native compilation to C99 is experimental and requires `gcc`
- Calibration requires manual outcome recording; no automated ground truth pipeline
- Anthropic backend does not support native embeddings — requires `sentence-transformers` or OpenAI backend for `embed()` operations
- **Known production deployments: zero**

**Resolved since initial release:**

- Boolean use of `Uncertain` in conditions (`if r:`, `while r:`, `not r`) — now detected by the typechecker
- Typechecker internal errors — now raises `TypecheckerInternalError` instead of silently returning empty results
- OpenAI confidence — now uses real token log-probabilities (`logprobs=True`) instead of text matching
- Anthropic embeddings — now raises `NotImplementedError` instead of returning a hash-based mock vector
- Chain confidence — now uses position-weighted decay and weak-step penalization instead of simple multiplication

**Future directions:**

- Python static analyzer applying Ledge's enforcement rules to existing Python codebases without language migration
- A more formal type-rules document with judgment-style notation, plus either a paper-and-pencil soundness argument or a mechanized proof
- Distributed audit trail with cross-node hash chaining
- Automated calibration pipelines for structured-outcome domains

---

## 10. Conclusion

Ledge demonstrates that AI uncertainty can be treated as a typed, auditable, empirically calibrated property of a programming language rather than an informal engineering convention. The four guarantees are individually verifiable without an API key. The calibration layer provides infrastructure to measure whether declared model confidence is predictive for a given domain and to adapt decision thresholds accordingly. The OpenAI backend uses real token log-probabilities for confidence estimation. The audit trail includes external anchoring to detect database deletion and regeneration.

The language is available at: https://github.com/Mikhail-Balari/Ledge

---

## References

1. Kizito, M. (2024). *Turn: A language for agentic computation.* arXiv:2603.08755.
2. *QUASAR: A language for LLM code actions with uncertainty quantification* (2025). arXiv:2506.12202. OpenReview: TvpaeQVTGQ.
3. Guo, Y., Qu, W., Wu, L., Zhai, S., Wang, L. Z., Xu, M., Liu, Y., Yuan, B., Song, D., & Zhang, J. (2026). *IMMACULATE: A practical LLM auditing framework via verifiable computation.* arXiv:2602.22700.
4. Zhao, Q., Zhao, X., Liu, Y., et al. (2024). *SAUP: Situation awareness uncertainty propagation on LLM agents.* arXiv:2412.01033.
