# Ledge

[![PyPI version](https://img.shields.io/pypi/v/ledge-lang.svg)](https://pypi.org/project/ledge-lang/)
[![CI](https://github.com/Mikhail-Balari/Ledge/actions/workflows/ci.yml/badge.svg)](https://github.com/Mikhail-Balari/Ledge/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
![Status: alpha / experimental](https://img.shields.io/badge/status-alpha%20%2F%20experimental-orange)

**Ledge is an experimental runtime and DSL for auditable AI decision boundaries.**

It does not prove that a model is correct. It helps make unchecked AI
uncertainty visible, enforceable, and auditable before it becomes action. Ledge
surrounds AI calls with a static analysis pass that rejects direct use of
results whose confidence has not been checked, records AI decisions in a
hash-chained audit log, compares declared confidence against real outcomes
over time, and can attach structured confidence evidence before an AI output
crosses into a business action. Ledge 1.7.0 Alpha adds a tamper-evident
decision ledger for semantic AI decision-boundary events: local
append-oriented records plus verification, export, and AI-readable review
packs for inspecting how uncertain AI outputs became, or were prevented from
becoming, system actions.

Ledge is alpha software. It is not an AI model, not a formal proof system, not
a compliance product, and not a replacement for evaluation, monitoring, or
human review. Use normal Python and your normal stack for everything else; use
Ledge around the boundary where AI output may become a decision or action. See
[Limitations and non-goals](#limitations-and-non-goals).

---

## The one-paragraph contract

Ledge does not prove that AI outputs are correct. Confidence is not correctness.
What Ledge does is statically reject direct use of a value typed as `Uncertain[T]`
unless it passes through one of the language's recognized handling constructs:
a confidence guard (`if confidence_of(x) >= t:` or `if is_confident(x):`), a
runtime-checked extraction (`when(x, t, fallback)`), or the explicit
`unsafe_value_of(x)` escape hatch. The static checker is a single-file,
flow-sensitive AST walker with documented limitations (intraprocedural,
conservative on inverted/early-return guards, no alias analysis beyond the
single `define c as confidence_of(x)` pattern). The runtime records every AI
call in a SHA-256 chained audit log, anchored to an external file so the
deletion-and-rebuild attack is detectable. None of this proves anything about
the model; it just makes "I forgot to check" turn into a static error.

---

## What this is not

- **Not a formal proof system.** No mechanized soundness theorem. The static
  checker is an AST walker with the limitations listed below.
- **Not a calibrated uncertainty framework.** Backend confidence scores
  (OpenAI logprobs, Anthropic structured self-assessment) are signals, not
  calibrated probabilities of correctness. Calibration must be measured.
- **Not a replacement for evals, monitoring, or human review.**
- **Not a legal compliance product.** The regulatory export is intended to
  support structured evidence review, but it does not establish compliance.
  Whether it is useful for any specific regime is between you and your lawyer.
- **Not tamper-proof, audit-proof, immutable storage, or blockchain.** The
  decision ledger is local append-oriented records plus verification; it is not
  secure storage by itself.
- **Not a security boundary against a malicious local operator.** The audit
  trail detects post-hoc modification by an attacker with DB access but
  no anchor-file access; an attacker with both can forge a clean history.
- **Not a general-purpose replacement for Python.** Use Python for everything
  else; use Ledge only at the layer where AI decisions are made.

---

## Install and run in 2 minutes

From PyPI:

```bash
pip install ledge-lang==1.7.0
ledge demo
ledge demo medical_triage
ledge demo loan_approval
ledge pilot-dry-run loan_approval
ledge python-integration-demo
```

From a source checkout:

```bash
python scripts/run_pilot_dry_run.py pilot_templates/loan_approval
python examples/python_integration/app.py
python scripts/ledge_check_ci.py ledge_lang/demos examples/python_integration
```

Expected output (no API key, no clone, no setup):

```
=== MEDICAL TRIAGE DEMO ===
PATIENT P001: ESCALATE TO HUMAN (confidence=0)
PATIENT P002: ESCALATE TO HUMAN (confidence=0)
PATIENT P003: ESCALATE TO HUMAN (confidence=0)

Decisions logged in audit trail: 3
Cryptographic chain intact: true
```

Without a real AI backend connected, every patient escalates to human review --
that is the safe-failure default. Connect a real backend and it will classify
using backend-provided confidence estimates.

To see what the bundled demo looks like in source form:

```bash
python -c "from ledge_lang import demos; print(open(demos.demo_path('medical_triage')).read())"
```

To run the clearest safety-oriented showcase examples you currently need to
clone the repository:

```bash
git clone https://github.com/Mikhail-Balari/Ledge
cd Ledge
ledge run examples/showcase/loan_approval.ledge
ledge run examples/showcase/medical_triage.ledge
```

`examples/showcase/financial_analysis.ledge` is a mixed deterministic-plus-AI
example: debt-ratio rules may produce preliminary rule-based decisions even
when AI history confidence is 0, and the output labels that distinction.

The bundled `loan_approval` demo is synthetic. It is not a credit model and not
a lending decision system. It demonstrates deterministic rule checks,
confidence-gated AI use, human review fallback, and audit-chain verification.

`ledge run` runs the static Uncertain checker before execution. If you are
deliberately experimenting with unchecked extraction, use
`ledge run program.ledge --unsafe` to bypass the checker.

Python API note: `from ledge_lang import checked_run` is the safety-gated
programmatic execution helper. It runs the same static checker before execution
and raises `LedgeError` without executing the program if type issues are found.
`from ledge_lang import run` remains the low-level direct execution API for
interpreter and test harness use; it bypasses the static checker by design.

Python SDK Core: `from ledge_lang.sdk import Uncertain, DecisionPolicy`
provides a minimal alpha SDK surface for modeling uncertain values and decision
policies in normal Python code. This does not replace the DSL static checker.
It is API-level and runtime-level handling. Ledge 1.5.0 Alpha added
`ledge lint-python` for AST-based CI enforcement of common unsafe Python
decision-boundary patterns. Ledge 1.6.0 Alpha adds a Confidence Evidence
Engine: structured, redaction-aware, hashable evidence for confidence scores
before AI outputs cross into business actions. Ledge 1.7.0 Alpha adds a
Tamper-Evident Decision Ledger for semantic decision-boundary events,
verification, local audit review export packages, AI-readable review packs,
and SDK-facing recording helpers. It does not provide complete Python
semantic verification, complete cross-file/interprocedural dataflow analysis,
a truth guarantee, hallucination prevention, legal compliance, production
readiness, enterprise readiness, tamper-proof storage, audit-proof guarantees,
immutable storage, or blockchain.
See [`examples/sdk_decision_boundary`](examples/sdk_decision_boundary/) and
[`examples/confidence`](examples/confidence/). For the end-to-end ledger
workflow, see [`examples/ledger`](examples/ledger/).

For minimal Python integration and CI checker examples after installing the
package:

```bash
ledge python-integration-demo
ledge ci-check path/to/your/ledge/files
ledge lint-python path/to/your/python/files --config ledge.toml
```

From a source checkout, the wrappers and repository-path CI check remain
available:

```bash
python examples/python_integration/app.py
python scripts/ledge_check_ci.py ledge_lang/demos examples/python_integration
ledge ci-check ledge_lang/demos examples/python_integration
ledge lint-python examples/python_linter --config examples/python_linter/ledge.toml
```

Confidence Evidence Engine examples that use the repository fixture files also
require a source checkout where `examples/confidence/` is available:

```bash
ledge confidence-eval examples/confidence/fixture.json
ledge confidence-eval examples/confidence/fixture.json --format json
ledge calibration-report examples/confidence/outcomes.json
ledge calibration-report examples/confidence/outcomes.json --format json
```

Decision Ledger examples that use repository paths also require a source
checkout where `examples/ledger/` is available:

```bash
python examples/ledger/sdk_decision_result_to_ledger.py
ledge ledger-verify --store examples/ledger/out/support_ticket_ledger.jsonl --manifest examples/ledger/out/ledger_manifest.json
ledge ledger-export --store examples/ledger/out/support_ticket_ledger.jsonl --manifest examples/ledger/out/ledger_manifest.json --out examples/ledger/out/audit_export --force
ledge ledger-review-pack --store examples/ledger/out/support_ticket_ledger.jsonl --manifest examples/ledger/out/ledger_manifest.json --out examples/ledger/out/ai_review_pack.json --force
```

For the detailed checker contract, see [`docs/STATIC_CHECKER.md`](docs/STATIC_CHECKER.md).
For Python integration guidance, see [`docs/PYTHON_INTEGRATION.md`](docs/PYTHON_INTEGRATION.md).
For SDK-level uncertain values in normal Python, see
[`examples/sdk_decision_boundary`](examples/sdk_decision_boundary/).
For current and future uncertainty semantics, see
[`docs/UNCERTAINTY_MODEL.md`](docs/UNCERTAINTY_MODEL.md).
For confidence evidence records, signal generation, reporting, and limits, see
[`docs/CONFIDENCE_EVIDENCE_ENGINE.md`](docs/CONFIDENCE_EVIDENCE_ENGINE.md).
For the tamper-evident decision ledger, schema, verification contract, SDK
integration, and limitations, see
[`docs/DECISION_LEDGER.md`](docs/DECISION_LEDGER.md).
For deployment assumptions and non-goals, see [`docs/THREAT_MODEL.md`](docs/THREAT_MODEL.md).
For the future audit anchoring design, see
[`docs/AUDIT_ANCHORING.md`](docs/AUDIT_ANCHORING.md).
For the path from alpha software toward production-critical readiness, see
[`docs/ROADMAP.md`](docs/ROADMAP.md).
For a short technical review path, see [`EXPERT_REVIEW.md`](EXPERT_REVIEW.md).
For demo and pilot planning materials, see [`DEMO.md`](DEMO.md),
[`COMMERCIAL.md`](COMMERCIAL.md), and [`PILOT_PACK.md`](PILOT_PACK.md).
For the synthetic pilot dry run after installing the package:

```bash
ledge pilot-dry-run loan_approval
```

From a source checkout, the wrapper remains available:

```bash
python scripts/run_pilot_dry_run.py pilot_templates/loan_approval
```

---

## Where Ledge fits

Ledge belongs at the boundary where AI or model output can become a business
action: approve, reject, escalate, bill, refund, route, write, publish, or
trigger a tool/API. It is suitable today for demos, proofs of concept, and
shadow-mode pilots where the goal is to make uncertainty handling explicit and
reviewable.

Production-critical or regulated use requires additional integration, security
review, monitoring, calibration, operational testing, legal/compliance review,
and human oversight appropriate to the domain. Ledge is one control around one
decision boundary, not a complete governance system.

---

## The checker's contract, precisely

A value of type `Uncertain[T]` (returned by `analyze`, `classify`, `generate`,
`ask`, `embed`) cannot be used directly. The checker accepts these forms:

```ledge
define r as classify(symptoms) using ["urgent", "routine"]

# (1) Confidence guard -- recognized narrowing patterns:
if confidence_of(r) >= 0.85:
    show value_of(r)                         # OK inside this block

if is_confident(r):
    show value_of(r)                         # OK inside this block

# (2) Alias-aware guard (the checker remembers the alias):
define c as confidence_of(r)
if c >= 0.85:
    show value_of(r)                         # OK inside this block

# (3) Runtime-checked extraction with fallback:
show when(r, 0.85, "fallback for low-confidence")

# (4) Explicit escape hatch -- deliberately ugly name:
show unsafe_value_of(r)                      # OK anywhere; reader is warned
```

The checker rejects these:

```ledge
define r as classify(symptoms) using ["urgent", "routine"]
show r                                       # ERROR: unsafe use of Uncertain
show value_of(r)                             # ERROR: value_of outside guard
show upper(r)                                # ERROR: Uncertain in function call
define x: text as r                          # ERROR: Uncertain to typed var
```

This is the central enforcement. Everything else -- audit trail, calibration,
regulatory export -- is supporting infrastructure.

---

## Four properties you can verify in your terminal

Run these yourself. No API key. No setup. Under 5 minutes. Each demo is a
small Python script that exercises one runtime behavior; the script prints
its own pass/fail.

### G1 -- Zero confidence without a backend

```bash
python demo_guarantee1.py
```

Without a real model connected, every AI primitive returns
`confidence = 0.0`. The system cannot invent certainty. This is a runtime
property, not a static one.

### G2 -- Unsafe use is rejected before execution

```bash
python demo_guarantee2.py
```

The static analyzer rejects unsafe uses of `Uncertain[T]` (see the contract
above) before any code runs. If the checker itself crashes, it raises
`TypecheckerInternalError` with a stack trace rather than returning an
empty result list.

### G3 -- Hash-chained audit trail with external anchor

```bash
python demo_guarantee3.py
```

Every AI decision is recorded with a SHA-256 hash chain. Changing any field
(confidence, timestamp, operation) breaks the chain. An external anchor file
(`~/.ledge/anchors.jsonl`) records chain state every 10 decisions; if the
SQLite database is deleted and rebuilt, the anchors detect the discontinuity.

**Threat model.** This detects post-hoc modification by an actor who can
read/write the SQLite store but not the anchor file. An attacker who controls
both the database and the anchor file can forge a clean history. This is not
resistant to a malicious local operator who controls both files. See `GUARANTEES.md` for the
full threat model.

```bash
ledge audit --verify-anchors   # cross-check anchor file against the store
```

### G4 -- Safe failure when no backend is configured

```bash
python demo_guarantee4.py
```

A consequence of G1: without a backend, `confidence = 0.0`, so any decision
threshold `> 0.0` causes the system to escalate. It does not act on
fabricated certainty.

---

## Confidence isn't correctness

Ledge does not trust confidence scores. It records them and compares them
against real outcomes over time.

Per-backend confidence sources:

```python
# OpenAI: token log-probabilities over classification labels, taken as a
# token-probability-derived confidence estimate. Sensitive to:
#   - first-token classification (multi-token labels degrade gracefully)
#   - top-logprob truncation (low-probability labels fall off the list)
#   - prompt phrasing and label order
#   - model-specific behavior (gpt-4o-mini vs gpt-4o differ)
#   - drift over time as the provider updates the model
# These are signals. They are NOT calibrated correctness probabilities.
backend = openai_backend(api_key="sk-...", model="gpt-4o-mini")

# Anthropic: structured self-assessment -- the model returns a confidence
# score alongside its answer. This is self-reported, not derived from
# model weights or token probabilities.
backend = anthropic_backend(api_key="sk-ant-...", model="claude-3-haiku-20240307")
```

Treat both as inputs to calibration, not as ground truth. The calibration
layer (Layer 3 below) measures real accuracy per model and domain:

```bash
ledge audit --calibration gpt-4 medical
ledge audit --calibration-metrics gpt-4 medical
```

```
Calibration Report: gpt-4 / medical (n=30)
  RANGE      COUNT  MEAN_CONF  ACCURACY  CAL_ERROR
  0.8-0.9      20     0.848     0.850     0.002
  0.9-1.0      10     0.924     0.700     0.224  <- overconfident

  Brier score         : 0.1711   (lower is better; 0.0 is perfect)
  ECE                 : 0.0756   (lower is better; <0.10 is a rough heuristic)
  False accept rate   : 0.1429   (accepted when wrong)
  False reject rate   : 0.7826   (rejected when right)
  Calibrated threshold: 0.921    (provisional -- only 10 samples > 0.9)
  Well calibrated     : False    (overconfident in 0.9-1.0 range)
```

See [CALIBRATION_GUIDE.md](CALIBRATION_GUIDE.md) for minimum sample
requirements (default 30), self-reported-outcome caveats, and drift handling.

---

## How the pieces fit together

```
Uncertain output -> static check -> logged decision
     -> recorded outcome -> calibrated threshold
          -> safer future decision
```

**Multi-step chains.** Confidence degrades across reasoning steps. If each
step is 0.85 confident, five steps yield `0.85^5 = 0.44`. The
`chain_confidence()` builtin applies position-weighted decay and penalizes
weak steps; the result is one propagated confidence value for the chain,
subject to the same handling rules as any other Uncertain value.

**Layer 1 -- Pre-execution static check.**
Direct use of `Uncertain[T]` is rejected. (See *The checker's contract* above.)

**Layer 2 -- Runtime confidence provenance.**
Confidence comes from the backend you connect; without one it is exactly 0.0.
The `AIDerived` wrapper preserves AI origin through extraction so callers can
still detect it.

**Layer 3 -- Domain calibration.**
Real accuracy is measured per model and domain. The calibrated threshold is
computed from observed outcomes, not from the backend's own confidence claim.
Falls back to the default 0.85 with a warning if sample size is below
`min_samples` (default 30).

**Layer 4 -- Adaptive threshold API.**

```python
from ledge_lang.calibration import DomainCalibrator

threshold = calibrator.get_calibrated_threshold(
    'gpt-4', 'medical', desired_accuracy=0.90, min_samples=30
)
```

**Layer 5 -- Structured evidence export.**
JSON-LD output is intended to support structured evidence review for AI
logging, monitoring, and transparency work. Generating an export does not
establish legal compliance in any jurisdiction; that requires appropriate
review by qualified counsel.

```bash
ledge audit --export-regulatory report.json
ledge audit --validate-regulatory report.json
```

---

## Why a DSL plus SDK instead of only a Python library, mypy plugin, Pyright plugin, linter, or framework?

The plain version, without inflated claims.

**A plain Python library** can help teams model uncertainty, apply policies,
and make decision handling explicit. That is why Ledge now includes a Python
SDK Core. But a library alone cannot prevent a developer from forgetting to
use it, bypassing it, or directly passing an uncertain value into an action
path.

**The Ledge DSL** exists for the stricter case: a smaller controlled surface
where unsafe extraction can become a static error before runtime.

**A mypy or Pyright plugin** could cover part of this problem inside normal
Python, especially around `Uncertain[T]`. That path is valuable, but it still
depends on plugin installation, project configuration, and the limits of
expressing confidence-guarded extraction through Python's type system.

**A linter** can catch obvious unsafe patterns in Python code. Ledge includes
`ledge lint-python` for AST-based CI enforcement of common unsafe SDK
decision-boundary patterns. The limitation is that linters work mostly through
syntax and conventions, so cross-file flows, interprocedural flows, aliasing, and
framework-specific behavior need careful handling.

**A framework or SDK** can require specific classes and method signatures.
This works well when a team consistently adopts the SDK or framework. Ledge's
SDK follows this path for adoption and integration, while the DSL remains the
stricter boundary layer.

**What Ledge actually buys you is the combination.** A DSL for the most
controlled decision-boundary layer, a Python SDK for normal application
integration, AST-based CI enforcement for common Python unsafe-use patterns,
and a roadmap toward richer evidence capture. The trade-off is honest: the DSL
is a new surface with no broad ecosystem yet, while the SDK and linter are
easier to adopt but cannot provide complete semantic verification by
themselves.

### Related work and adjacent tools

These projects are related and useful; Ledge does not replace them.

- [Model Context Protocol](https://modelcontextprotocol.io/) standardizes how
  AI applications expose and consume tools, resources, and context. Ledge is
  focused on the program boundary after an AI result enters the decision flow.
- [Guardrails AI](https://guardrailsai.com/docs) and
  [NVIDIA NeMo Guardrails](https://docs.nvidia.com/nemo/guardrails/latest/)
  provide guardrail frameworks for validating or constraining model behavior.
  Ledge's narrower experiment is to make uncertain results explicit in code and
  reject unchecked use before execution.
- [LangChain](https://docs.langchain.com/) and
  [LangGraph](https://docs.langchain.com/oss/python/langgraph) help structure
  LLM applications and agent workflows. Ledge can sit at a decision boundary;
  it is not an orchestration framework.
- [mypy](https://mypy.readthedocs.io/) and
  [Pyright](https://microsoft.github.io/pyright/#/) are Python type checkers;
  [Ruff](https://docs.astral.sh/ruff/) and
  [Pylint](https://pylint.pycqa.org/) are Python linting/static-analysis tools.
  A mature Python plugin or linter could cover parts of this space. Ledge tests
  a smaller DSL surface where `Uncertain[T]` and confidence guards are built
  into the checked execution path.
- Structured output and schema validation, such as
  [OpenAI Structured Outputs](https://platform.openai.com/docs/guides/structured-outputs)
  and [JSON Schema](https://json-schema.org/), help ensure outputs have the
  expected shape. Ledge addresses a different question: whether a program is
  allowed to use an AI-derived value without checking confidence and recording
  the decision path.

The current experiment is representing AI outputs as `Uncertain[T]`,
rejecting unchecked use before execution, and tying decisions to audit and
calibration evidence. There is no claim here of being first, unique, or
revolutionary.

**When you should NOT use Ledge.** If your team already has a working
discipline around uncertainty handling; if your AI calls are isolated enough
that a linter or a thin wrapper library is sufficient; if your stack
constraints make a separate-language layer unacceptable; if you need
production-grade tooling, IDE support, or ecosystem maturity. Ledge is an
experiment, not infrastructure.

---

## Limitations and non-goals

Things Ledge does not claim, with the most common technical objections
addressed up front.

**Does Ledge prove that the AI's answer is correct?** No. It only rejects
specific syntactic patterns of unchecked use.

**Does high confidence mean the answer is correct?** No. Backend confidence
scores are signals, not calibrated probabilities. The calibration layer
exists to measure the gap between declared and observed accuracy.

**Does it prevent all misuse of uncertain values?** Only according to the
implemented checker rules. See *Known checker limitations* below.

**Is this a full formal type system?** No. It is a single-file,
flow-sensitive AST analysis. There is no mechanized soundness theorem and
no claim that the rules form a sound or complete system.

**Is the audit trail immutable against a malicious admin?** No. The hash
chain plus external anchor file detects modification by an attacker with
DB access but no anchor access. An attacker who controls both can forge a
clean history.

**Does it replace evaluation, calibration monitoring, or human review?**
No. Calibration is helpful but is not a substitute for evals, behavioral
testing, or a human in the loop where the cost of a wrong answer is high.

**Does it guarantee EU AI Act, GDPR, HIPAA, or any other compliance?** No.
The regulatory export is intended to support structured evidence review, but it
does not establish compliance. Compliance in any specific jurisdiction requires
legal counsel.

**Why not just use Python + mypy/Pyright?** See *Why a DSL plus SDK* above --
that is a legitimate choice for many teams. Ledge pairs an adoptable Python
SDK with a narrower DSL boundary for cases that need stricter checked
execution.

### Known checker limitations

These are limitations of the static analysis pass, not bugs:

- **Intraprocedural only.** The checker tracks Uncertain within a function
  body. It does not follow values across function boundaries. Function
  parameters/returns annotated as `uncertain[T]` are honored at the
  boundary; the `AIDerived` runtime wrapper preserves AI provenance through
  extraction.
- **Conservative on early-return guards.** Patterns like
  `if confidence_of(x) < t: return; use(x)` are not currently recognized as
  narrowing the rest of the block. Use the `if ... >= t: ... else:` form, or
  use `unsafe_value_of(x)` if you've satisfied yourself out-of-band.
- **No `not is_uncertain(x)`.** Only the positive forms
  (`is_confident(x)`, `confidence_of(x) >= t`) are recognized as narrowing.
- **No alias analysis beyond a single `define c as confidence_of(x)`.**
  More complex aliasing (e.g., reading the confidence through a map) won't
  narrow.
- **No lambda flow narrowing.** A confidence check inside a lambda body
  doesn't narrow the lambda parameter for subsequent expressions.
- **Lambdas in `map(...)` propagate inner Uncertain.** `list[uncertain[T]]`
  is recognized and iteration of such a list triggers the same checks.
  More complex higher-order patterns may not be recognized.

If you hit a case the checker should recognize but doesn't, open an issue.

---

## How Ledge relates to existing work

**Turn** -- Kizito, 2024 ([arxiv:2603.08755](https://arxiv.org/abs/2603.08755))
Typed LLM inference as a language primitive with a confidence operator,
designed for agentic systems where LLMs write code. Ledge targets developers
building systems that *use* LLMs and adds domain calibration, outcome
tracking, and a chained audit trail.

**QUASAR** -- 2025 ([arxiv:2506.12202](https://arxiv.org/abs/2506.12202) | [OpenReview](https://openreview.net/forum?id=TvpaeQVTGQ))
A language for LLM code actions with uncertainty quantification via conformal
prediction, transpiling from Python written by LLMs. Ledge is written by
developers and enforces handling at static-analysis time. QUASAR's uncertainty
is grounded in conformal-prediction theory; Ledge's calibration is empirical.

**IMMACULATE** -- Guo et al., 2026 ([arxiv:2602.22700](https://arxiv.org/abs/2602.22700))
Audits whether LLM API providers execute the model they claim. Ledge audits
whether the *code using* those models handles their output safely. Complementary.

**SAUP** -- Zhao et al., 2024 ([arxiv:2412.01033](https://arxiv.org/abs/2412.01033))
Uncertainty propagation through multi-step LLM agent reasoning at runtime
using situational weights. Ledge implements transitive uncertainty propagation
as `chain_confidence()` at the language level (position-weighted decay,
weak-step penalty) and surfaces it to the static checker.

If you know of relevant work we missed, open an issue.

---

## Security model

No Python `eval()` or `exec()`. Ledge uses a custom tree-walker interpreter,
so Python's object-introspection escape paths do not apply.

Python FFI imports are blocked by default in safe mode:

```bash
ledge run program.ledge --safe-mode               # block all imports + cap iterations
ledge run program.ledge --allow-import=math,json  # whitelist specific modules
```

These execution flags still run the static checker first. Add `--unsafe` only
when you explicitly want to skip the Uncertain contract check.

For server deployments where users submit Ledge code, run inside Docker or
similar OS-level isolation. `--safe-mode` is not a substitute for that.

---

## Tests

```bash
python tests/conformance.py   # 284/284 passed
python -m pytest tests/unit/  # 373 passed
```

The test count moves over time. The conformance harness and the unit suite
are the source of truth.

---

## Frequently asked questions

**Who is this for?**
Developers building systems that use AI models in production, especially in
regulated industries where "I forgot to check confidence" is a real failure
mode.

**Does it replace Python?**
No. Ledge is for the layer where AI decisions are made. Everything else
stays in your existing language.

**Is the confidence score actually accurate?**
No. The calibration layer measures how accurate it is over time and on your
data. See [CALIBRATION_GUIDE.md](CALIBRATION_GUIDE.md).

**Is the audit trail legally acceptable?**
The export can support structured evidence review, but it does not establish
legal compliance. Whether it is useful for a specific process is for your
counsel.

**Can I use this for production-critical decisions?**
Not yet. It is a working prototype with checkable runtime properties.

What works today:
- The static contract above (enforced by the tests in `tests/unit/test_typechecker.py`)
- Hash-chained audit trail with external anchor verification
- OpenAI backend using token log-probabilities for confidence
- Domain calibration with Brier score, ECE, and false accept/reject rates
- Position-weighted chain confidence with weak-step penalization
- Structured regulatory export for evidence review

What doesn't:
- Distributed audit storage
- A mature package ecosystem
- Known production deployments
- IDE tooling beyond the bundled LSP server
- Mechanized proofs of the type rules

**Zero production deployments -- why should I trust this?**
You shouldn't. You should verify it. Every property in this document is
checkable in under 5 minutes with no API key. The properties either hold
when you run them or they don't.

---

## License

MIT

---

## Questions and feedback

If something breaks, a claim doesn't hold up, or you know existing work that
does this better -- open an issue. If you use Ledge in a real system, even
experimentally, we want to hear about it.
