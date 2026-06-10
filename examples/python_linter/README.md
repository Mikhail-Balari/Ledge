# Ledge Python Linter Example

This directory contains a small, synthetic example for `ledge lint-python`.

The linter is AST-based CI enforcement for common unsafe Python decision-boundary
patterns around the Ledge SDK. It is not a proof of complete Python semantic
safety and it is not a mypy or Pyright plugin.

Run the safe example:

```bash
ledge lint-python examples/python_linter/safe_usage.py --config examples/python_linter/ledge.toml
```

Run the unsafe example:

```bash
ledge lint-python examples/python_linter/unsafe_usage.py --config examples/python_linter/ledge.toml
```

The examples use synthetic refund-routing data only. They do not use API keys,
real customer data, production systems, or compliance workflows.
