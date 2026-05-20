# Ledge — Current Status

**Version 1.2.0 — May 2026**

## Quickstart

```bash
pip install ledge-lang
ledge demo medical_triage
```

Ledge 1.2.0 is published on PyPI. For a source checkout, you can also build and
install the local wheel from `dist/`.

No clone, no API key, no setup. The bundled demo escalates every patient to
human review because there is no AI backend connected — that is the
safe-failure default.

## What works today

### The four runtime properties (see GUARANTEES.md for caveats)

    python demo_guarantee1.py  # confidence = 0 without a backend
    python demo_guarantee2.py  # static checker rejects direct use of Uncertain
    python demo_guarantee3.py  # SHA-256 chained audit log detects modification
    python demo_guarantee4.py  # zero automatic decisions without a backend

### Toolchain

    ledge run program.ledge                      # typecheck, then interpret
    ledge run program.ledge --unsafe             # skip typecheck and interpret
    ledge check --types program.ledge            # run the static analyzer
    ledge demo medical_triage                    # run a bundled demo
    ledge audit --verify                         # verify the chain
    ledge audit --verify-anchors                 # cross-check anchors vs store
    ledge audit --calibration <model> <domain>   # measured vs declared accuracy
    ledge audit --calibration-metrics <m> <d>    # Brier, ECE, false accept/reject
    ledge audit --compare <m_a> <m_b> <domain>   # migration risk between models
    ledge audit --export-regulatory report.json  # EU AI Act Article 12/13 JSON-LD
    ledge audit --validate-regulatory report.json

### Breaking change in 1.2.0

`value_of(x)` on an Uncertain `x` is now a static analysis error outside
of a recognized confidence guard (`if confidence_of(x) >= t:`,
`if is_confident(x):`, alias-aware variants, or `when(x, t, fallback)`).
The runtime behavior of `value_of` is unchanged. The escape hatch is the
new `unsafe_value_of(x)`, which is allowed anywhere and signals to readers
that confidence was not checked.

Migration:

```ledge
# Before (1.1.x — accepted by checker, silently unsafe):
show value_of(r)

# After (1.2.0 — pick one):
if confidence_of(r) >= 0.85: show value_of(r)   # idiomatic
show when(r, 0.85, "fallback")                  # runtime-checked
show unsafe_value_of(r)                         # explicit unchecked
```

## Tests

- Conformance: 284 / 284 passing
- Unit suite: 354 / 354 passing
- Integration suite: 21 / 21 passing
- 0 known failures on Linux, macOS, Windows

(See CI for the authoritative numbers.)

## Known limitations of the static checker

- Intraprocedural only — does not track Uncertain across function calls.
- Conservative on early-return guards: `if c < t: return; use(r)` does not
  narrow the rest of the block. Use `if c >= t: ... else:` instead.
- No `not is_uncertain(x)` — only positive forms.
- One-hop alias support; no multi-hop.
- No flow narrowing inside lambda bodies.

See [GUARANTEES.md](GUARANTEES.md) Property 2 for the full list.

## What does not yet exist

- Distributed audit storage (audit is per-process, optionally persisted to
  local SQLite via the audit store).
- A mature package ecosystem.
- IDE tooling beyond the bundled LSP server.
- Mechanized proofs of the static rules.
- Known production deployments.

## Checked execution paths

- `ledge run file.ledge` typechecks before execution.
- `ledge run file.ledge --unsafe` bypasses that static check explicitly.
- `ledge check --types file.ledge` reports type issues without execution.
- `checked_run(source)` is the safety-gated Python API.
- `run(source)` remains the low-level direct execution API for interpreter and
  test harness use.
