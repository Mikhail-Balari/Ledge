"""Redaction helpers for confidence evidence.

These helpers hash raw values without persisting them. Summaries are deliberately
coarse so they do not leak full raw input or output by default.
"""

from __future__ import annotations

from typing import Any

from .exceptions import CanonicalSerializationError
from .hashing import hash_text, stable_json_dumps


def _stable_value_text(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    try:
        return stable_json_dumps(value)
    except CanonicalSerializationError as exc:
        raise CanonicalSerializationError(
            f"unsupported redaction hash input type: {type(value).__name__}"
        ) from exc


def hash_input(value: Any) -> str:
    """Hash input-like data without storing the raw value."""
    return hash_text(_stable_value_text(value))


def hash_output(value: Any) -> str:
    """Hash output-like data without storing the raw value."""
    return hash_text(_stable_value_text(value))


def redacted_summary(value: Any, max_length: int = 120) -> str:
    """Return a coarse redacted summary without full raw content."""
    text = _stable_value_text(value)
    type_name = type(value).__name__
    capped = max(0, int(max_length))
    length_label = len(text)
    return f"[redacted {type_name}; length={length_label}; max_length={capped}]"
