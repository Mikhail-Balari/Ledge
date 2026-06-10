"""Command-line entry point for `ledge lint-python`."""

from __future__ import annotations

import argparse
import sys

from .config import LintConfigError, load_config
from .report import diagnostics_to_json, format_diagnostics
from .scanner import display_diagnostic_paths, lint_paths


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="ledge lint-python",
        description="Lint Python code for common unsafe Ledge SDK decision-boundary patterns.",
    )
    parser.add_argument("paths", nargs="+", help="Python files or directories to scan")
    parser.add_argument("--config", help="Path to ledge.toml")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args(argv)

    try:
        config = load_config(args.config)
        result = lint_paths(args.paths, config)
    except (FileNotFoundError, LintConfigError) as exc:
        if args.format == "json":
            print(
                diagnostics_to_json(
                    [
                        _config_error_diagnostic(str(exc)),
                    ]
                )
            )
        else:
            print(f"ledge lint-python: {exc}", file=sys.stderr)
        return 2

    diagnostics = display_diagnostic_paths(result.diagnostics)
    if args.format == "json":
        print(diagnostics_to_json(diagnostics))
    else:
        print(f"Ledge Python lint: {result.files_scanned} file(s)")
        if diagnostics:
            print(format_diagnostics(diagnostics))
            print(f"\nFAIL: {len(diagnostics)} Python lint violation(s)")
        else:
            print("PASS: no Python lint violations")

    return 1 if diagnostics else 0


def _config_error_diagnostic(message: str):
    from .report import Diagnostic

    return Diagnostic(
        path="<config>",
        line=1,
        column=0,
        rule_id="LPY000",
        severity="error",
        message=message,
        suggestion="Fix the linter config or pass a valid --config path.",
    )
