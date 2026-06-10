"""Audit-ready confidence evidence records."""

from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any

from ledge_lang._version import __version__

from .exceptions import (
    InvalidEvidenceError,
    InvalidEvidenceScoreError,
    InvalidEvidenceSourceError,
)
from .hashing import sha256_text, stable_json_dumps

SCHEMA_VERSION = "confidence-evidence/v1"
RAW_DATA_WARNING = "raw_data_included_review_storage_controls"
RAW_LIKE_METADATA_KEYS = {
    "raw",
    "raw_input",
    "raw_output",
    "input",
    "output",
    "prompt",
    "response",
    "completion",
    "model_output",
    "user_input",
    "user_text",
    "customer_data",
    "customer_text",
    "pii",
    "secret",
    "token",
    "api_key",
    "password",
}


def _coerce_score(value: object, field_name: str = "score") -> float:
    if isinstance(value, bool):
        raise InvalidEvidenceScoreError(f"{field_name} must not be bool")
    if not isinstance(value, (int, float)):
        raise InvalidEvidenceScoreError(
            f"{field_name} must be a finite number between 0.0 and 1.0"
        )
    coerced = float(value)
    if coerced != coerced or coerced in (float("inf"), float("-inf")):
        raise InvalidEvidenceScoreError(
            f"{field_name} must be a finite number between 0.0 and 1.0"
        )
    if coerced < 0.0 or coerced > 1.0:
        raise InvalidEvidenceScoreError(
            f"{field_name} must be a finite number between 0.0 and 1.0"
        )
    return coerced


def _require_non_empty_text(value: object, field_name: str, error_type: type[Exception]) -> str:
    if not isinstance(value, str) or not value.strip():
        raise error_type(f"{field_name} is required and must be a non-empty string")
    return value


def _has_raw_like_metadata(value: object) -> bool:
    if not isinstance(value, dict):
        return False

    keys = {str(key).lower() for key in value.keys()}
    if value.get("raw_data_included") is True or keys & RAW_LIKE_METADATA_KEYS:
        return True

    for nested in value.values():
        if isinstance(nested, dict) and _has_raw_like_metadata(nested):
            return True
        if isinstance(nested, list) and any(_has_raw_like_metadata(item) for item in nested):
            return True
    return False


def _append_raw_data_warning(warnings: list[str], *metadata_values: object) -> None:
    if any(_has_raw_like_metadata(value) for value in metadata_values):
        if RAW_DATA_WARNING not in warnings:
            warnings.append(RAW_DATA_WARNING)


@dataclass
class EvidenceSource:
    """One evidence source contributing to a confidence conclusion."""

    source_type: str
    status: str
    score: float | None = None
    impact: str | None = None
    warnings: list[str] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.source_type = _require_non_empty_text(
            self.source_type,
            "source_type",
            InvalidEvidenceSourceError,
        )
        self.status = _require_non_empty_text(
            self.status,
            "status",
            InvalidEvidenceSourceError,
        )
        if self.score is not None:
            self.score = _coerce_score(self.score, "source score")
        self.warnings = deepcopy(list(self.warnings or []))
        self.details = deepcopy(dict(self.details or {}))
        self.metadata = deepcopy(dict(self.metadata or {}))
        _append_raw_data_warning(self.warnings, self.details, self.metadata)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_type": self.source_type,
            "status": self.status,
            "score": self.score,
            "impact": self.impact,
            "warnings": deepcopy(self.warnings),
            "details": deepcopy(self.details),
            "metadata": deepcopy(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EvidenceSource":
        if not isinstance(data, dict):
            raise InvalidEvidenceSourceError("evidence source must be a dictionary")
        return cls(
            source_type=data.get("source_type"),
            status=data.get("status"),
            score=data.get("score"),
            impact=data.get("impact"),
            warnings=list(data.get("warnings") or []),
            details=dict(data.get("details") or {}),
            metadata=dict(data.get("metadata") or {}),
        )


@dataclass
class ConfidenceEvidence:
    """Audit-ready evidence backing a confidence score."""

    evidence_id: str
    boundary_id: str
    score: float
    sources: list[EvidenceSource]
    warnings: list[str] = field(default_factory=list)
    created_at: str | None = None
    ledge_version: str | None = None
    schema_version: str = SCHEMA_VERSION
    input_hash: str | None = None
    output_hash: str | None = None
    policy_id: str | None = None
    policy_hash: str | None = None
    evidence_hash: str | None = None
    redaction_applied: bool = True
    redaction_strategy: str | None = "hash_only"
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.evidence_id = _require_non_empty_text(
            self.evidence_id,
            "evidence_id",
            InvalidEvidenceError,
        )
        self.boundary_id = _require_non_empty_text(
            self.boundary_id,
            "boundary_id",
            InvalidEvidenceError,
        )
        self.schema_version = _require_non_empty_text(
            self.schema_version,
            "schema_version",
            InvalidEvidenceError,
        )
        self.score = _coerce_score(self.score)
        if not isinstance(self.sources, list):
            raise InvalidEvidenceError("sources must be a list")
        self.sources = [
            deepcopy(source)
            if isinstance(source, EvidenceSource)
            else EvidenceSource.from_dict(source)
            for source in deepcopy(self.sources)
        ]
        self.warnings = deepcopy(list(self.warnings or []))
        if not self.sources and "no_evidence_sources" not in self.warnings:
            self.warnings.append("no_evidence_sources")
        self.ledge_version = self.ledge_version or __version__
        if not isinstance(self.redaction_applied, bool):
            raise InvalidEvidenceError("redaction_applied must be bool")
        self.metadata = deepcopy(dict(self.metadata or {}))
        self._apply_raw_data_warnings()

    def _apply_raw_data_warnings(self) -> None:
        _append_raw_data_warning(self.warnings, self.metadata)

    def to_dict(self) -> dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "boundary_id": self.boundary_id,
            "score": self.score,
            "sources": [source.to_dict() for source in self.sources],
            "warnings": deepcopy(self.warnings),
            "created_at": self.created_at,
            "ledge_version": self.ledge_version,
            "schema_version": self.schema_version,
            "input_hash": self.input_hash,
            "output_hash": self.output_hash,
            "policy_id": self.policy_id,
            "policy_hash": self.policy_hash,
            "evidence_hash": self.evidence_hash,
            "redaction_applied": self.redaction_applied,
            "redaction_strategy": self.redaction_strategy,
            "metadata": deepcopy(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ConfidenceEvidence":
        if not isinstance(data, dict):
            raise InvalidEvidenceError("confidence evidence must be a dictionary")
        return cls(
            evidence_id=data.get("evidence_id"),
            boundary_id=data.get("boundary_id"),
            score=data.get("score"),
            sources=[
                source if isinstance(source, EvidenceSource) else EvidenceSource.from_dict(source)
                for source in data.get("sources", [])
            ],
            warnings=list(data.get("warnings") or []),
            created_at=data.get("created_at"),
            ledge_version=data.get("ledge_version"),
            schema_version=data.get("schema_version", SCHEMA_VERSION),
            input_hash=data.get("input_hash"),
            output_hash=data.get("output_hash"),
            policy_id=data.get("policy_id"),
            policy_hash=data.get("policy_hash"),
            evidence_hash=data.get("evidence_hash"),
            redaction_applied=data.get("redaction_applied", True),
            redaction_strategy=data.get("redaction_strategy", "hash_only"),
            metadata=dict(data.get("metadata") or {}),
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True, ensure_ascii=False)

    @classmethod
    def from_json(cls, text: str) -> "ConfidenceEvidence":
        return cls.from_dict(json.loads(text))

    def to_canonical_dict(self) -> dict[str, Any]:
        data = self.to_dict()
        data.pop("evidence_hash", None)
        return data

    def to_canonical_json(self) -> str:
        return stable_json_dumps(self.to_canonical_dict())

    def compute_hash(self) -> str:
        return sha256_text(self.to_canonical_json())

    def with_hash(self) -> "ConfidenceEvidence":
        data = self.to_dict()
        data["evidence_hash"] = self.compute_hash()
        return ConfidenceEvidence.from_dict(data)
