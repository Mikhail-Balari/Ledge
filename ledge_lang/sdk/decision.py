"""Decision result objects for the Ledge Python SDK core."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Generic, TypeVar

from ._validation import _coerce_confidence
from .policy import normalize_action

T = TypeVar("T")


@dataclass
class DecisionResult(Generic[T]):
    """Serializable result of applying a policy to an uncertain value."""

    action: str
    allowed: bool
    value: T | None
    confidence: float
    reason: str
    policy_name: str | None = None
    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.action = normalize_action(self.action)
        self.allowed = self.action == "allow"
        self.confidence = _coerce_confidence(self.confidence)
        self.warnings = list(self.warnings)
        self.metadata = dict(self.metadata)
