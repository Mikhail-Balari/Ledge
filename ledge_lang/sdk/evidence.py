"""Minimal evidence container for SDK-level decision handling."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ._validation import _coerce_confidence


@dataclass
class ConfidenceEvidence:
    """Minimal Phase 1 container for confidence-related metadata."""

    score: float
    source: str | None = None
    signals: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.score = _coerce_confidence(self.score, "evidence score")
        self.signals = dict(self.signals)
        self.warnings = list(self.warnings)
        self.metadata = dict(self.metadata)
