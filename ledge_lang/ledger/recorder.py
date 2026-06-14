"""SDK-facing helpers for recording decision events into a local ledger."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from .event import ALLOWED_REDACTION_PROFILES, DecisionEvent
from .exceptions import LedgerStoreError, LedgerValidationError
from .store import DecisionLedger


@dataclass(frozen=True)
class LedgerRecordContext:
    """Stable context shared by decision events recorded for one boundary."""

    boundary_id: str
    boundary_version: str
    policy_hash: str
    redaction_profile: str = "hash_only"
    trace_id: str | None = None
    span_id: str | None = None
    request_id: str | None = None
    actor_id_hash: str | None = None
    service_name: str | None = None
    environment: str | None = None

    def __post_init__(self) -> None:
        _require_non_empty_string(self.boundary_id, "boundary_id")
        _require_non_empty_string(self.boundary_version, "boundary_version")
        _require_non_empty_string(self.policy_hash, "policy_hash")
        if self.redaction_profile not in ALLOWED_REDACTION_PROFILES:
            raise LedgerValidationError("redaction_profile is not allowed")
        for field in (
            "trace_id",
            "span_id",
            "request_id",
            "actor_id_hash",
            "service_name",
            "environment",
        ):
            value = getattr(self, field)
            if value is not None and not isinstance(value, str):
                raise LedgerValidationError(f"{field} must be a string when present")


class LedgerRecorder:
    """Append semantic decision events without manually managing ledger linkage."""

    def __init__(
        self,
        ledger: DecisionLedger | str | Path,
        context: LedgerRecordContext,
        *,
        initialize: bool = False,
    ) -> None:
        self.ledger = ledger if isinstance(ledger, DecisionLedger) else DecisionLedger(ledger)
        if not isinstance(context, LedgerRecordContext):
            raise LedgerValidationError("ledger recorder context must be a LedgerRecordContext")
        self.context = context

        if self.ledger.exists():
            self.ledger.read_events()
        elif initialize:
            self.ledger.initialize()
        else:
            raise LedgerStoreError("ledger store not found; initialize the ledger before recording")

    def record(
        self,
        *,
        event_id: str | None = None,
        timestamp_utc: str | None = None,
        evidence_hash: str,
        input_hash: str,
        output_hash: str,
        confidence_score: float,
        action: str,
        policy_result: str,
        warnings: list[str] | None = None,
    ) -> DecisionEvent:
        """Create, append, and return one validated decision event."""

        event = DecisionEvent.create(
            event_id=event_id or _new_event_id(),
            sequence=self.ledger.next_sequence(),
            timestamp_utc=timestamp_utc or _utc_now(),
            boundary_id=self.context.boundary_id,
            boundary_version=self.context.boundary_version,
            policy_hash=self.context.policy_hash,
            evidence_hash=evidence_hash,
            input_hash=input_hash,
            output_hash=output_hash,
            confidence_score=confidence_score,
            action=action,
            policy_result=policy_result,
            warnings=list(warnings or []),
            redaction_profile=self.context.redaction_profile,
            previous_event_hash=self.ledger.expected_previous_hash(),
            trace_id=self.context.trace_id,
            span_id=self.context.span_id,
            request_id=self.context.request_id,
            actor_id_hash=self.context.actor_id_hash,
            service_name=self.context.service_name,
            environment=self.context.environment,
        )
        self.ledger.append(event)
        return event


def record_decision_event(
    ledger: DecisionLedger | str | Path,
    context: LedgerRecordContext,
    *,
    evidence_hash: str,
    input_hash: str,
    output_hash: str,
    confidence_score: float,
    action: str,
    policy_result: str,
    warnings: list[str] | None = None,
    event_id: str | None = None,
    timestamp_utc: str | None = None,
    initialize: bool = False,
) -> DecisionEvent:
    """Record one decision event using a short functional API."""

    recorder = LedgerRecorder(ledger, context, initialize=initialize)
    return recorder.record(
        event_id=event_id,
        timestamp_utc=timestamp_utc,
        evidence_hash=evidence_hash,
        input_hash=input_hash,
        output_hash=output_hash,
        confidence_score=confidence_score,
        action=action,
        policy_result=policy_result,
        warnings=warnings,
    )


def _require_non_empty_string(value: Any, field: str) -> None:
    if not isinstance(value, str) or not value:
        raise LedgerValidationError(f"{field} must be a non-empty string")


def _new_event_id() -> str:
    return f"evt_{uuid4().hex}"


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
