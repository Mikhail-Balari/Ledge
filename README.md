# Ledge

**Ledge is a governance runtime and programming language for AI decisions.**

It does not trust model confidence blindly.  
It forces confidence handling, records decisions, captures outcomes,  
and calibrates thresholds from real-world accuracy.

> Ledge turns AI uncertainty from an informal engineering convention  
> into a typed, auditable, empirically calibrated control system.

---

## Why does this matter?

Most general-purpose languages allow code like this to run with no error:

```python
# Python — valid code, no warning
result = model.classify(patient_symptoms)
send_treatment_recommendation(result["diagnosis"])
# What if the model was 30% confident? Nobody checked.
```

In Ledge, this is caught before the program runs:

```ledge
define result as classify(symptoms) using ["urgent", "routine", "monitor"]
show result
# STATIC ANALYSIS ERROR: Unsafe use of Uncertain value
# Confidence was never verified.
# Fix: check confidence_of(result) before using it.
```

The only way to use the result is to handle uncertainty explicitly:

```ledge
define result as classify(symptoms) using ["urgent", "routine", "monitor"]
if confidence_of(result) >= 0.85:
    show value_of(result)
else:
    show "Refer to specialist — confidence too low"
```

### But aren't confidence scores arbitrary?

Ledge does not trust confidence scores. It measures them.

Model confidence scores are imperfect. OpenAI logprobs are not calibrated for your domain. Anthropic's structured self-assessment is self-reported. Ledge does not claim these scores are ground truth.

What Ledge does: it forces you to handle them, records every decision, captures real outcomes, and measures empirically whether the confidence scores from your chosen model are actually predictive in your domain. If your model says 0.9 confidence but only achieves 70% accuracy on your medical data, Ledge detects that and raises your threshold automatically.

You cannot know if confidence is useful until you measure it. Ledge gives you the infrastructure to measure it.

---

## Why a language and not a Python library?

A library can ask you to call `check_confidence()`. It cannot prevent you from forgetting.

In Python, this code compiles, runs, and nobody is warned:

```python
result = model.classify(patient_symptoms)
send_treatment_recommendation(result["diagnosis"])
# model was 30% confident. nobody checked.
```

A Python typechecker cannot detect that `result` carries uncertainty without explicit annotations on every function that touches AI output — annotations developers routinely omit. Ledge is a language because the only way to *guarantee* — not suggest, guarantee — that uncertain values are handled before use is to own the type system entirely. A library enforces conventions. Ledge enforces correctness.

This is not solved by mypy or static type checkers. mypy verifies type consistency — it cannot verify that you checked confidence before unwrapping a value. Expressing that constraint requires dependent types or effect systems that Python does not have. Ledge has them because it owns the type system entirely.

---

## Install and run in 2 minutes

```bash
pip install ledge-lang
```

Then run a real example — no API key needed:

```bash
ledge run examples/showcase/medical_triage.ledge
```

Expected output:
```
=== MEDICAL TRIAGE SYSTEM ===
PATIENT P001: ESCALATE TO HUMAN (confidence=0)
PATIENT P002: ESCALATE TO HUMAN (confidence=0)
PATIENT P003: ESCALATE TO HUMAN (confidence=0)
Decisions logged in audit trail: 3
Cryptographic chain intact: true
```

Without a real AI backend connected, every patient escalates to human review.  
Connect a real backend and it will classify with backend-provided confidence estimates.

---

## Four verifiable guarantees

Run these yourself. No API key. No setup. Under 5 minutes.

### G1 — Zero confidence without a backend

```bash
python demo_guarantee1.py
```

```
classify   without backend -> confidence = 0
analyze    without backend -> confidence = 0
generate   without backend -> confidence = 0
Guarantee verified: without backend, confidence = 0
```

Without a real model connected, confidence is always exactly zero. The system cannot invent certainty.

### G2 — Unsafe AI use is caught before execution

```bash
python demo_guarantee2.py
```

```
Unsafe code errors detected: 1
Message: Unsafe use of Uncertain value 'r' in 'show'
         confidence was never verified
Safe code errors detected: 0
Guarantee verified.
```

The static typechecker catches unsafe code before the program runs — not after something goes wrong in production. If the typechecker itself encounters an internal bug, it raises `TypecheckerInternalError` with a full stack trace — it never silently returns an empty result.

*Note on terminology: Ledge is currently interpreted, not compiled in the traditional sense. "Compile-time" refers to the pre-execution static analysis phase that runs before any code executes.*

### G3 — Cryptographic audit trail

```bash
python demo_guarantee3.py
```

```
Entries recorded:           3
Chain intact (initial):     True
After modifying confidence: False
After inserting fake entry: False
Guarantee verified: any modification breaks the chain.
```

Every AI decision is recorded with a SHA-256 hash chain. Changing any field — confidence, timestamp, result — breaks the chain and is detected immediately. An external anchor file (`~/.ledge/anchors.jsonl`) records chain state every 10 decisions — if the SQLite database is deleted and regenerated, the anchors detect the inconsistency.

**Deleting and regenerating the database is detected.** The anchor file lives outside the database. If the database is wiped and rebuilt, the anchors show a state discontinuity. An attacker would need to control both the database and the anchor file to forge a clean history.

```bash
ledge audit --verify-anchors   # verify anchor file against current database
```

### G4 — Safe failure by design

```bash
python demo_guarantee4.py
```

```
Patients escalated to human:   3
Patients classified automatic: 0
Guarantee verified: without backend, zero automatic decisions.
```

Without a backend, the system escalates to human. It does not approve. It does not classify. It waits.

---

## Five layers of AI governance

```
Uncertain output → forced handling → logged decision
     → recorded outcome → calibrated threshold
          → safer future decision
```

**What about multi-step chains?**
Confidence degrades across reasoning steps. If each step is 0.85 confident, five steps yield 0.85^5 = 0.44 — not 0.85. Ledge handles this with `chain_confidence()`, which applies position-weighted decay and penalizes weak steps. The result is a single propagated confidence value for the full chain, subject to the same enforcement rules as any other uncertain value.

### Layer 1 — Pre-execution uncertainty safety

Unsafe AI use is a static analysis error. The program does not run. *(See G2 above.)*

### Layer 2 — Runtime confidence provenance

Confidence comes from the backend you connect. Without one, it is always exactly 0.0. *(See G1 above.)*

**How confidence is computed per backend:**

```python
from ledge_lang.backends import openai_backend, anthropic_backend

# OpenAI: uses token log-probabilities over classification labels.
# This is a token-probability-derived confidence estimate.
# It is more grounded than self-reported confidence, but it is
# not assumed to be calibrated. The calibration layer (Layer 3)
# still measures it against real outcomes per model and domain.
backend = openai_backend(api_key="sk-...", model="gpt-4o-mini")

# Anthropic: uses structured self-assessment — the model is asked
# to return a confidence score alongside its answer as part of
# the structured output. This is not a native probability score
# from the model weights.
backend = anthropic_backend(api_key="sk-ant-...", model="claude-3-haiku-20240307")
```

**Important:** "Confidence from backend" does not mean "the model is 92% sure in an absolute sense." It means the backend returned a score using the method above. For OpenAI logprobs, this is a token-probability-derived confidence estimate — more grounded than self-reported confidence, but not assumed to be calibrated for your domain. For Anthropic structured output, it is a self-reported score. Treat both as signals, not ground truth. The calibration layer (Layer 3) exists precisely because these scores may not reflect real accuracy.

### Layer 3 — Domain calibration

This is the answer to "but confidence scores are arbitrary" — see the framing above.

Ledge compares declared confidence against real outcomes per model and domain:

```bash
ledge audit --calibration gpt-4 medical
ledge audit --calibration-metrics gpt-4 medical
```

Real output from the audit system:

```
Calibration Report: gpt-4 / medical (n=30)
  RANGE      COUNT  MEAN_CONF  ACCURACY  CAL_ERROR
  0.8-0.9      20     0.848     0.850     0.002
  0.9-1.0      10     0.924     0.700     0.224  <- overconfident
                      WARNING: only 10 samples in 0.9-1.0 bucket
                      Threshold in this range is provisional (n < 30)

  Brier score         : 0.1711  (lower is better; 0.0 is perfect)
  ECE                 : 0.0756  (lower is better; <0.10 is a rough heuristic)
  False accept rate   : 0.1429  (accepted when wrong)
  False reject rate   : 0.7826  (rejected when right)
  Calibrated threshold: 0.921   (provisional — see warning above)
  Well calibrated     : False   (overconfident in 0.9-1.0 range)
```

The backend reports 0.9+ confidence in the medical domain but achieves only 70% accuracy there. Ledge detects this and raises the threshold. The warning flags that 10 samples is below the recommended minimum of 30 for reliable threshold estimation.

See [CALIBRATION_GUIDE.md](CALIBRATION_GUIDE.md) for minimum sample requirements, limitations of self-reported outcomes, and drift handling.

### Layer 4 — Adaptive thresholds

The default 0.85 is arbitrary. Replace it with a value derived from your actual outcomes:

```python
from ledge_lang.calibration import DomainCalibrator

threshold = calibrator.get_calibrated_threshold(
    'gpt-4', 'medical', desired_accuracy=0.90, min_samples=30
)
# Returns calibrated threshold based on observed outcomes
# Returns default 0.85 with a warning if n < min_samples
```

### Layer 5 — Compliance-supporting audit trail

Every decision exports in a structured format designed for EU AI Act Article 12/13 evidence documentation:

```bash
ledge audit --export-regulatory report.json
ledge audit --validate-regulatory report.json
```

```
VALIDATION PASSED — compliance-supporting Article 12/13 export is structurally valid
```

*What this means:* The export matches Ledge's evidence schema for Articles 12 (logging and monitoring) and 13 (transparency). Article 12 covers automatic logging capabilities during the system lifecycle. Article 13 covers transparency sufficient for deployers to understand and appropriately use AI outputs. Generating a structurally valid JSON-LD is a necessary but not sufficient condition for regulatory compliance. The schema structure is inspectable by running `--export-regulatory` and examining the output. Consult legal counsel for your specific use case and jurisdiction.

---

## Showcase examples

Each of these runs without an API key:

```bash
ledge run examples/showcase/financial_analysis.ledge   # credit risk assessment
ledge run examples/showcase/legal_contracts.ledge      # contract clause review
ledge run examples/showcase/email_scanner.ledge        # phishing detection
ledge run examples/showcase/hiring_screen.ledge        # candidate screening
ledge run examples/showcase/loan_approval.ledge        # Basel III + EU AI Act Article 14
ledge run examples/showcase/medical_record.ledge       # diagnosis with audit trail
```

All show the same pattern: without a real AI backend, every decision escalates to human review. No automatic decisions without evidence.

---

## Frequently asked questions

**Who is this for?**  
Developers building systems that use AI models in production — especially in regulated industries: healthcare, finance, legal, insurance.

**Does it replace Python?**  
No. Ledge is for the layer where AI decisions are made and must be governed. Python and other languages handle everything else.

**What about the confidence score — is it actually accurate?**  
Ledge does not claim confidence scores are accurate. It enforces that they are handled, logged, and compared against real outcomes over time. The calibration layer measures how accurate they actually are. See [CALIBRATION_GUIDE.md](CALIBRATION_GUIDE.md).

**Is the audit trail legally acceptable?**  
The export meets the structural requirements of Ledge's Article 12/13 evidence schema. Whether it satisfies legal compliance in your specific jurisdiction requires legal counsel.

**Is this production-ready?**  
Honestly: it is a working prototype with real, verifiable guarantees.

What works today:
- The four guarantees (verified by 284 conformance tests + 338 unit tests)
- Cryptographic audit trail with hash chains and external anchor verification
- OpenAI backend using real token log-probabilities for confidence
- Domain calibration with Brier score, ECE, and false accept/reject rates
- Weighted chain confidence with position decay and weak-step penalization
- Compliance-supporting regulatory export

What does not yet exist:
- Distributed audit storage
- A mature package ecosystem
- Known production deployments

**Zero production deployments — why should I trust this?**  
You should not trust it — you should verify it. Every guarantee in this document is checkable in under 5 minutes with no API key and no account. The guarantees either hold when you run them or they do not. That is the answer to zero production deployments.

---

## How Ledge relates to existing work

**Turn** — Kizito, 2024  
[arxiv:2603.08755](https://arxiv.org/abs/2603.08755)  
Introduces typed LLM inference as a language primitive with a confidence operator. Designed for agentic systems where LLMs write code. Ledge targets developers building systems that *use* LLMs, and adds domain calibration, outcome tracking, and cryptographic audit trails not present in Turn.

**QUASAR** — 2025  
[arxiv:2506.12202](https://arxiv.org/abs/2506.12202) | [OpenReview](https://openreview.net/forum?id=TvpaeQVTGQ)  
A language for LLM code actions with uncertainty quantification via conformal prediction. Transpiles from Python written by LLMs. Ledge is written by developers and enforces confidence handling at analysis time.

**IMMACULATE** — Guo et al., 2026  
[arxiv:2602.22700](https://arxiv.org/abs/2602.22700)  
Audits whether LLM API providers execute the model they claim. Ledge audits whether the *code using* those models handles their output safely. Complementary, not competing.

**SAUP** — Zhao et al., 2024  
[arxiv:2412.01033](https://arxiv.org/abs/2412.01033)  
Uncertainty propagation through multi-step LLM agent reasoning at runtime using situational weights. Ledge implements transitive uncertainty propagation as `chain_confidence()` at the language level — using position-weighted confidence decay and weak-step penalization — and enforces it at analysis time.

**On the research gap:**  
We found no published work combining pre-execution enforcement of AI confidence handling with empirical domain calibration and cryptographic audit trails in a single language. If you know of relevant work we missed, open an issue.

---

## Security model

No Python `eval()` or `exec()`. Ledge uses a custom tree-walker interpreter — Python's object introspection escape paths do not apply.

Python FFI imports are blocked by default:

```bash
ledge run program.ledge --safe-mode               # blocks all imports
ledge run program.ledge --allow-import=math,json  # whitelist specific modules
```

For server deployments where users submit Ledge code: run inside Docker.  
`--safe-mode` is not a replacement for OS-level isolation.

---

## Tests

```bash
python tests/conformance.py   # 284/284 passed
python -m pytest tests/unit/  # 338 passed, 1 pre-existing Windows encoding failure
```

---

## What Ledge does not do

- Does not prove that any individual confidence score is accurate at decision time — it measures and calibrates confidence empirically over time
- Does not replace Python for general-purpose programming
- No package ecosystem beyond 15 included packages
- Native compiler requires `gcc` (experimental)
- Ledge Studio requires `pip install "ledge-lang[studio]"`
- Known production deployments: zero
- Audit trail protects against post-hoc modification by any actor with database access, including the system operator. It does not protect against an attacker who also controls the anchor file.
- Designed for Python/JavaScript developers working with LLMs today — not a theoretically optimal type system. Languages with dependent types (Haskell, Idris) offer stronger guarantees at much higher adoption cost.

---

## License

MIT

---

## Questions and feedback

If something breaks, a claim does not hold up, or you know existing work that does this better — open an issue.

If you use Ledge in a real system, even experimentally — we want to hear about it.
