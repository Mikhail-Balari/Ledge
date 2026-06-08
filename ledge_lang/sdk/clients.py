"""Deterministic SDK clients for examples and tests.

These clients do not make network calls and do not represent real model
confidence. Provider adapters belong in a later phase.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Generic, Mapping, TypeVar

from .evidence import ConfidenceEvidence
from .uncertain import Uncertain

T = TypeVar("T")


class BaseAIClient(Generic[T]):
    """Small interface for deterministic SDK examples."""

    def predict(self, key: str, payload: Any | None = None) -> Uncertain[T]:
        raise NotImplementedError


@dataclass
class DeterministicAIClient(Generic[T]):
    """Return predefined Uncertain values for stable examples and tests."""

    responses: Mapping[str, Uncertain[T] | Mapping[str, Any]]
    default: Uncertain[T] | None = None
    source: str = "deterministic_fake"

    def predict(self, key: str, payload: Any | None = None) -> Uncertain[T]:
        raw = self.responses.get(key)
        if raw is None:
            if self.default is not None:
                return self.default
            return Uncertain(
                value=None,
                confidence=0.0,
                source=self.source,
                warnings=[f"no deterministic response configured for {key!r}"],
                metadata={"key": key},
            )
        if isinstance(raw, Uncertain):
            return raw
        return _uncertain_from_mapping(raw, self.source, key)


@dataclass
class FakeAIClient(DeterministicAIClient[T]):
    """Alias-style fake client for tests and public examples."""

    responses: Mapping[str, Uncertain[T] | Mapping[str, Any]] = field(default_factory=dict)


def _uncertain_from_mapping(
    raw: Mapping[str, Any],
    default_source: str,
    key: str,
) -> Uncertain[Any]:
    evidence = None
    if "evidence" in raw and raw["evidence"] is not None:
        evidence_raw = raw["evidence"]
        if isinstance(evidence_raw, ConfidenceEvidence):
            evidence = evidence_raw
        else:
            evidence = ConfidenceEvidence(**dict(evidence_raw))

    metadata = dict(raw.get("metadata", {}))
    metadata.setdefault("key", key)
    return Uncertain(
        value=raw.get("value"),
        confidence=raw.get("confidence", 0.0),
        source=raw.get("source", default_source),
        metadata=metadata,
        warnings=list(raw.get("warnings", [])),
        evidence=evidence,
    )
