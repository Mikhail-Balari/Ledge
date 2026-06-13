"""Canonical JSON helpers for decision ledger hash inputs."""

from __future__ import annotations

import json
import math
from collections.abc import Mapping
from typing import Any

from .exceptions import LedgerValidationError


def canonical_json(data: Mapping[str, Any]) -> str:
    """Return deterministic JSON suitable for ledger hash input."""
    if not isinstance(data, Mapping):
        raise LedgerValidationError("canonical ledger payload must be a mapping")

    _validate_json_like(data, "$")
    try:
        return json.dumps(
            data,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise LedgerValidationError("ledger payload is not canonical JSON serializable") from exc


def _validate_json_like(value: Any, path: str) -> None:
    if value is None or isinstance(value, (str, bool)):
        return

    if isinstance(value, int) and not isinstance(value, bool):
        return

    if isinstance(value, float):
        if not math.isfinite(value):
            raise LedgerValidationError(f"non-finite number at {path}")
        return

    if isinstance(value, list):
        for index, item in enumerate(value):
            _validate_json_like(item, f"{path}[{index}]")
        return

    if isinstance(value, Mapping):
        for key, item in value.items():
            if not isinstance(key, str):
                raise LedgerValidationError(f"non-string key at {path}")
            _validate_json_like(item, f"{path}.{key}")
        return

    raise LedgerValidationError(f"unsupported JSON value at {path}")
