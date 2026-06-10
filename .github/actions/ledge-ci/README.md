# Ledge CI Action

Composite GitHub Action for running `ledge lint-python` in CI.

Example:

This example assumes the `v1.5.0` tag exists. Replace it with the Ledge
release tag you want to run.

```yaml
- uses: Mikhail-Balari/Ledge/.github/actions/ledge-ci@v1.5.0
  with:
    paths: "src examples"
    config: "ledge.toml"
```

This action installs `ledge-lang` from PyPI and runs AST-based Python linting
for common unsafe Ledge SDK decision-boundary patterns.

It does not require secrets or API keys. It is not complete semantic
verification, production-readiness certification, or compliance enforcement.
