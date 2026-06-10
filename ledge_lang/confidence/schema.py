"""Schema validation evidence helpers."""

from __future__ import annotations

import json
from typing import Any

from .evidence import ConfidenceEvidence, EvidenceSource
from .exceptions import SchemaEvidenceError
from .redaction import hash_output

TYPE_MAP = {
    "str": str,
    "int": int,
    "float": float,
    "bool": bool,
    "dict": dict,
    "list": list,
}


def evaluate_schema(
    raw_output: str | dict[str, Any],
    required_fields: list[str] | None = None,
    expected_types: dict[str, str] | None = None,
    critical_fields: list[str] | None = None,
    boundary_id: str = "unknown",
) -> ConfidenceEvidence:
    """Evaluate simple JSON/object shape and return audit-ready evidence."""
    required_fields = list(required_fields or [])
    expected_types = dict(expected_types or {})
    critical_fields = list(critical_fields or [])
    _validate_type_specs(expected_types)

    warnings: list[str] = []
    details: dict[str, Any] = {
        "required_fields": required_fields,
        "expected_types": expected_types,
        "critical_fields": critical_fields,
    }
    parsed: dict[str, Any] | None = None
    output_hash = hash_output(raw_output)

    if isinstance(raw_output, str):
        try:
            loaded = json.loads(raw_output)
        except json.JSONDecodeError as exc:
            warnings.append("schema_validation_failed")
            details["error"] = f"invalid JSON: {exc.msg}"
            return _schema_evidence(
                boundary_id=boundary_id,
                score=0.0,
                status="failed",
                warnings=warnings,
                details=details,
                output_hash=output_hash,
            )
        if not isinstance(loaded, dict):
            warnings.append("schema_validation_failed")
            details["error"] = "JSON output must be an object"
            return _schema_evidence(
                boundary_id=boundary_id,
                score=0.0,
                status="failed",
                warnings=warnings,
                details=details,
                output_hash=output_hash,
            )
        parsed = loaded
    elif isinstance(raw_output, dict):
        parsed = dict(raw_output)
    else:
        warnings.append("schema_validation_failed")
        details["error"] = "raw_output must be a JSON string or dictionary"
        return _schema_evidence(
            boundary_id=boundary_id,
            score=0.0,
            status="failed",
            warnings=warnings,
            details=details,
            output_hash=output_hash,
        )

    missing_required = [field for field in required_fields if field not in parsed]
    missing_critical = [field for field in critical_fields if field not in parsed]
    type_mismatches: list[dict[str, str]] = []

    if missing_required:
        warnings.append("required_field_missing")
        details["missing_required_fields"] = missing_required
    if missing_critical:
        warnings.append("critical_field_missing")
        details["missing_critical_fields"] = missing_critical

    for field, type_name in expected_types.items():
        if field not in parsed:
            continue
        if not _matches_expected_type(parsed[field], type_name):
            type_mismatches.append(
                {
                    "field": field,
                    "expected": type_name,
                    "actual": type(parsed[field]).__name__,
                }
            )

    if type_mismatches:
        warnings.append("type_mismatch")
        details["type_mismatches"] = type_mismatches

    score = 1.0
    status = "passed"
    if missing_critical or type_mismatches:
        score = 0.0
        status = "failed"
    elif missing_required:
        score = 0.5
        status = "warning"

    return _schema_evidence(
        boundary_id=boundary_id,
        score=score,
        status=status,
        warnings=warnings,
        details=details,
        output_hash=output_hash,
    )


def _validate_type_specs(expected_types: dict[str, str]) -> None:
    for field, type_name in expected_types.items():
        if type_name not in TYPE_MAP:
            allowed = ", ".join(sorted(TYPE_MAP))
            raise SchemaEvidenceError(
                f"invalid expected type for {field!r}: {type_name!r}; expected one of {allowed}"
            )


def _matches_expected_type(value: Any, type_name: str) -> bool:
    expected = TYPE_MAP[type_name]
    if type_name == "int":
        return isinstance(value, int) and not isinstance(value, bool)
    if type_name == "float":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    return isinstance(value, expected)


def _schema_evidence(
    boundary_id: str,
    score: float,
    status: str,
    warnings: list[str],
    details: dict[str, Any],
    output_hash: str,
) -> ConfidenceEvidence:
    source = EvidenceSource(
        source_type="schema_validation",
        status=status,
        score=score,
        impact="hard_gate" if score == 0.0 else "validation_signal",
        warnings=warnings,
        details=details,
        metadata={"raw_output_stored": False},
    )
    return ConfidenceEvidence(
        evidence_id=f"{boundary_id}:schema_validation",
        boundary_id=boundary_id,
        score=score,
        sources=[source],
        warnings=warnings,
        output_hash=output_hash,
        redaction_applied=True,
        redaction_strategy="hash_only",
        metadata={"raw_output_stored": False},
    ).with_hash()
