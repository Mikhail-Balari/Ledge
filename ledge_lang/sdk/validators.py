"""Validation helpers for SDK-level uncertain values."""

from __future__ import annotations

from typing import Any, Callable, TypeVar

from .exceptions import SchemaValidationError
from .uncertain import Uncertain

T = TypeVar("T")


def validate_with(value: T, validator: Callable[[T], bool]) -> tuple[bool, list[str]]:
    """Run a boolean validator and return a stable success/warnings tuple."""
    try:
        result = validator(value)
    except Exception as exc:
        return False, [f"validator raised {type(exc).__name__}: {exc}"]

    if result is True:
        return True, []
    if result is False:
        return False, ["validator returned False"]
    return False, [f"validator returned non-boolean result: {result!r}"]


def uncertain_from_validation(
    value: T,
    confidence: float,
    validator: Callable[[T], bool],
    source: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> Uncertain[T]:
    """Create an Uncertain value from a simple validation result."""
    ok, warnings = validate_with(value, validator)
    if ok:
        return Uncertain(
            value=value,
            confidence=confidence,
            source=source,
            metadata=metadata or {},
        )
    return Uncertain(
        value=None,
        confidence=0.0,
        source=source,
        metadata=metadata or {},
        warnings=warnings,
    )


def validate_pydantic(value: Any, model: Any) -> tuple[bool, list[str]]:
    """Optional Pydantic-style validation without adding Pydantic as a dependency."""
    try:
        if hasattr(model, "model_validate"):
            model.model_validate(value)
        elif hasattr(model, "parse_obj"):
            model.parse_obj(value)
        else:
            raise SchemaValidationError("model does not expose model_validate or parse_obj")
    except Exception as exc:
        return False, [f"schema validation failed: {exc}"]
    return True, []
