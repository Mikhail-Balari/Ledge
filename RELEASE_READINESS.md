# Release Readiness - Ledge 1.2.0

This document records the final technical readiness state for Ledge 1.2.0 as a
durable release checklist for the public repository.

## Final Guarantee Statement

Ledge's current static guarantee is deliberately narrow: `ledge check --types`,
the default `ledge run` command, and Python `checked_run(...)` reject programs
that use a value typed `Uncertain[T]` without one of the recognized handling
constructs. The recognized safe patterns are a positive confidence guard such as
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
- `ledge_lang.checked_run(source)` is the safety-gated Python API. It runs the
  static checker first, raises `LedgeError` with the type issues if checking
  fails, and does not execute the program on failure.
- `ledge_lang.checked_run_file(path)` reads a file and delegates to
  `checked_run(...)`.
- The low-level Python API `ledge_lang.run(source)` executes source directly and
  bypasses the checker by design for interpreter and test harness use.

## Durable Review Documents

- `docs/STATIC_CHECKER.md` documents the checked CLI and Python execution paths.
- `docs/THREAT_MODEL.md` documents the current boundary and non-goals.
- `docs/ROADMAP.md` documents the path from alpha software toward
  production-critical readiness.

## Verification Commands Run

- `python -m pytest tests/unit/`
- `python -m pytest tests/unit/test_checked_run_api.py -q`
- `python -m pytest tests/integration/test_cli_run_typecheck.py -q`
- GitHub Actions CI for unit tests, integration tests, conformance tests, and
  `scripts/pre_release_check.py`
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
- PyPI install verification of `ledge-lang==1.2.0` from a clean temporary
  environment after upload.

## Results

- Unit tests: PASS, `373 passed`.
- Conformance: PASS, `284/284 passed`.
- Official example typecheck: PASS, all 18 official `.ledge` examples pass.
- Targeted CLI tests: PASS, `8 passed` in
  `tests/integration/test_cli_run_typecheck.py`.
- Targeted checked Python API tests: PASS, `6 passed` in
  `tests/unit/test_checked_run_api.py`.
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
- README quickstart status: PASS, the README uses the published PyPI package as
  the primary install path and keeps local wheel installation as a source
  checkout option.
- Version consistency: PASS, `pyproject.toml`, `ledge_lang.__version__`,
  `ledge version`, the wheel filename, and installed package metadata all report
  `1.2.0`.
- PyPI status: PASS, `ledge-lang==1.2.0` is uploaded and verified.
- Git tag: PASS, `v1.2.0` exists.
- GitHub Release: PASS, `Ledge 1.2.0` exists.
- Packaging metadata: PASS, license metadata was updated to the modern
  `license = "MIT"` form and the legacy license classifier was removed.
- Public CI: PASS, `.github/workflows/ci.yml` runs on push and pull request
  without secrets.

## Files Removed From Public Release Surface

Temporary process logs and channel-specific readiness notes were removed from
the public repository. Future scratch verification logs are ignored by
`.gitignore`.

## Remaining Risks

- Ledge is still alpha software. The checker is intentionally scoped and does
  not claim whole-program or interprocedural soundness.
- The static Uncertain contract is enforced by the CLI, checker, and
  `checked_run(...)`, while `run(...)` remains a low-level execution primitive
  for callers that need manual control.
- The audit log is hash-chained and useful as supporting evidence, but it does
  not protect against an attacker who controls both the SQLite store and the
  anchor file.
- Regulatory exports are structured evidence artifacts, not proof of legal
  compliance.
- Ledge 1.2.0 is published, tagged, and released, but remains alpha software.

## Final Launch Verdict

Ready now.
