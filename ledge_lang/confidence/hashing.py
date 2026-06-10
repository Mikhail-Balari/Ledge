"""Deterministic hashing helpers for confidence evidence."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from .exceptions import CanonicalSerializationError


def stable_json_dumps(obj: Any) -> str:
    """Serialize JSON-compatible data deterministically for hashing."""
    try:
        return json.dumps(
            obj,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise CanonicalSerializationError(
            f"object is not canonical JSON serializable: {exc}"
        ) from exc


def sha256_text(text: str) -> str:
    """Return lowercase hex SHA-256 for UTF-8 text."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def hash_dict(obj: dict[str, Any]) -> str:
    """Hash a JSON-compatible dictionary using canonical JSON."""
    return sha256_text(stable_json_dumps(obj))


def hash_text(value: str) -> str:
    """Hash a text value without storing the original value."""
    return sha256_text(value)


def hash_bytes(value: bytes) -> str:
    """Return lowercase hex SHA-256 for bytes."""
    return hashlib.sha256(value).hexdigest()
