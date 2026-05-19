# Ledge Claim Registry
## Version 1.2.0

Public claims should be backed by a command, test, or source file. This registry
tracks the claims that are currently reasonable to make; it is an accountability
document, not a proof of formal soundness.

## AI And Uncertainty

| Claim | Evidence | Status |
|---|---|---|
| Without an AI backend, AI operations report `confidence=0.0`. | `tests/unit/`, `python scripts/pre_release_check.py` | Checked |
| Unchecked `Uncertain[T]` use is rejected by the static checker. | `tests/unit/test_typechecker.py`, `tests/integration/test_cli_run_typecheck.py` | Checked |
| `ledge run <file.ledge>` runs the static checker before execution by default. | `tests/integration/test_cli_run_typecheck.py` | Checked |
| `ledge run <file.ledge> --unsafe` is the explicit CLI bypass. | `tests/integration/test_cli_run_typecheck.py` | Checked |

## Language And Tooling

| Claim | Evidence | Status |
|---|---|---|
| The conformance suite passes. | `python tests/conformance.py` | Checked in release verification |
| Unit tests pass. | `python -m pytest tests/unit/` | Checked in release verification |
| Official `.ledge` examples typecheck under `ledge check --types`. | `python scripts/pre_release_check.py` | Checked in release verification |
| The bundled `medical_triage` demo ships in the wheel. | `python scripts/pre_release_check.py` and clean wheel install verification | Checked |

## Claims Not To Make Yet

| Claim | Why |
|---|---|
| Ledge is ready for critical production systems. | It is alpha software with no known production deployments. |
| Ledge has a mechanized proof or formal soundness theorem. | The current checker is an implementation-level static analysis pass. |
| The audit log resists every local attacker. | It has a limited threat model and does not protect against an attacker who controls both store and anchor files. |
| Ledge provides legal or regulatory certification for EU AI Act, GDPR, HIPAA, or any other regime. | The project can produce supporting evidence artifacts, not legal certification. |
