# Ledge — One-page summary

**Version 1.2.0**

A small experimental DSL for making AI uncertainty explicit in program flow.
Surrounds AI calls with a static analysis pass that rejects direct use of
uncertain results, records every AI decision in a SHA-256 chained audit log,
and compares declared confidence against real outcomes so the threshold can
be recalibrated.

---

## The thirty-second pitch

The most common production bug in AI code is "I forgot to check confidence":

```python
# Python — runs fine, silently acts on low-confidence outputs
result = model.classify(email)
if result["label"] == "spam":
    delete_email()
```

In Ledge the static analyzer rejects this:

```ledge
define result as classify(email) using ["spam", "ok"]
if value_of(result) = "spam":   # ERROR — value_of outside a confidence guard
    delete_email()
```

The accepted form is one of:

```ledge
# (1) Recognized confidence guard:
if confidence_of(result) >= 0.9:
    if value_of(result) = "spam":
        delete_email()
    else:
        # legitimate, do nothing
else:
    send_to_human_review()

# (2) Runtime-checked extraction:
if when(result, 0.9, "ok") = "spam":
    delete_email()

# (3) Explicit escape hatch (deliberately ugly name):
if unsafe_value_of(result) = "spam":
    delete_email()
```

This is a static-analysis property, not a formal theorem. The checker is a
single-file, flow-sensitive AST walker with documented limitations. See
[GUARANTEES.md](GUARANTEES.md) for the precise contract and the explicit
list of cases it does NOT yet recognize.

---

## What's in the box

| Component | Status |
|---|---|
| Static analyzer (intraprocedural Uncertain tracking) | works, 35 tests |
| Runtime `Uncertain[T]` / `AIDerived` / `UncertainChain` | works |
| Tree-walker interpreter + bytecode VM | works, 1500-program differential |
| SHA-256 chained audit log with external anchor file | works, threat model documented |
| Domain calibration (Brier, ECE, false accept/reject) | works |
| Model migration comparison | works |
| EU AI Act Article 12/13 evidence export (JSON-LD) | works (structural only — see caveats) |
| OpenAI backend (token logprobs) | works (logprobs are signals, not calibrated probabilities) |
| Anthropic backend (structured self-assessment) | works (self-reported, not derived from weights) |
| LSP server, formatter, debugger | works |
| Native C99 compiler (experimental, requires gcc) | partial |
| 284 conformance tests + 343 unit tests | passing on Linux/macOS/Windows |

---

## What this is NOT

- Not a formal type system. No mechanized soundness proof.
- Not a calibrated uncertainty framework. Backend confidence is a signal.
- Not a legal compliance product. Regulatory export is supporting evidence.
- Not tamper-proof against an attacker who controls both the DB and the anchor file.
- Not a replacement for evals, monitoring, or human review.
- Not a general-purpose replacement for Python.

---

## Installation

```bash
pip install ledge-lang
ledge demo medical_triage             # runs without an API key
```

Optional extras:

```bash
pip install "ledge-lang[studio]"      # web IDE
```

OpenAI / Anthropic backends are pulled in as needed via their own SDKs;
no Ledge-specific extras required.

---

## Where to go next

- [README.md](README.md) — full quickstart, the precise checker contract, FAQ, comparisons.
- [GUARANTEES.md](GUARANTEES.md) — each runtime property paired with a runnable demo and its threat model.
- [CALIBRATION_GUIDE.md](CALIBRATION_GUIDE.md) — minimum sample sizes, drift handling, what calibration doesn't fix.
- [HACKER_NEWS_READINESS.md](HACKER_NEWS_READINESS.md) — what was softened, strengthened, and what remains before a formal PL claim could be made.
