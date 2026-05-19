# Release Readiness - Ledge 1.2.0

This document records the final technical readiness state for Ledge 1.2.0.
It replaces the temporary Hacker News working logs with a durable release
checklist for the public repository.

## Final Guarantee Statement

Ledge's current static guarantee is deliberately narrow: `ledge check --types`
and the default `ledge run` command reject single-file programs that use a value
typed `Uncertain[T]` without one of the recognized handling constructs. The
recognized safe patterns are a positive confidence guard such as
`if confidence_of(x) >= threshold:`, `when(x, threshold, fallback)`, or the
explicit escape hatch `unsafe_value_of(x)`. This is a flow-sensitive static
analysis pass, not a mechanized proof, not a formal soundness theorem, and not a
legal compliance certification.

## Command Behavior

- `ledge run <file.ledge>` runs the static typechecker first. If type issues are
  found, it prints the issues, exits non-zero, and does not execute the program.
- `ledge run <file.ledge> --unsafe` skips the static typecheck and executes the
  program anyway. This is the explicit bypass for experiments and unsafe
  examples.
- `ledge check --types <file.ledge>` only runs the static checker and does not
  execute the program.
- The low-level Python API `ledge_lang.run(source)` executes source directly.
  Python API callers that need the same safety gate as the CLI should call
  `ledge_lang.typechecker.check_types(source)` before `run(source)`.

## Verification Commands Run

- `python -m pytest tests/unit/`
- `python -m pytest tests/integration/test_cli_run_typecheck.py -q`
- `python tests/conformance.py`
- `python -m ledge_lang.cli check --types <file>` for every official `.ledge`
  example under `ledge_lang/demos/`, `examples/`, and `examples/showcase/`
- `python -m ledge_lang.cli demo medical_triage`
- `python scripts/pre_release_check.py`
- `python -m build`
- Clean virtual environment install of
  `dist/ledge_lang-1.2.0-py3-none-any.whl`
- Installed wheel checks from outside the repository:
  `ledge --help`, `ledge version`, `ledge demo`, `ledge demo medical_triage`,
  `python -m ledge_lang.cli --help`, and
  `python -m ledge_lang.cli demo medical_triage`

## Results

- Unit tests: PASS, `343 passed`.
- Conformance: PASS, `284/284 passed`.
- Official example typecheck: PASS, all 18 official `.ledge` examples pass.
- Targeted CLI tests: PASS, `4 passed` in
  `tests/integration/test_cli_run_typecheck.py`.
- Pre-release script: PASS, `scripts/pre_release_check.py` completed
  successfully.
- Bundled demo: PASS, `medical_triage` runs through the checked CLI path.
- Package build: PASS, source distribution and wheel were built.
- Wheel content verification: PASS, the wheel contains
  `ledge_lang/demos/medical_triage.ledge`.
- Clean wheel install: PASS, the built wheel installed into a clean temporary
  virtual environment without relying on editable-install behavior.
- Installed command verification: PASS, `ledge --help`, `ledge version`,
  `ledge demo`, and `ledge demo medical_triage` all work from the clean
  environment.
- README quickstart status: PASS, the README distinguishes the local 1.2.0
  wheel workflow from the future PyPI install workflow.
- Version consistency: PASS, `pyproject.toml`, `ledge_lang.__version__`,
  `ledge version`, the wheel filename, and installed package metadata all report
  `1.2.0`.
- PyPI status: 1.2.0 is NOT uploaded yet.
- Packaging metadata: PASS, license metadata was updated to the modern
  `license = "MIT"` form and the legacy license classifier was removed.

## Files Removed From Public Release Surface

Temporary launch-process logs were removed from the public repository:

- `HACKER_NEWS_FINAL_PASS_LOG.md`
- `HACKER_NEWS_READINESS.md`
- `hn_risky_phrases.txt`
- `hn_example_typecheck_results.txt`
- `hn_pre_hn_check_results.txt`
- `hn_packaging_verification.txt`

Future `hn_*.txt` scratch files are ignored by `.gitignore`.

## Remaining Risks

- Ledge is still alpha software. The checker is intentionally scoped and does
  not claim whole-program or interprocedural soundness.
- The static Uncertain contract is enforced by the CLI and checker, while the
  low-level Python API remains an execution primitive for callers that need
  manual control.
- The audit log is hash-chained and useful as supporting evidence, but it does
  not protect against an attacker who controls both the SQLite store and the
  anchor file.
- Regulatory exports are structured evidence artifacts, not proof of legal
  compliance.
- The package has not been uploaded to PyPI as version 1.2.0.

## Final Launch Verdict

Ready to post publicly after PyPI 1.2.0 is uploaded.
