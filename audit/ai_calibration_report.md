# AI Calibration Report — Ledge v1.1.0

## Hard invariant

Without backend: confidence=0.0, value=nothing, ALWAYS.
Tested: analyze, classify, generate, ask, embed.
All 5 ops verified in tests/integration/test_install_smoke.py.

## Type preservation (fixed this cycle)

classify() now returns uncertain[text] even when value=nothing.
Previously returned uncertain[nothing] — now correct.

## Calibration study

Full study (confidence vs accuracy curves) requires real AI backend.
Planned for v1.2.0 with benchmarks on standard NLP tasks.
