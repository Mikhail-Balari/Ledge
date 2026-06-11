"""Calibration reporting for confidence evidence."""

from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .evidence import _coerce_score
from .exceptions import InvalidEvidenceError


@dataclass
class CalibrationOutcome:
    """One historical outcome used for calibration reporting."""

    boundary_id: str
    prediction_id: str
    score: float
    outcome: bool
    action: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.boundary_id, str) or not self.boundary_id.strip():
            raise InvalidEvidenceError("boundary_id is required")
        if not isinstance(self.prediction_id, str) or not self.prediction_id.strip():
            raise InvalidEvidenceError("prediction_id is required")
        self.score = _coerce_score(self.score, "score")
        if not isinstance(self.outcome, bool):
            raise InvalidEvidenceError("outcome must be bool")
        if self.action is not None and not isinstance(self.action, str):
            raise InvalidEvidenceError("action must be a string when provided")
        if self.metadata is None:
            self.metadata = {}
        elif not isinstance(self.metadata, dict):
            raise InvalidEvidenceError("calibration outcome metadata must be a dictionary")
        else:
            self.metadata = deepcopy(self.metadata)

    def to_dict(self) -> dict[str, Any]:
        return {
            "boundary_id": self.boundary_id,
            "prediction_id": self.prediction_id,
            "score": self.score,
            "outcome": self.outcome,
            "action": self.action,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CalibrationOutcome":
        if not isinstance(data, dict):
            raise InvalidEvidenceError("calibration outcome must be a dictionary")
        metadata = data.get("metadata") or {}
        if not isinstance(metadata, dict):
            raise InvalidEvidenceError("calibration outcome metadata must be a dictionary")
        return cls(
            boundary_id=data.get("boundary_id"),
            prediction_id=data.get("prediction_id"),
            score=data.get("score"),
            outcome=data.get("outcome"),
            action=data.get("action"),
            metadata=dict(metadata),
        )


@dataclass
class CalibrationReport:
    """Deterministic calibration report for a decision boundary."""

    boundary_id: str
    sample_count: int
    brier_score: float | None
    ece: float | None
    bins: list[dict[str, Any]]
    warnings: list[str] = field(default_factory=list)
    suggested_threshold: float | None = None
    limitations: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "boundary_id": self.boundary_id,
            "sample_count": self.sample_count,
            "brier_score": self.brier_score,
            "ece": self.ece,
            "bins": [dict(row) for row in self.bins],
            "warnings": list(self.warnings),
            "suggested_threshold": self.suggested_threshold,
            "limitations": list(self.limitations),
            "metadata": dict(self.metadata),
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True, ensure_ascii=False)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CalibrationReport":
        if not isinstance(data, dict):
            raise InvalidEvidenceError("calibration report must be a dictionary")
        return cls(
            boundary_id=data.get("boundary_id"),
            sample_count=int(data.get("sample_count", 0)),
            brier_score=data.get("brier_score"),
            ece=data.get("ece"),
            bins=[dict(row) for row in data.get("bins", [])],
            warnings=list(data.get("warnings") or []),
            suggested_threshold=data.get("suggested_threshold"),
            limitations=list(data.get("limitations") or []),
            metadata=dict(data.get("metadata") or {}),
        )


def load_outcomes(path: str | Path) -> list[CalibrationOutcome]:
    """Load calibration outcomes from a JSON file."""
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except OSError as exc:
        raise InvalidEvidenceError(f"could not read outcomes file: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise InvalidEvidenceError(f"malformed outcomes JSON: {exc.msg}") from exc

    if not isinstance(data, list):
        raise InvalidEvidenceError("outcomes file must contain a JSON list")
    return [CalibrationOutcome.from_dict(item) for item in data]


def generate_calibration_report(
    outcomes: list[CalibrationOutcome],
    *,
    boundary_id: str | None = None,
    bins: int = 10,
    min_samples: int = 30,
) -> CalibrationReport:
    """Generate deterministic Brier/ECE calibration metrics."""
    if bins <= 0:
        raise InvalidEvidenceError("bins must be a positive integer")
    if min_samples < 0:
        raise InvalidEvidenceError("min_samples must be non-negative")

    records = [
        item if isinstance(item, CalibrationOutcome) else CalibrationOutcome.from_dict(item)
        for item in list(outcomes or [])
    ]
    if boundary_id is not None:
        records = [item for item in records if item.boundary_id == boundary_id]

    report_boundary = boundary_id or _common_boundary_id(records)
    warnings: list[str] = []
    limitations = [
        "calibration requires historical outcomes",
        "brier_score_and_ece_are_reports_not_truth_guarantees",
        "suggested_thresholds_are_cautious_guidance_not_compliance_guarantees",
    ]

    if not records:
        warnings.append("no_matching_outcomes")
        return CalibrationReport(
            boundary_id=report_boundary,
            sample_count=0,
            brier_score=None,
            ece=None,
            bins=[],
            warnings=warnings,
            suggested_threshold=None,
            limitations=limitations,
            metadata={
                "bin_count": bins,
                "min_samples": min_samples,
                "threshold_rule": "none when no outcomes are available",
            },
        )

    sample_count = len(records)
    if sample_count < min_samples:
        warnings.append("low_sample_size")

    brier_score = sum((_truth(item.outcome) - item.score) ** 2 for item in records) / sample_count
    bin_rows = _build_bins(records, bins)
    ece = sum(
        (row["count"] / sample_count) * row["calibration_error"]
        for row in bin_rows
        if row["count"] > 0
    )
    suggested_threshold = None if sample_count < min_samples else _suggest_threshold(records)
    metadata = {
        "bin_count": bins,
        "min_samples": min_samples,
        "threshold_rule": (
            "none when sample_count is below min_samples; otherwise lowest score "
            "threshold with empirical precision >= 0.8 and at least 3 samples"
        ),
        "calibration_claim": "not_calibrated_without_sufficient_representative_outcomes",
    }
    return CalibrationReport(
        boundary_id=report_boundary,
        sample_count=sample_count,
        brier_score=brier_score,
        ece=ece,
        bins=bin_rows,
        warnings=warnings,
        suggested_threshold=suggested_threshold,
        limitations=limitations,
        metadata=metadata,
    )


def _truth(value: bool) -> float:
    return 1.0 if value else 0.0


def _common_boundary_id(records: list[CalibrationOutcome]) -> str:
    if not records:
        return "all"
    boundary_ids = sorted({item.boundary_id for item in records})
    return boundary_ids[0] if len(boundary_ids) == 1 else "multiple"


def _build_bins(records: list[CalibrationOutcome], bin_count: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index in range(bin_count):
        lower = index / bin_count
        upper = (index + 1) / bin_count
        if index == bin_count - 1:
            bucket = [item for item in records if lower <= item.score <= upper]
        else:
            bucket = [item for item in records if lower <= item.score < upper]
        count = len(bucket)
        if count:
            mean_score = sum(item.score for item in bucket) / count
            accuracy = sum(_truth(item.outcome) for item in bucket) / count
            calibration_error = abs(mean_score - accuracy)
        else:
            mean_score = None
            accuracy = None
            calibration_error = 0.0
        rows.append(
            {
                "bin": index,
                "lower": lower,
                "upper": upper,
                "count": count,
                "mean_score": mean_score,
                "accuracy": accuracy,
                "calibration_error": calibration_error,
            }
        )
    return rows


def _suggest_threshold(records: list[CalibrationOutcome]) -> float | None:
    candidates = sorted({item.score for item in records})
    best: float | None = None
    for threshold in candidates:
        selected = [item for item in records if item.score >= threshold]
        if len(selected) < 3:
            continue
        precision = sum(_truth(item.outcome) for item in selected) / len(selected)
        if precision >= 0.8:
            best = threshold
            break
    return best
