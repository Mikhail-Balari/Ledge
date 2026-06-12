"""Private SDK interoperability helpers for evidence containers."""

from __future__ import annotations

from dataclasses import dataclass, field
import math
from types import MappingProxyType
from typing import Any, Mapping

from .evidence import ConfidenceEvidence as SDKConfidenceEvidence

RAW_LIKE_METADATA_KEYS = {
    "api_key",
    "completion",
    "customer_data",
    "customer_text",
    "input",
    "model_output",
    "output",
    "password",
    "pii",
    "prompt",
    "raw",
    "raw_input",
    "raw_output",
    "response",
    "secret",
    "token",
    "user_input",
    "user_text",
}


@dataclass(frozen=True)
class EvidenceContext:
    """Normalized SDK-facing evidence metadata."""

    evidence_kind: str
    evidence_valid: bool
    evidence_score: float | None
    metadata: Mapping[str, Any] = field(default_factory=dict)
    warnings: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        safe_metadata = MappingProxyType(dict(self.metadata))
        object.__setattr__(self, "metadata", safe_metadata)
        object.__setattr__(self, "warnings", tuple(self.warnings))


def extract_evidence_context(evidence: object | None) -> EvidenceContext:
    """Return safe, normalized metadata and warnings for SDK decision results."""
    if evidence is None:
        return EvidenceContext(
            evidence_kind="none",
            evidence_valid=False,
            evidence_score=None,
        )

    if isinstance(evidence, SDKConfidenceEvidence):
        return _sdk_evidence_context(evidence)

    if _looks_like_audit_confidence_evidence(evidence):
        return _audit_confidence_evidence_context(evidence)

    return _unknown_evidence_context(evidence)


def _sdk_evidence_context(evidence: SDKConfidenceEvidence) -> EvidenceContext:
    warnings, warning_problem = _normalize_warnings(_safe_getattr(evidence, "warnings"))
    metadata_warnings: list[str] = []
    score, score_warning = _coerce_evidence_score(_safe_getattr(evidence, "score"))
    if score_warning:
        warnings = _dedupe((*warnings, score_warning))

    metadata: dict[str, Any] = {
        "evidence_kind": "sdk",
        "evidence_valid": score_warning is None,
        "evidence_warnings": list(warnings),
    }
    if score_warning is None:
        metadata["evidence_score"] = score

    source = _safe_getattr(evidence, "source")
    if isinstance(source, str):
        metadata["evidence_source"] = source

    signals, signal_warnings = _sanitize_optional_mapping(
        _safe_getattr(evidence, "signals"),
        field_name="evidence_signals",
    )
    if signals:
        metadata["evidence_signals"] = signals
    metadata_warnings.extend(signal_warnings)

    source_metadata, source_metadata_warnings = _sanitize_optional_mapping(
        _safe_getattr(evidence, "metadata"),
        field_name="evidence_metadata",
    )
    if source_metadata:
        metadata["evidence_metadata"] = source_metadata
    metadata_warnings.extend(source_metadata_warnings)

    if warning_problem:
        metadata_warnings.append("invalid_evidence_warnings")
    warnings = _dedupe((*warnings, *metadata_warnings))
    metadata["evidence_warnings"] = list(warnings)
    if metadata_warnings or score_warning:
        metadata["evidence_valid"] = False

    return EvidenceContext(
        evidence_kind="sdk",
        evidence_valid=bool(metadata["evidence_valid"]),
        evidence_score=score if score_warning is None else None,
        metadata=metadata,
        warnings=warnings,
    )


def _audit_confidence_evidence_context(evidence: object) -> EvidenceContext:
    warnings, warning_problem = _normalize_warnings(_safe_getattr(evidence, "warnings"))
    context_warnings: list[str] = []
    score, score_warning = _coerce_evidence_score(_safe_getattr(evidence, "score"))
    if score_warning:
        context_warnings.append(score_warning)

    evidence_hash = _safe_string(_safe_getattr(evidence, "evidence_hash"))
    if evidence_hash is None:
        evidence_hash = _compute_evidence_hash(evidence)
    if evidence_hash is None:
        context_warnings.append("evidence_hash_unavailable")

    source_metadata, source_metadata_warnings = _sanitize_optional_mapping(
        _safe_getattr(evidence, "metadata"),
        field_name="evidence_metadata",
    )
    context_warnings.extend(source_metadata_warnings)
    if warning_problem:
        context_warnings.append("invalid_evidence_warnings")

    warnings = _dedupe((*warnings, *context_warnings))
    evidence_valid = score_warning is None
    metadata: dict[str, Any] = {
        "evidence_kind": "confidence",
        "evidence_valid": evidence_valid,
        "evidence_id": _safe_string(_safe_getattr(evidence, "evidence_id")),
        "evidence_hash": evidence_hash,
        "evidence_boundary_id": _safe_string(_safe_getattr(evidence, "boundary_id")),
        "evidence_schema_version": _safe_string(_safe_getattr(evidence, "schema_version")),
        "evidence_policy_id": _safe_string(_safe_getattr(evidence, "policy_id")),
        "evidence_policy_hash": _safe_string(_safe_getattr(evidence, "policy_hash")),
        "evidence_input_hash": _safe_string(_safe_getattr(evidence, "input_hash")),
        "evidence_output_hash": _safe_string(_safe_getattr(evidence, "output_hash")),
        "evidence_redaction_applied": _safe_bool(
            _safe_getattr(evidence, "redaction_applied")
        ),
        "evidence_warnings": list(warnings),
    }
    if score_warning is None:
        metadata["evidence_score"] = score
    if source_metadata:
        metadata["evidence_metadata"] = source_metadata

    return EvidenceContext(
        evidence_kind="confidence",
        evidence_valid=evidence_valid,
        evidence_score=score if score_warning is None else None,
        metadata=metadata,
        warnings=warnings,
    )


def _unknown_evidence_context(evidence: object) -> EvidenceContext:
    warnings, warning_problem = _normalize_warnings(_safe_getattr(evidence, "warnings"))
    context_warnings = ["unknown_evidence_shape"]

    score = _safe_getattr(evidence, "score")
    if score is not None:
        _, score_warning = _coerce_evidence_score(score)
        if score_warning:
            context_warnings.append(score_warning)

    if warning_problem:
        context_warnings.append("invalid_evidence_warnings")

    metadata_warnings = _inspect_unknown_metadata(evidence)
    context_warnings.extend(metadata_warnings)

    warnings = _dedupe((*warnings, *context_warnings))
    metadata = {
        "evidence_kind": "unknown",
        "evidence_valid": False,
        "evidence_type": type(evidence).__name__,
        "evidence_warnings": list(warnings),
    }
    return EvidenceContext(
        evidence_kind="unknown",
        evidence_valid=False,
        evidence_score=None,
        metadata=metadata,
        warnings=warnings,
    )


def _looks_like_audit_confidence_evidence(evidence: object) -> bool:
    return all(
        _safe_getattr(evidence, name) is not None
        for name in ("evidence_id", "boundary_id", "schema_version")
    )


def _compute_evidence_hash(evidence: object) -> str | None:
    compute_hash = _safe_getattr(evidence, "compute_hash")
    if not callable(compute_hash):
        return None
    try:
        computed = compute_hash()
    except Exception:
        return None
    return computed if isinstance(computed, str) else None


def _safe_getattr(value: object, name: str) -> Any:
    try:
        return getattr(value, name)
    except Exception:
        return None


def _coerce_evidence_score(value: object) -> tuple[float | None, str | None]:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None, "invalid_evidence_score"
    coerced = float(value)
    if not math.isfinite(coerced) or coerced < 0.0 or coerced > 1.0:
        return None, "invalid_evidence_score"
    return coerced, None


def _normalize_warnings(value: object) -> tuple[tuple[str, ...], bool]:
    if value is None:
        return (), False
    if not isinstance(value, (list, tuple)):
        return (), True

    normalized: list[str] = []
    invalid = False
    for item in value:
        if isinstance(item, str):
            normalized.append(item)
        else:
            invalid = True
    return _dedupe(normalized), invalid


def _sanitize_optional_mapping(
    value: object,
    *,
    field_name: str,
) -> tuple[dict[str, Any], list[str]]:
    if value is None:
        return {}, []
    if not isinstance(value, dict):
        return {}, ["invalid_evidence_metadata"]

    sanitized, redacted = _sanitize_json_like(value)
    warnings = ["unsafe_evidence_metadata_redacted"] if redacted else []
    if isinstance(sanitized, dict):
        return sanitized, warnings
    return {field_name: sanitized}, warnings


def _sanitize_json_like(value: object, *, key_name: str | None = None) -> tuple[Any, bool]:
    if key_name is not None and key_name.lower() in RAW_LIKE_METADATA_KEYS:
        return "[redacted]", True

    if value is None or isinstance(value, (str, bool)):
        return value, False
    if isinstance(value, int) and not isinstance(value, bool):
        return value, False
    if isinstance(value, float):
        if math.isfinite(value):
            return value, False
        return "[redacted]", True
    if isinstance(value, list):
        items: list[Any] = []
        redacted = False
        for item in value:
            safe_item, item_redacted = _sanitize_json_like(item)
            items.append(safe_item)
            redacted = redacted or item_redacted
        return items, redacted
    if isinstance(value, dict):
        result: dict[str, Any] = {}
        redacted = False
        for key, item in value.items():
            if not isinstance(key, str):
                redacted = True
                continue
            safe_item, item_redacted = _sanitize_json_like(item, key_name=key)
            result[key] = safe_item
            redacted = redacted or item_redacted
        return result, redacted
    return "[redacted]", True


def _inspect_unknown_metadata(evidence: object) -> list[str]:
    metadata = _safe_getattr(evidence, "metadata")
    if metadata is None:
        return []
    if not isinstance(metadata, dict):
        return ["invalid_evidence_metadata"]
    _, redacted = _sanitize_json_like(metadata)
    return ["unsafe_evidence_metadata_redacted"] if redacted else []


def _safe_string(value: object) -> str | None:
    return value if isinstance(value, str) else None


def _safe_bool(value: object) -> bool | None:
    return value if isinstance(value, bool) else None


def _dedupe(values: tuple[str, ...] | list[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    deduped: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            deduped.append(value)
    return tuple(deduped)
