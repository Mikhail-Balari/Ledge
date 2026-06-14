"""AI-readable review packs for decision ledgers."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .canonical import canonical_json
from .event import DecisionEvent
from .exceptions import LedgerReviewPackError, LedgerStoreError
from .store import DecisionLedger
from .verifier import FAILED, LedgerVerificationResult, verify_ledger


REVIEW_PACK_SCHEMA_VERSION = "ledge.ai_review_pack.v1"
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
OPTIONAL_CORRELATION_FIELDS = (
    "trace_id",
    "span_id",
    "request_id",
    "actor_id_hash",
    "service_name",
    "environment",
)


@dataclass(frozen=True)
class LedgerAIReviewPack:
    """Machine-readable review contract for a decision ledger."""

    data: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return dict(self.data)

    def to_json(self) -> str:
        return canonical_json(self.to_dict())


def build_ai_review_pack(
    store_path: str | Path,
    manifest_path: str | Path | None = None,
    boundary_id: str | None = None,
) -> LedgerAIReviewPack:
    """Build a deterministic, safe review pack for AI or governance workflows."""

    store = Path(store_path)
    manifest = Path(manifest_path) if manifest_path is not None else None
    if not store.exists():
        raise LedgerReviewPackError("ledger store not found")

    verification = verify_ledger(store, manifest)
    events = _safe_read_events(store)
    events_in_scope = _filter_events(events, boundary_id) if events else []
    if verification.status == FAILED and not events:
        event_summaries: list[dict[str, Any]] = []
    else:
        event_summaries = [_event_summary(event) for event in events_in_scope]

    pack_data = {
        "review_schema": REVIEW_PACK_SCHEMA_VERSION,
        "generated_at_utc": _utc_now(),
        "source_ledger": str(store),
        "manifest_used": str(manifest) if manifest is not None else None,
        "boundary_filter": boundary_id,
        "ledger_status": verification.status,
        "events_checked": verification.events_checked,
        "events_in_scope": len(event_summaries),
        "decision_boundaries": sorted({event["boundary_id"] for event in event_summaries}),
        "integrity_summary": _integrity_summary(verification),
        "policy_results_count": _count_field(event_summaries, "policy_result"),
        "actions_count": _count_field(event_summaries, "action"),
        "warnings_count": sum(event["warnings_count"] for event in event_summaries),
        "critical_findings_count": len(verification.critical_findings),
        "findings_summary": [_finding_summary(finding.to_dict()) for finding in verification.findings],
        "recommended_review_focus": _recommended_review_focus(
            verification=verification,
            events=events_in_scope,
            event_summaries=event_summaries,
            manifest_provided=manifest is not None,
        ),
        "event_summaries": event_summaries,
        "limitations": _limitations(),
    }
    return LedgerAIReviewPack(pack_data)


def write_ai_review_pack(
    pack: LedgerAIReviewPack,
    path: str | Path,
    force: bool = False,
) -> None:
    """Write an AI review pack as one canonical JSON file."""

    out_path = Path(path)
    if out_path.exists() and not force:
        raise LedgerReviewPackError("review pack output already exists; use force to overwrite")
    if out_path.exists() and out_path.is_dir():
        raise LedgerReviewPackError("review pack output path is a directory")

    rendered = pack.to_json() + "\n"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = out_path.with_name(f".{out_path.name}.tmp")
    try:
        tmp_path.write_text(rendered, encoding="utf-8")
        tmp_path.replace(out_path)
    except OSError as exc:
        try:
            if tmp_path.exists():
                tmp_path.unlink()
        except OSError:
            pass
        raise LedgerReviewPackError("review pack could not be written") from exc


def _safe_read_events(store: Path) -> list[DecisionEvent]:
    try:
        return DecisionLedger(store).read_events()
    except LedgerStoreError:
        return []


def _filter_events(events: list[DecisionEvent], boundary_id: str | None) -> list[DecisionEvent]:
    if boundary_id is None:
        return list(events)
    return [event for event in events if event.boundary_id == boundary_id]


def _event_summary(event: DecisionEvent) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "event_id": event.event_id,
        "sequence": event.sequence,
        "timestamp_utc": event.timestamp_utc,
        "boundary_id": event.boundary_id,
        "boundary_version": event.boundary_version,
        "policy_hash": event.policy_hash,
        "evidence_hash": event.evidence_hash,
        "input_hash": event.input_hash,
        "output_hash": event.output_hash,
        "confidence_score": event.confidence_score,
        "policy_result": event.policy_result,
        "action": event.action,
        "warnings_count": len(event.warnings),
        "redaction_profile": event.redaction_profile,
        "previous_event_hash": event.previous_event_hash,
        "current_event_hash": event.current_event_hash,
    }
    for field in OPTIONAL_CORRELATION_FIELDS:
        value = getattr(event, field)
        if value is not None:
            summary[field] = value
    return summary


def _integrity_summary(verification: LedgerVerificationResult) -> dict[str, Any]:
    return {
        "chain_valid": verification.chain_valid,
        "manifest_valid": verification.manifest_valid,
        "schema_valid": verification.schema_valid,
        "redaction_posture_valid": verification.redaction_posture_valid,
        "first_event_hash": verification.first_event_hash,
        "last_event_hash": verification.last_event_hash,
    }


def _count_field(events: list[dict[str, Any]], field: str) -> dict[str, int]:
    counts = Counter(str(event[field]) for event in events)
    return dict(sorted(counts.items()))


def _finding_summary(finding: dict[str, Any]) -> dict[str, Any]:
    safe = dict(finding)
    field = safe.get("field")
    if isinstance(field, str) and any(part in RAW_FIELD_NAMES for part in field.split(",")):
        safe["field"] = "redacted_raw_field"
    return safe


def _recommended_review_focus(
    *,
    verification: LedgerVerificationResult,
    events: list[DecisionEvent],
    event_summaries: list[dict[str, Any]],
    manifest_provided: bool,
) -> list[str]:
    focus: list[str] = []
    if verification.critical_findings:
        focus.append("Review critical ledger integrity findings before relying on event summaries.")
    if not manifest_provided:
        focus.append("Provide and verify a ledger manifest to check event count and chain anchors.")

    blocked_count = sum(1 for event in events if event.policy_result == "block")
    escalated_count = sum(1 for event in events if event.policy_result == "escalate")
    warning_count = sum(len(event.warnings) for event in events)
    high_confidence_warning_count = sum(
        1 for event in events if event.confidence_score >= 0.8 and event.warnings
    )
    low_confidence_allowed_count = sum(
        1
        for event in events
        if event.policy_result in {"allow", "allow_with_warning"} and event.confidence_score < 0.5
    )
    if blocked_count:
        focus.append("Inspect blocked actions and confirm they were not executed downstream.")
    if escalated_count:
        focus.append("Inspect escalated actions and confirm human-review handoff behavior.")
    if high_confidence_warning_count:
        focus.append("Inspect high-confidence events that still carried warnings.")
    if low_confidence_allowed_count:
        focus.append("Inspect low-confidence allowed actions against the decision policy.")
    if warning_count:
        focus.append("Review event warnings by boundary, policy result, action, and evidence hash.")
    if event_summaries and not any(
        "trace_id" in event or "request_id" in event for event in event_summaries
    ):
        focus.append("Consider adding trace_id or request_id for easier cross-system review.")
    if not focus:
        focus.append("Review decision boundaries, evidence hashes, policy results, actions, warnings, and integrity status.")
    return focus


def _limitations() -> list[str]:
    return [
        "not compliance certification",
        "tamper-evident, not tamper-proof",
        "append-oriented local records, not immutable storage",
        "does not guarantee truth",
        "does not prevent hallucinations",
        "reviewing AI must not trust original AI output blindly",
        "review should inspect boundary, policy result, evidence hashes, action, warnings, and integrity status",
    ]


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
