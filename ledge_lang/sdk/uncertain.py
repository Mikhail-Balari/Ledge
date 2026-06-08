"""Uncertain values for the Ledge Python SDK core."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Generic, TypeVar

from ._validation import _coerce_confidence
from .decision import DecisionResult
from .evidence import ConfidenceEvidence
from .exceptions import UnsafeUnwrapError
from .policy import DecisionPolicy, normalize_action

T = TypeVar("T")


@dataclass
class Uncertain(Generic[T]):
    """AI-derived or otherwise uncertain value with an explicit confidence."""

    value: T | None
    confidence: float
    source: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    evidence: ConfidenceEvidence | None = None

    def __post_init__(self) -> None:
        self.confidence = _coerce_confidence(self.confidence)
        self.metadata = dict(self.metadata)
        self.warnings = list(self.warnings)

    def is_usable(self, policy: DecisionPolicy) -> bool:
        """Return True only when the value satisfies the policy threshold."""
        if self.value is None and not policy.allow_missing_value:
            return False
        return self.confidence >= policy.min_confidence

    def handle(
        self,
        policy: DecisionPolicy,
        on_low_confidence: str | None = None,
    ) -> DecisionResult[T]:
        """Apply a minimal decision policy to this uncertain value."""
        metadata = dict(self.metadata)
        if self.source is not None:
            metadata.setdefault("source", self.source)
        if self.evidence is not None:
            metadata.setdefault("evidence_score", self.evidence.score)
            if self.evidence.source is not None:
                metadata.setdefault("evidence_source", self.evidence.source)

        if self.value is None and not policy.allow_missing_value:
            return DecisionResult(
                action=policy.on_missing_value,
                allowed=False,
                value=None,
                confidence=self.confidence,
                reason="missing value; policy does not allow missing values",
                policy_name=policy.name,
                warnings=self._combined_warnings(),
                metadata=metadata,
            )

        if self.confidence >= policy.min_confidence:
            return DecisionResult(
                action="allow",
                allowed=True,
                value=self.value,
                confidence=self.confidence,
                reason=(
                    f"confidence {self.confidence:.3f} meets threshold "
                    f"{policy.min_confidence:.3f}"
                ),
                policy_name=policy.name,
                warnings=self._combined_warnings(),
                metadata=metadata,
            )

        action = (
            normalize_action(on_low_confidence, "on_low_confidence")
            if on_low_confidence is not None
            else policy.on_low_confidence
        )
        return DecisionResult(
            action=action,
            allowed=False,
            value=self.value,
            confidence=self.confidence,
            reason=(
                f"low confidence {self.confidence:.3f}; required "
                f"{policy.min_confidence:.3f}"
            ),
            policy_name=policy.name,
            warnings=self._combined_warnings(),
            metadata=metadata,
        )

    def unsafe_unwrap(self, reason: str) -> T:
        """Explicit escape hatch that requires a developer-supplied reason."""
        if reason is None or not str(reason).strip():
            raise UnsafeUnwrapError("unsafe_unwrap requires a non-empty reason")
        if self.value is None:
            raise UnsafeUnwrapError("cannot unsafe_unwrap an uncertain value with no value")
        return self.value

    def _combined_warnings(self) -> list[str]:
        warnings = list(self.warnings)
        if self.evidence is not None:
            warnings.extend(self.evidence.warnings)
        return warnings
