# Ledge — Current Status
## Version 1.1.0 — May 2026

## What works today

### Core guarantees (run these yourself)
    python demo_guarantee1.py  # Zero confidence without backend
    python demo_guarantee2.py  # Unsafe AI use = compile error
    python demo_guarantee3.py  # Cryptographic audit trail
    python demo_guarantee4.py  # Safe failure by design

### New in this version
    ledge audit --stats              # Real accuracy by model/domain
    ledge audit --verify             # Verify cryptographic chain
    ledge audit --calibration gpt-4 medical  # Calibration report
    ledge audit --compare gpt-4 claude medical  # Model comparison
    ledge audit --export-regulatory report.json  # EU AI Act export
    ledge run "classify this as spam or not"     # Natural language

### Tests
- Conformance: 284/284
- Unit tests: 337 passing
- 2 pre-existing failures (Windows console encoding)

## Six features that make Ledge unique

1. Persistent audit trail (SQLite) — decisions survive 
   between sessions. Auditable days later.

2. Interprocedural uncertainty propagation — uncertainty 
   does not disappear inside function boundaries.

3. Automatic domain calibration — learns real model 
   accuracy per domain from historical outcomes.

4. Automatic model comparison — tells you exactly which 
   decisions would change if you switch models.

5. Regulatory export — EU AI Act Article 12/13 compliant 
   JSON-LD with one command.

6. Natural language interface — describe what you want 
   in English, Ledge generates and runs the safe program.

## Known limitations
- Audit trail is local SQLite (not distributed)
- NL interface uses heuristics (no LLM required)
- Native compiler requires gcc
- Not on PyPI public registry yet
