# Ledge — One-page summary

**Current release-prep target: 1.7.0 Alpha**

This one-page summary originated in the 1.2.0 materials. For the current
1.7.0 Alpha public surface, Ledge also includes the Python SDK Core, Python
linter / CI enforcement, Confidence Evidence Engine, and Tamper-Evident
Decision Ledger. The ledger uses local append-oriented records plus
verification; it is not production-ready, enterprise-ready, legal compliance
certification, tamper-proof, audit-proof, immutable storage, blockchain, or
secure storage by itself.

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
| Static analyzer (intraprocedural Uncertain tracking) | works, covered by unit and integration tests |
| Runtime `Uncertain[T]` / `AIDerived` / `UncertainChain` | works |
| Tree-walker interpreter + bytecode VM | works, 1500-program differential |
| SHA-256 chained audit log with external anchor file | works, threat model documented |
| Domain calibration (Brier, ECE, false accept/reject) | works |
| Model migration comparison | works |
| Structured evidence export (JSON-LD) | works (structural only; not a legal compliance determination) |
| OpenAI backend (token logprobs) | works (logprobs are signals, not calibrated probabilities) |
| Anthropic backend (structured self-assessment) | works (self-reported, not derived from weights) |
| LSP server, formatter, debugger | works |
| Native C99 compiler (experimental, requires gcc) | partial |
| 284 conformance tests + 373 unit tests | passing in release checks |

---

## What this is NOT

- Not a formal type system. No mechanized soundness proof.
- Not a calibrated uncertainty framework. Backend confidence is a signal.
- Not a legal compliance product. Regulatory export is supporting evidence.
- Not a security boundary against an attacker who controls both the DB and the anchor file.
- Not a replacement for evals, monitoring, or human review.
- Not a general-purpose replacement for Python.

---

## Installation

```bash
python -m pip install dist/ledge_lang-1.2.0-py3-none-any.whl
ledge demo medical_triage             # runs without an API key
```

After Ledge 1.2.0 is published to PyPI, replace the local wheel install with
`pip install ledge-lang`.

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
- [docs/STATIC_CHECKER.md](docs/STATIC_CHECKER.md) — checked CLI and Python execution paths.
- [docs/THREAT_MODEL.md](docs/THREAT_MODEL.md) — current boundaries and non-goals.
- [docs/ROADMAP.md](docs/ROADMAP.md) — path from alpha to production-critical readiness.
