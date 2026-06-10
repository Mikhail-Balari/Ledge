"""Structured diagnostics and formatters for Python lint output."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class Diagnostic:
    path: str
    line: int
    column: int
    rule_id: str
    severity: str
    message: str
    suggestion: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def format_diagnostics(diagnostics: Iterable[Diagnostic]) -> str:
    lines: list[str] = []
    for diagnostic in diagnostics:
        location = f"{diagnostic.path}:{diagnostic.line}:{diagnostic.column + 1}"
        lines.append(
            f"{location}: {diagnostic.severity.upper()} {diagnostic.rule_id}: "
            f"{diagnostic.message}"
        )
        if diagnostic.suggestion:
            lines.append(f"  Suggestion: {diagnostic.suggestion}")
    return "\n".join(lines)


def diagnostics_to_json(diagnostics: Iterable[Diagnostic]) -> str:
    return json.dumps([diagnostic.to_dict() for diagnostic in diagnostics], indent=2)


def display_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(Path.cwd().resolve()))
    except ValueError:
        return str(path)
