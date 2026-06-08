"""Decision policies for SDK-level uncertain values."""

from __future__ import annotations

from dataclasses import dataclass

from ._validation import _coerce_confidence
from .exceptions import PolicyValidationError


VALID_ACTIONS = {"allow", "human_review", "block"}


def normalize_action(action: str, field_name: str = "action") -> str:
    """Normalize and validate a policy or decision action string."""
    if not isinstance(action, str):
        raise PolicyValidationError(f"{field_name} must be a string action")
    normalized = action.strip().lower()
    if normalized not in VALID_ACTIONS:
        allowed = ", ".join(sorted(VALID_ACTIONS))
        raise PolicyValidationError(
            f"{field_name} must be one of: {allowed}; got {action!r}"
        )
    return normalized


@dataclass(frozen=True)
class DecisionPolicy:
    """Minimal SDK policy for handling an uncertain AI-derived value."""

    min_confidence: float
    name: str | None = None
    allow_missing_value: bool = False
    on_low_confidence: str = "human_review"
    on_missing_value: str = "block"
    on_schema_error: str = "block"

    def __post_init__(self) -> None:
        threshold = _coerce_confidence(self.min_confidence, "min_confidence")
        object.__setattr__(self, "min_confidence", threshold)
        object.__setattr__(
            self,
            "on_low_confidence",
            normalize_action(self.on_low_confidence, "on_low_confidence"),
        )
        object.__setattr__(
            self,
            "on_missing_value",
            normalize_action(self.on_missing_value, "on_missing_value"),
        )
        object.__setattr__(
            self,
            "on_schema_error",
            normalize_action(self.on_schema_error, "on_schema_error"),
        )
