"""Private validation helpers for SDK confidence-like fields."""

from __future__ import annotations

import math

from .exceptions import InvalidConfidenceError


def _coerce_confidence(value: object, field_name: str = "confidence") -> float:
    """Return a finite float in [0.0, 1.0] or raise InvalidConfidenceError."""
    if isinstance(value, bool):
        raise InvalidConfidenceError(f"{field_name} must not be bool")
    if not isinstance(value, (int, float)):
        raise InvalidConfidenceError(
            f"{field_name} must be a finite number between 0.0 and 1.0"
        )
    coerced = float(value)
    if not math.isfinite(coerced) or coerced < 0.0 or coerced > 1.0:
        raise InvalidConfidenceError(
            f"{field_name} must be a finite number between 0.0 and 1.0"
        )
    return coerced
