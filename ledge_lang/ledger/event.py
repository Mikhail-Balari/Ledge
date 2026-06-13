"""DecisionEvent model for semantic AI decision boundary ledger events."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Any, ClassVar

from .canonical import canonical_json
from .exceptions import LedgerHashError, LedgerValidationError
from .hashing import compute_event_hash, verify_event_hash


SCHEMA_VERSION = "ledge.decision_event.v1"
ALLOWED_POLICY_RESULTS = frozenset({"allow", "allow_with_warning", "block", "escalate"})
ALLOWED_REDACTION_PROFILES = frozenset({"hash_only", "redacted_summary", "external_reference"})
SHA256_HEX_RE = re.compile(r"^[0-9a-f]{64}$")
UTC_TIMESTAMP_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$"
)

REQUIRED_FIELDS = (
    "schema_version",
    "event_id",
    "sequence",
    "timestamp_utc",
    "boundary_id",
    "boundary_version",
    "policy_hash",
    "evidence_hash",
    "input_hash",
    "output_hash",
    "confidence_score",
    "action",
    "policy_result",
    "warnings",
    "redaction_profile",
    "previous_event_hash",
    "current_event_hash",
)
OPTIONAL_CORRELATION_FIELDS = (
    "trace_id",
    "span_id",
    "request_id",
    "actor_id_hash",
    "service_name",
    "environment",
)
RAW_FIELD_NAMES = frozenset(
    {
        "input",
        "output",
        "raw_input",
        "raw_output",
        "prompt",
        "completion",
        "messages",
        "response",
        "payload",
    }
)
ALL_FIELDS = frozenset(REQUIRED_FIELDS + OPTIONAL_CORRELATION_FIELDS)


@dataclass(frozen=True)
class DecisionEvent:
    """A canonical, hash-linked decision boundary event."""

    schema_version: str
    event_id: str
    sequence: int
    timestamp_utc: str
    boundary_id: str
    boundary_version: str
    policy_hash: str
    evidence_hash: str
    input_hash: str
    output_hash: str
    confidence_score: float
    action: str
    policy_result: str
    warnings: tuple[str, ...]
    redaction_profile: str
    previous_event_hash: str | None
    current_event_hash: str
    trace_id: str | None = None
    span_id: str | None = None
    request_id: str | None = None
    actor_id_hash: str | None = None
    service_name: str | None = None
    environment: str | None = None

    SCHEMA_VERSION: ClassVar[str] = SCHEMA_VERSION

    @classmethod
    def create(
        cls,
        *,
        event_id: str,
        sequence: int,
        timestamp_utc: str,
        boundary_id: str,
        boundary_version: str,
        policy_hash: str,
        evidence_hash: str,
        input_hash: str,
        output_hash: str,
        confidence_score: float,
        action: str,
        policy_result: str,
        warnings: list[str] | None = None,
        redaction_profile: str = "hash_only",
        previous_event_hash: str | None = None,
        trace_id: str | None = None,
        span_id: str | None = None,
        request_id: str | None = None,
        actor_id_hash: str | None = None,
        service_name: str | None = None,
        environment: str | None = None,
    ) -> "DecisionEvent":
        payload = {
            "schema_version": SCHEMA_VERSION,
            "event_id": event_id,
            "sequence": sequence,
            "timestamp_utc": timestamp_utc,
            "boundary_id": boundary_id,
            "boundary_version": boundary_version,
            "policy_hash": policy_hash,
            "evidence_hash": evidence_hash,
            "input_hash": input_hash,
            "output_hash": output_hash,
            "confidence_score": confidence_score,
            "action": action,
            "policy_result": policy_result,
            "warnings": list(warnings or []),
            "redaction_profile": redaction_profile,
            "previous_event_hash": previous_event_hash,
        }
        optional_values = {
            "trace_id": trace_id,
            "span_id": span_id,
            "request_id": request_id,
            "actor_id_hash": actor_id_hash,
            "service_name": service_name,
            "environment": environment,
        }
        payload.update({key: value for key, value in optional_values.items() if value is not None})
        _validate_payload(payload, require_current_hash=False)
        payload["current_event_hash"] = compute_event_hash(payload)
        return cls._from_validated_payload(payload)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DecisionEvent":
        if not isinstance(data, dict):
            raise LedgerValidationError("decision event must be a dictionary")
        payload = dict(data)
        _validate_payload(payload, require_current_hash=True)
        if not verify_event_hash(payload):
            raise LedgerHashError("decision event current_event_hash does not match payload")
        return cls._from_validated_payload(payload)

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "schema_version": self.schema_version,
            "event_id": self.event_id,
            "sequence": self.sequence,
            "timestamp_utc": self.timestamp_utc,
            "boundary_id": self.boundary_id,
            "boundary_version": self.boundary_version,
            "policy_hash": self.policy_hash,
            "evidence_hash": self.evidence_hash,
            "input_hash": self.input_hash,
            "output_hash": self.output_hash,
            "confidence_score": self.confidence_score,
            "action": self.action,
            "policy_result": self.policy_result,
            "warnings": list(self.warnings),
            "redaction_profile": self.redaction_profile,
            "previous_event_hash": self.previous_event_hash,
            "current_event_hash": self.current_event_hash,
        }
        for field in OPTIONAL_CORRELATION_FIELDS:
            value = getattr(self, field)
            if value is not None:
                data[field] = value
        return data

    def to_canonical_json(self) -> str:
        return canonical_json(self.to_dict())

    def verify_hash(self) -> bool:
        return verify_event_hash(self.to_dict())

    @classmethod
    def _from_validated_payload(cls, payload: dict[str, Any]) -> "DecisionEvent":
        return cls(
            schema_version=payload["schema_version"],
            event_id=payload["event_id"],
            sequence=payload["sequence"],
            timestamp_utc=payload["timestamp_utc"],
            boundary_id=payload["boundary_id"],
            boundary_version=payload["boundary_version"],
            policy_hash=payload["policy_hash"],
            evidence_hash=payload["evidence_hash"],
            input_hash=payload["input_hash"],
            output_hash=payload["output_hash"],
            confidence_score=payload["confidence_score"],
            action=payload["action"],
            policy_result=payload["policy_result"],
            warnings=tuple(payload["warnings"]),
            redaction_profile=payload["redaction_profile"],
            previous_event_hash=payload["previous_event_hash"],
            current_event_hash=payload["current_event_hash"],
            trace_id=payload.get("trace_id"),
            span_id=payload.get("span_id"),
            request_id=payload.get("request_id"),
            actor_id_hash=payload.get("actor_id_hash"),
            service_name=payload.get("service_name"),
            environment=payload.get("environment"),
        )


def _validate_payload(payload: dict[str, Any], *, require_current_hash: bool) -> None:
    unknown_fields = set(payload) - ALL_FIELDS
    if unknown_fields:
        raw_fields = sorted(unknown_fields & RAW_FIELD_NAMES)
        if raw_fields:
            raise LedgerValidationError(f"raw fields are not allowed in decision events: {raw_fields}")
        raise LedgerValidationError(f"unknown decision event fields: {sorted(unknown_fields)}")

    for field in REQUIRED_FIELDS:
        if field == "current_event_hash" and not require_current_hash:
            continue
        if field not in payload:
            raise LedgerValidationError(f"missing required decision event field: {field}")

    if payload.get("schema_version") != SCHEMA_VERSION:
        raise LedgerValidationError("unsupported decision event schema_version")

    _require_non_empty_string(payload.get("event_id"), "event_id")
    _require_sequence(payload.get("sequence"))
    _require_utc_timestamp(payload.get("timestamp_utc"))
    _require_non_empty_string(payload.get("boundary_id"), "boundary_id")
    _require_non_empty_string(payload.get("boundary_version"), "boundary_version")
    _require_non_empty_string(payload.get("policy_hash"), "policy_hash")
    _require_non_empty_string(payload.get("evidence_hash"), "evidence_hash")
    _require_non_empty_string(payload.get("input_hash"), "input_hash")
    _require_non_empty_string(payload.get("output_hash"), "output_hash")
    _require_confidence_score(payload.get("confidence_score"))
    _require_non_empty_string(payload.get("action"), "action")
    _require_policy_result(payload.get("policy_result"))
    _require_warnings(payload.get("warnings"))
    _require_redaction_profile(payload.get("redaction_profile"))
    _require_previous_hash(payload.get("previous_event_hash"), payload["sequence"])
    if require_current_hash:
        _require_hash(payload.get("current_event_hash"), "current_event_hash")

    for field in OPTIONAL_CORRELATION_FIELDS:
        value = payload.get(field)
        if value is not None and not isinstance(value, str):
            raise LedgerValidationError(f"{field} must be a string when present")

    canonical_json(
        {
            key: value
            for key, value in payload.items()
            if require_current_hash or key != "current_event_hash"
        }
    )


def _require_non_empty_string(value: Any, field: str) -> None:
    if not isinstance(value, str) or not value:
        raise LedgerValidationError(f"{field} must be a non-empty string")


def _require_sequence(value: Any) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise LedgerValidationError("sequence must be an integer >= 1")


def _require_utc_timestamp(value: Any) -> None:
    if not isinstance(value, str) or not UTC_TIMESTAMP_RE.match(value):
        raise LedgerValidationError("timestamp_utc must be a UTC timestamp ending in Z")


def _require_confidence_score(value: Any) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise LedgerValidationError("confidence_score must be a finite number in [0.0, 1.0]")
    coerced = float(value)
    if not math.isfinite(coerced) or coerced < 0.0 or coerced > 1.0:
        raise LedgerValidationError("confidence_score must be a finite number in [0.0, 1.0]")


def _require_policy_result(value: Any) -> None:
    if value not in ALLOWED_POLICY_RESULTS:
        raise LedgerValidationError("policy_result is not allowed")


def _require_warnings(value: Any) -> None:
    if not isinstance(value, list):
        raise LedgerValidationError("warnings must be a list of strings")
    for warning in value:
        if not isinstance(warning, str):
            raise LedgerValidationError("warnings must be a list of strings")


def _require_redaction_profile(value: Any) -> None:
    if value not in ALLOWED_REDACTION_PROFILES:
        raise LedgerValidationError("redaction_profile is not allowed")


def _require_previous_hash(value: Any, sequence: int) -> None:
    if sequence == 1 and value is None:
        return
    if sequence > 1 and value is None:
        raise LedgerValidationError("previous_event_hash is required for sequence > 1")
    _require_hash(value, "previous_event_hash")


def _require_hash(value: Any, field: str) -> None:
    if not isinstance(value, str) or not SHA256_HEX_RE.match(value):
        raise LedgerValidationError(f"{field} must be a lowercase SHA-256 hex string")
