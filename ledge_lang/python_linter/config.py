"""Configuration loading for the Ledge Python linter."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


class LintConfigError(Exception):
    """Raised when linter configuration cannot be parsed."""


@dataclass
class LintConfig:
    min_confidence: float | None = None
    critical_actions: set[str] = field(default_factory=set)
    unsafe_unwrap_requires_reason: bool = True

    @classmethod
    def from_mapping(cls, data: dict[str, Any]) -> "LintConfig":
        ledge = data.get("ledge", {})
        if not isinstance(ledge, dict):
            raise LintConfigError("[ledge] must be a table")

        min_confidence = ledge.get("min_confidence")
        if min_confidence is not None:
            min_confidence = _validate_min_confidence(min_confidence)

        actions = ledge.get("actions", {})
        if actions is None:
            actions = {}
        if not isinstance(actions, dict):
            raise LintConfigError("[ledge.actions] must be a table")
        critical = actions.get("critical", [])
        if critical is None:
            critical = []
        if not isinstance(critical, list) or not all(isinstance(item, str) for item in critical):
            raise LintConfigError("ledge.actions.critical must be a list of strings")

        allow = ledge.get("allow", {})
        if allow is None:
            allow = {}
        if not isinstance(allow, dict):
            raise LintConfigError("[ledge.allow] must be a table")
        requires_reason = allow.get("unsafe_unwrap_requires_reason", True)
        if not isinstance(requires_reason, bool):
            raise LintConfigError("ledge.allow.unsafe_unwrap_requires_reason must be boolean")

        return cls(
            min_confidence=min_confidence,
            critical_actions=set(critical),
            unsafe_unwrap_requires_reason=requires_reason,
        )


def load_config(config_path: str | Path | None = None) -> LintConfig:
    """Load linter config from a TOML file, or return defaults."""
    if config_path is None:
        candidate = Path("ledge.toml")
        if not candidate.exists():
            return LintConfig()
    else:
        candidate = Path(config_path)
        if not candidate.exists():
            raise LintConfigError(f"config file not found: {candidate}")

    text = candidate.read_text(encoding="utf-8-sig")
    try:
        data = _loads_toml(text)
    except Exception as exc:
        raise LintConfigError(f"failed to parse config {candidate}: {exc}") from exc
    return LintConfig.from_mapping(data)


def _loads_toml(text: str) -> dict[str, Any]:
    try:
        import tomllib  # type: ignore[import-not-found]
    except ModuleNotFoundError:
        return _loads_simple_toml(text)
    return tomllib.loads(text)


def _validate_min_confidence(value: Any) -> float:
    if isinstance(value, bool):
        raise LintConfigError("ledge.min_confidence must not be boolean")
    if not isinstance(value, (int, float)):
        raise LintConfigError("ledge.min_confidence must be a number")
    confidence = float(value)
    if not math.isfinite(confidence) or not 0.0 <= confidence <= 1.0:
        raise LintConfigError("ledge.min_confidence must be between 0.0 and 1.0")
    return confidence


def _loads_simple_toml(text: str) -> dict[str, Any]:
    """Small TOML subset parser for ledge.toml on Python versions without tomllib."""
    root: dict[str, Any] = {}
    current = root
    for lineno, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        if line.startswith("[") and line.endswith("]"):
            section = line[1:-1].strip()
            if not section:
                raise LintConfigError(f"empty TOML section at line {lineno}")
            current = root
            for part in section.split("."):
                part = part.strip()
                if not part:
                    raise LintConfigError(f"invalid TOML section at line {lineno}")
                current = current.setdefault(part, {})
                if not isinstance(current, dict):
                    raise LintConfigError(f"section conflicts with value at line {lineno}")
            continue

        if "=" not in line:
            raise LintConfigError(f"expected key=value at line {lineno}")
        key, value = [part.strip() for part in line.split("=", 1)]
        if not key:
            raise LintConfigError(f"empty key at line {lineno}")
        current[key] = _parse_simple_value(value, lineno)
    return root


def _parse_simple_value(value: str, lineno: int) -> Any:
    if value in ("true", "false"):
        return value == "true"

    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [_parse_simple_value(item.strip(), lineno) for item in _split_list(inner)]

    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        return value[1:-1]

    try:
        if "." in value:
            return float(value)
        return int(value)
    except ValueError as exc:
        raise LintConfigError(f"unsupported value at line {lineno}: {value!r}") from exc


def _split_list(inner: str) -> list[str]:
    items: list[str] = []
    current: list[str] = []
    quote: str | None = None
    for char in inner:
        if quote is not None:
            current.append(char)
            if char == quote:
                quote = None
            continue
        if char in ("'", '"'):
            quote = char
            current.append(char)
            continue
        if char == ",":
            item = "".join(current).strip()
            if item:
                items.append(item)
            current = []
            continue
        current.append(char)

    item = "".join(current).strip()
    if item:
        items.append(item)
    return items
