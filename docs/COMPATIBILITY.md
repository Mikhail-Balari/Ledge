# Ledge Compatibility Policy
## Version 1.0.0

This document defines what is guaranteed to remain stable across Ledge
versions, and what may change.

---

## Stability guarantees

### What will NOT break between patch versions (1.0.x → 1.0.y)

- All programs that currently produce correct output will continue to
  produce identical output
- All error messages that currently fire will continue to fire for the
  same conditions
- The `run()` Python API signature will not change
- All builtins documented in `docs/SPEC.md` will remain available
- The `FEATURE_MATRIX.md` "shipped" items will not be removed
- Test suite will not decrease in coverage

### What will NOT break between minor versions (1.0.x → 1.1.x)

All of the above, plus:
- The bytecode format will remain compatible within a major version
- The LSP protocol version will not change
- The Python FFI (`import "python:module"`) will continue to work
- The `ledge_lang.run()` Python API will remain compatible

### What MAY change in minor versions (1.0.x → 1.1.x)

- New builtins may be added (not breaking — programs don't use them)
- New syntax may be added (not breaking — existing programs unaffected)
- Error messages may be improved (not breaking — tests check behavior, not exact wording)
- Performance may improve (not breaking)
- New experimental features may appear (clearly marked in FEATURE_MATRIX.md)

---

## Breaking changes policy

Breaking changes only occur on major version bumps (1.x.x → 2.x.x).

A **breaking change** is any change that:
- Makes a currently valid Ledge program produce an error
- Changes the output of a currently valid program
- Removes a shipped builtin or language construct
- Changes the semantics of an existing construct

Before a breaking change:
1. The change is proposed in `docs/proposals/`
2. It is reviewed for 90 days
3. A deprecation warning is issued in the previous minor version
4. Migration guide is written before release

---

## Experimental features

Features marked [EXPERIMENTAL] in `docs/FEATURE_MATRIX.md` have **no**
stability guarantee. They may change, break, or be removed without notice.

Current experimental features (v1.0.0):
- `stream from "url"` — parses but URL sources not connected
- `agent ... :` blocks — syntax only, no MCP connectivity
- `subscribe to / emit to` — basic syntax, no runtime support

Do not build production systems on experimental features.

---

## Deprecation process

1. Feature is marked `[deprecated]` in FEATURE_MATRIX.md
2. Runtime emits a deprecation warning when used
3. Feature remains usable for one full minor version cycle
4. Feature is removed in the following minor version (not major)

Deprecated features will always have a documented migration path.

---

## Version numbering

Ledge follows [Semantic Versioning](https://semver.org):

```
MAJOR.MINOR.PATCH

1.0.0  — first stable release
1.0.1  — bug fix (no behavior change)
1.1.0  — new features, backwards compatible
2.0.0  — breaking changes (90-day review, migration guide)
```

---

## The `any` escape hatch

Type annotations are optional. `define x: any as ...` accepts any type.
This is always backwards compatible — annotated code can be de-annotated.

---

## Python API stability

The public Python API for embedding Ledge:

```python
from ledge_lang import run, compile_ledge
from ledge_lang.interpreter import Interpreter
from ledge_lang.lexer import Lexer
from ledge_lang.parser import Parser

# run() signature — stable
lines, value = run(
    source: str,
    output_fn: callable = print,
    ai_backend: dict = None
)
```

Internal modules (`ledge_lang.ast_nodes`, `ledge_lang.core_types` internals)
are not part of the public API and may change.

---

## Conformance test stability

The 284 conformance tests in `tests/conformance.py` define the observable
behavior of the language. Any change that causes a conformance test failure
is a breaking change, regardless of version bump.

Third-party implementations should run `tests/conformance.py` to verify
their implementation. A conforming implementation that passes all tests
is guaranteed to work with code written for any other conforming implementation.
