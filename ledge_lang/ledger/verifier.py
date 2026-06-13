"""Verifier core for decision ledger integrity checks."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, ClassVar

from .canonical import canonical_json
from .event import DecisionEvent
from .exceptions import LedgerHashError, LedgerManifestError, LedgerValidationError
from .manifest import LedgerManifest


VERIFICATION_SCHEMA_VERSION = "ledge.ledger_verification.v1"
PASSED = "passed"
PASSED_WITH_WARNINGS = "passed_with_warnings"
FAILED = "failed"
INFO = "info"
WARNING = "warning"
CRITICAL = "critical"
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


@dataclass(frozen=True)
class LedgerFinding:
    """A stable machine-readable ledger verification finding."""

    severity: str
    code: str
    message: str
    line_number: int | None = None
    event_sequence: int | None = None
    event_id: str | None = None
    field: str | None = None

    def __post_init__(self) -> None:
        if self.severity not in {INFO, WARNING, CRITICAL}:
            raise ValueError("ledger finding severity is not supported")
        if not self.code:
            raise ValueError("ledger finding code is required")
        if not self.message:
            raise ValueError("ledger finding message is required")

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "severity": self.severity,
            "code": self.code,
            "message": self.message,
        }
        if self.line_number is not None:
            data["line_number"] = self.line_number
        if self.event_sequence is not None:
            data["event_sequence"] = self.event_sequence
        if self.event_id is not None:
            data["event_id"] = self.event_id
        if self.field is not None:
            data["field"] = self.field
        return data


@dataclass(frozen=True)
class LedgerVerificationResult:
    """Machine-readable and human-readable ledger verification result."""

    status: str
    ledger_path: str
    manifest_path: str | None
    events_checked: int
    first_event_hash: str | None
    last_event_hash: str | None
    chain_valid: bool
    manifest_valid: bool
    schema_valid: bool
    redaction_posture_valid: bool
    findings: tuple[LedgerFinding, ...]
    recommended_review_focus: tuple[str, ...]

    VERIFICATION_SCHEMA: ClassVar[str] = VERIFICATION_SCHEMA_VERSION

    @property
    def critical_findings(self) -> tuple[LedgerFinding, ...]:
        return tuple(finding for finding in self.findings if finding.severity == CRITICAL)

    @property
    def warnings(self) -> tuple[LedgerFinding, ...]:
        return tuple(finding for finding in self.findings if finding.severity == WARNING)

    def to_dict(self) -> dict[str, Any]:
        return {
            "verification_schema": VERIFICATION_SCHEMA_VERSION,
            "status": self.status,
            "ledger_path": self.ledger_path,
            "manifest_path": self.manifest_path,
            "events_checked": self.events_checked,
            "first_event_hash": self.first_event_hash,
            "last_event_hash": self.last_event_hash,
            "chain_valid": self.chain_valid,
            "manifest_valid": self.manifest_valid,
            "schema_valid": self.schema_valid,
            "redaction_posture_valid": self.redaction_posture_valid,
            "critical_findings": [finding.to_dict() for finding in self.critical_findings],
            "warnings": [finding.to_dict() for finding in self.warnings],
            "findings": [finding.to_dict() for finding in self.findings],
            "recommended_review_focus": list(self.recommended_review_focus),
            "limitations": [
                "tamper-evident, not tamper-proof",
                "audit review package, not compliance certification",
                "append-oriented local records, not immutable storage",
            ],
        }

    def to_json(self) -> str:
        return canonical_json(self.to_dict())

    def to_text(self) -> str:
        lines = [
            "Ledge ledger verification",
            f"Status: {self.status}",
            f"Ledger path: {self.ledger_path}",
            f"Manifest path: {self.manifest_path if self.manifest_path is not None else 'not provided'}",
            f"Events checked: {self.events_checked}",
            f"Chain valid: {str(self.chain_valid).lower()}",
            f"Manifest valid: {str(self.manifest_valid).lower()}",
            f"Schema valid: {str(self.schema_valid).lower()}",
            f"Redaction posture valid: {str(self.redaction_posture_valid).lower()}",
            f"First event hash: {self.first_event_hash if self.first_event_hash is not None else 'none'}",
            f"Last event hash: {self.last_event_hash if self.last_event_hash is not None else 'none'}",
        ]
        if self.findings:
            lines.append("Findings:")
            for finding in self.findings:
                location = _format_finding_location(finding)
                lines.append(f"- {finding.severity} {finding.code}{location}: {finding.message}")
        else:
            lines.append("Findings: none")
        if self.recommended_review_focus:
            lines.append("Recommended review focus:")
            for item in self.recommended_review_focus:
                lines.append(f"- {item}")
        lines.append("Limitations:")
        lines.append("- tamper-evident, not tamper-proof")
        lines.append("- audit review package, not compliance certification")
        lines.append("- append-oriented local records, not immutable storage")
        return "\n".join(lines)


class LedgerVerifier:
    """Verify local ledger JSONL and optional manifest integrity."""

    def verify(
        self,
        ledger_path: str | Path,
        manifest_path: str | Path | None = None,
    ) -> LedgerVerificationResult:
        ledger = Path(ledger_path)
        manifest = Path(manifest_path) if manifest_path is not None else None
        findings: list[LedgerFinding] = []
        events: list[DecisionEvent] = []
        chain_valid = True
        schema_valid = True
        redaction_posture_valid = True

        if not ledger.exists():
            findings.append(
                _finding(
                    CRITICAL,
                    "LEDGER_FILE_MISSING",
                    "Ledger file is missing.",
                )
            )
            return _result(ledger, manifest, events, findings, False, False, False, False)

        try:
            lines = ledger.read_text(encoding="utf-8").splitlines()
        except OSError:
            findings.append(
                _finding(
                    CRITICAL,
                    "LEDGER_FILE_UNREADABLE",
                    "Ledger file could not be read.",
                )
            )
            return _result(ledger, manifest, events, findings, False, False, False, False)

        seen_sequences: set[int] = set()
        previous_event: DecisionEvent | None = None
        for line_number, line in enumerate(lines, start=1):
            if not line.strip():
                findings.append(
                    _finding(
                        CRITICAL,
                        "LEDGER_BLANK_LINE",
                        "Ledger contains a blank line.",
                        line_number=line_number,
                    )
                )
                chain_valid = False
                schema_valid = False
                continue

            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                findings.append(
                    _finding(
                        CRITICAL,
                        "LEDGER_INVALID_JSON",
                        "Ledger line is not valid JSON.",
                        line_number=line_number,
                    )
                )
                chain_valid = False
                schema_valid = False
                continue

            if not isinstance(payload, dict):
                findings.append(
                    _finding(
                        CRITICAL,
                        "LEDGER_INVALID_EVENT_SCHEMA",
                        "Ledger line is not a JSON object.",
                        line_number=line_number,
                    )
                )
                chain_valid = False
                schema_valid = False
                continue

            raw_fields = sorted(set(payload) & RAW_FIELD_NAMES)
            if raw_fields:
                findings.append(
                    _finding(
                        CRITICAL,
                        "LEDGER_INVALID_EVENT_SCHEMA",
                        "Ledger event contains raw-looking fields.",
                        line_number=line_number,
                        event_sequence=_safe_sequence(payload),
                        event_id=_safe_event_id(payload),
                        field=",".join(raw_fields),
                    )
                )
                chain_valid = False
                schema_valid = False
                redaction_posture_valid = False
                continue

            try:
                event = DecisionEvent.from_dict(payload)
            except LedgerHashError:
                findings.append(
                    _finding(
                        CRITICAL,
                        "LEDGER_EVENT_HASH_MISMATCH",
                        "Ledger event hash does not match its canonical payload.",
                        line_number=line_number,
                        event_sequence=_safe_sequence(payload),
                        event_id=_safe_event_id(payload),
                    )
                )
                chain_valid = False
                continue
            except LedgerValidationError:
                code = _schema_failure_code(payload)
                findings.append(
                    _finding(
                        CRITICAL,
                        code,
                        _schema_failure_message(code),
                        line_number=line_number,
                        event_sequence=_safe_sequence(payload),
                        event_id=_safe_event_id(payload),
                        field=_schema_failure_field(code),
                    )
                )
                chain_valid = False
                schema_valid = False
                if code == "LEDGER_INVALID_EVENT_SCHEMA":
                    redaction_posture_valid = False
                continue

            if event.sequence in seen_sequences:
                findings.append(
                    _finding(
                        CRITICAL,
                        "LEDGER_DUPLICATE_SEQUENCE",
                        "Ledger contains a duplicate event sequence.",
                        line_number=line_number,
                        event_sequence=event.sequence,
                        event_id=event.event_id,
                        field="sequence",
                    )
                )
                chain_valid = False
            seen_sequences.add(event.sequence)

            if previous_event is None:
                if event.sequence != 1:
                    findings.append(
                        _finding(
                            CRITICAL,
                            "LEDGER_SEQUENCE_NOT_STARTING_AT_ONE",
                            "First ledger event sequence must be 1.",
                            line_number=line_number,
                            event_sequence=event.sequence,
                            event_id=event.event_id,
                            field="sequence",
                        )
                    )
                    chain_valid = False
                if event.previous_event_hash is not None:
                    findings.append(
                        _finding(
                            CRITICAL,
                            "LEDGER_PREVIOUS_HASH_MISMATCH",
                            "First ledger event must not have previous_event_hash.",
                            line_number=line_number,
                            event_sequence=event.sequence,
                            event_id=event.event_id,
                            field="previous_event_hash",
                        )
                    )
                    chain_valid = False
            else:
                expected_sequence = previous_event.sequence + 1
                if event.sequence != expected_sequence and event.sequence not in seen_sequences - {event.sequence}:
                    findings.append(
                        _finding(
                            CRITICAL,
                            "LEDGER_SEQUENCE_GAP",
                            "Ledger event sequence is not continuous.",
                            line_number=line_number,
                            event_sequence=event.sequence,
                            event_id=event.event_id,
                            field="sequence",
                        )
                    )
                    chain_valid = False
                if event.previous_event_hash is None:
                    findings.append(
                        _finding(
                            CRITICAL,
                            "LEDGER_PREVIOUS_HASH_MISSING",
                            "Ledger event is missing previous_event_hash.",
                            line_number=line_number,
                            event_sequence=event.sequence,
                            event_id=event.event_id,
                            field="previous_event_hash",
                        )
                    )
                    chain_valid = False
                elif event.previous_event_hash != previous_event.current_event_hash:
                    findings.append(
                        _finding(
                            CRITICAL,
                            "LEDGER_PREVIOUS_HASH_MISMATCH",
                            "Ledger event previous_event_hash does not match previous event.",
                            line_number=line_number,
                            event_sequence=event.sequence,
                            event_id=event.event_id,
                            field="previous_event_hash",
                        )
                    )
                    chain_valid = False

            events.append(event)
            previous_event = event

        manifest_valid = self._verify_manifest(manifest, ledger, events, findings)
        return _result(
            ledger,
            manifest,
            events,
            findings,
            chain_valid and not _has_critical(findings, prefix="LEDGER_"),
            manifest_valid,
            schema_valid,
            redaction_posture_valid,
        )

    def _verify_manifest(
        self,
        manifest_path: Path | None,
        ledger_path: Path,
        events: list[DecisionEvent],
        findings: list[LedgerFinding],
    ) -> bool:
        if manifest_path is None:
            findings.append(
                _finding(
                    WARNING,
                    "LEDGER_MANIFEST_NOT_PROVIDED",
                    "Ledger manifest was not provided; chain checks ran without manifest validation.",
                )
            )
            return False

        if not manifest_path.exists():
            findings.append(
                _finding(
                    CRITICAL,
                    "LEDGER_MANIFEST_FILE_MISSING",
                    "Ledger manifest file is missing.",
                )
            )
            return False

        try:
            payload = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest = LedgerManifest.from_dict(payload)
        except (json.JSONDecodeError, OSError, LedgerManifestError):
            findings.append(
                _finding(
                    CRITICAL,
                    "LEDGER_MANIFEST_INVALID",
                    "Ledger manifest is malformed or invalid.",
                )
            )
            return False

        valid = True
        first_event_hash = events[0].current_event_hash if events else None
        last_event_hash = events[-1].current_event_hash if events else None
        if manifest.event_count != len(events):
            findings.append(
                _finding(
                    CRITICAL,
                    "LEDGER_MANIFEST_EVENT_COUNT_MISMATCH",
                    "Ledger manifest event_count does not match ledger events checked.",
                    field="event_count",
                )
            )
            valid = False
        if manifest.first_event_hash != first_event_hash:
            findings.append(
                _finding(
                    CRITICAL,
                    "LEDGER_MANIFEST_FIRST_HASH_MISMATCH",
                    "Ledger manifest first_event_hash does not match ledger.",
                    field="first_event_hash",
                )
            )
            valid = False
        if manifest.last_event_hash != last_event_hash:
            findings.append(
                _finding(
                    CRITICAL,
                    "LEDGER_MANIFEST_LAST_HASH_MISMATCH",
                    "Ledger manifest last_event_hash does not match ledger.",
                    field="last_event_hash",
                )
            )
            valid = False
        if not _paths_compatible(manifest.ledger_path, ledger_path):
            findings.append(
                _finding(
                    CRITICAL,
                    "LEDGER_MANIFEST_LEDGER_PATH_MISMATCH",
                    "Ledger manifest ledger_path does not match verified ledger path.",
                    field="ledger_path",
                )
            )
            valid = False
        return valid


def verify_ledger(
    ledger_path: str | Path,
    manifest_path: str | Path | None = None,
) -> LedgerVerificationResult:
    return LedgerVerifier().verify(ledger_path, manifest_path)


def _result(
    ledger_path: Path,
    manifest_path: Path | None,
    events: list[DecisionEvent],
    findings: list[LedgerFinding],
    chain_valid: bool,
    manifest_valid: bool,
    schema_valid: bool,
    redaction_posture_valid: bool,
) -> LedgerVerificationResult:
    critical = [finding for finding in findings if finding.severity == CRITICAL]
    warnings = [finding for finding in findings if finding.severity == WARNING]
    if critical:
        status = FAILED
    elif warnings:
        status = PASSED_WITH_WARNINGS
    else:
        status = PASSED
    return LedgerVerificationResult(
        status=status,
        ledger_path=str(ledger_path),
        manifest_path=str(manifest_path) if manifest_path is not None else None,
        events_checked=len(events),
        first_event_hash=events[0].current_event_hash if events else None,
        last_event_hash=events[-1].current_event_hash if events else None,
        chain_valid=chain_valid,
        manifest_valid=manifest_valid,
        schema_valid=schema_valid and not _has_code(findings, "LEDGER_INVALID_EVENT_SCHEMA"),
        redaction_posture_valid=redaction_posture_valid,
        findings=tuple(findings),
        recommended_review_focus=tuple(_recommended_review_focus(critical, warnings)),
    )


def _finding(
    severity: str,
    code: str,
    message: str,
    *,
    line_number: int | None = None,
    event_sequence: int | None = None,
    event_id: str | None = None,
    field: str | None = None,
) -> LedgerFinding:
    return LedgerFinding(
        severity=severity,
        code=code,
        message=message,
        line_number=line_number,
        event_sequence=event_sequence,
        event_id=event_id,
        field=field,
    )


def _schema_failure_code(payload: dict[str, Any]) -> str:
    sequence = payload.get("sequence")
    previous_hash = payload.get("previous_event_hash")
    if isinstance(sequence, int) and not isinstance(sequence, bool) and sequence > 1 and previous_hash is None:
        return "LEDGER_PREVIOUS_HASH_MISSING"
    return "LEDGER_INVALID_EVENT_SCHEMA"


def _schema_failure_message(code: str) -> str:
    if code == "LEDGER_PREVIOUS_HASH_MISSING":
        return "Ledger event is missing previous_event_hash."
    return "Ledger event schema is invalid."


def _schema_failure_field(code: str) -> str | None:
    if code == "LEDGER_PREVIOUS_HASH_MISSING":
        return "previous_event_hash"
    return None


def _safe_sequence(payload: dict[str, Any]) -> int | None:
    value = payload.get("sequence")
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    return None


def _safe_event_id(payload: dict[str, Any]) -> str | None:
    value = payload.get("event_id")
    if isinstance(value, str):
        return value
    return None


def _format_finding_location(finding: LedgerFinding) -> str:
    parts = []
    if finding.line_number is not None:
        parts.append(f"line {finding.line_number}")
    if finding.event_sequence is not None:
        parts.append(f"sequence {finding.event_sequence}")
    if finding.event_id is not None:
        parts.append(f"event {finding.event_id}")
    if finding.field is not None:
        parts.append(f"field {finding.field}")
    if not parts:
        return ""
    return " (" + ", ".join(parts) + ")"


def _paths_compatible(manifest_ledger_path: str, ledger_path: Path) -> bool:
    if manifest_ledger_path == str(ledger_path):
        return True
    try:
        return Path(manifest_ledger_path).resolve() == ledger_path.resolve()
    except OSError:
        return False


def _has_code(findings: list[LedgerFinding], code: str) -> bool:
    return any(finding.code == code for finding in findings)


def _has_critical(findings: list[LedgerFinding], *, prefix: str) -> bool:
    return any(finding.severity == CRITICAL and finding.code.startswith(prefix) for finding in findings)


def _recommended_review_focus(
    critical: list[LedgerFinding],
    warnings: list[LedgerFinding],
) -> list[str]:
    if critical:
        return [
            "Review critical ledger integrity findings before relying on ledger output.",
            "Compare affected event hashes, sequence numbers, policy results, and actions.",
        ]
    if warnings:
        return [
            "Review warning findings before relying on the ledger summary.",
            "Provide a manifest when possible to check event count and chain anchors.",
        ]
    return [
        "Review decision boundary events, evidence hashes, policy results, actions, and warnings.",
    ]
