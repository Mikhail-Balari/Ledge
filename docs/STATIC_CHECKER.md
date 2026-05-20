# Static Checker

This document describes the static `Uncertain[T]` checker in Ledge 1.2.0. It is an implementation reference for users and reviewers, not a formal type-system specification.

## Contract

Ledge treats AI inference results as `Uncertain[T]`. A program must not use an uncertain value as an ordinary value until it has made confidence handling explicit.

The checker currently recognizes these safe patterns:

- `if confidence_of(x) >= threshold:` followed by `value_of(x)` inside that block.
- `when(x, threshold, fallback)`, which extracts the value only above the threshold and otherwise returns the fallback.
- `unsafe_value_of(x)`, an explicit escape hatch for demonstrations and code that deliberately accepts the risk.

The checker rejects direct use of an uncertain value in output, arithmetic, boolean conditions, function calls, string interpolation, and unchecked `value_of(...)`. This includes nested forms such as `show "{value_of(r)}"` and `show "{r}"` unless the expression is inside a recognized confidence guard or uses an explicit safe extraction pattern.

## CLI behavior

- `ledge check --types file.ledge` runs the static checker and reports issues without executing the program.
- `ledge run file.ledge` runs the same static checker before execution. If issues are found, the command exits non-zero and does not execute the program.
- `ledge run file.ledge --unsafe` skips the static checker and executes directly.

The `--unsafe` flag is intended for debugging, migration, and examples that intentionally demonstrate unsafe behavior. It is not the recommended path for normal execution.

## Python API behavior

- `checked_run(source)` runs the static checker first and executes only if the program passes.
- `checked_run_file(path)` reads a file and delegates to `checked_run(...)`.
- `run(source)` is the low-level interpreter entry point. It executes directly and bypasses the checker by design for tests, embedding, and tooling that wants explicit control.

Code that wants the same safety gate as `ledge run` should use `checked_run(...)`, not `run(...)`.

## Limitations

The checker is intentionally small in the current release:

- It is intraprocedural and single-file.
- It tracks common local aliases, but not arbitrary interprocedural dataflow.
- It does not claim whole-program soundness.
- It does not replace runtime monitoring, evals, human review, sandboxing, or policy enforcement.
- It does not prove that model confidence is calibrated.

These limits are release blockers for production-critical use unless the deployment wraps Ledge with additional controls appropriate to the risk.

## Verification

Useful local checks:

```bash
python -m ledge_lang.cli check --types examples/medical_triage.ledge
python -m ledge_lang.cli run examples/medical_triage.ledge
python scripts/pre_release_check.py
```

For intentionally unsafe experiments, keep the example local and use the
explicit bypass:

```ledge
define r as analyze("untrusted text") as "sentiment"
show unsafe_value_of(r)
```

```bash
python -m ledge_lang.cli run <that-file> --unsafe
```

`unsafe_value_of(...)` is an escape hatch. It is not part of the safe contract,
and intentionally unsafe snippets are not included in the official
expected-to-pass example set.

The pre-release script typechecks all official examples expected to pass, runs the unit and conformance suites, runs the bundled medical triage demo, builds the package, and verifies that the built wheel contains the bundled demo file.
