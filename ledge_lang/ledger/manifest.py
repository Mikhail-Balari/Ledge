"""Local manifest summaries for decision ledger files."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, ClassVar

from ledge_lang._version import __version__

from .canonical import canonical_json
from .event import DecisionEvent
from .exceptions import LedgerManifestError
from .store import DecisionLedger


MANIFEST_SCHEMA_VERSION = "ledge.ledger_manifest.v1"
SHA256_HEX_RE = re.compile(r"^[0-9a-f]{64}$")
UTC_TIMESTAMP_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$"
)
MANIFEST_FIELDS = frozenset(
    {
        "schema_version",
        "ledger_path",
        "event_count",
        "first_event_hash",
        "last_event_hash",
        "created_at_utc",
        "updated_at_utc",
        "ledge_version",
    }
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


@dataclass(frozen=True)
class LedgerManifest:
    """A local summary for a decision ledger file."""

    schema_version: str
    ledger_path: str
    event_count: int
    first_event_hash: str | None
    last_event_hash: str | None
    created_at_utc: str
    updated_at_utc: str
    ledge_version: str

    SCHEMA_VERSION: ClassVar[str] = MANIFEST_SCHEMA_VERSION

    @classmethod
    def from_events(
        cls,
        *,
        ledger_path: str | Path,
        events: list[DecisionEvent],
        created_at_utc: str | None = None,
        updated_at_utc: str | None = None,
        ledge_version: str = __version__,
    ) -> "LedgerManifest":
        if not isinstance(events, list):
            raise LedgerManifestError("manifest events must be a list")
        for event in events:
            if not isinstance(event, DecisionEvent):
                raise LedgerManifestError("manifest events must contain DecisionEvent values")

        now = _utc_now()
        first_event_hash = events[0].current_event_hash if events else None
        last_event_hash = events[-1].current_event_hash if events else None
        payload = {
            "schema_version": MANIFEST_SCHEMA_VERSION,
            "ledger_path": str(ledger_path),
            "event_count": len(events),
            "first_event_hash": first_event_hash,
            "last_event_hash": last_event_hash,
            "created_at_utc": created_at_utc or now,
            "updated_at_utc": updated_at_utc or now,
            "ledge_version": ledge_version,
        }
        _validate_manifest_payload(payload)
        return cls(**payload)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LedgerManifest":
        if not isinstance(data, dict):
            raise LedgerManifestError("ledger manifest must be a dictionary")
        payload = dict(data)
        _validate_manifest_payload(payload)
        return cls(**payload)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "ledger_path": self.ledger_path,
            "event_count": self.event_count,
            "first_event_hash": self.first_event_hash,
            "last_event_hash": self.last_event_hash,
            "created_at_utc": self.created_at_utc,
            "updated_at_utc": self.updated_at_utc,
            "ledge_version": self.ledge_version,
        }

    def to_canonical_json(self) -> str:
        return canonical_json(self.to_dict())


def build_manifest(ledger: DecisionLedger) -> LedgerManifest:
    if not isinstance(ledger, DecisionLedger):
        raise LedgerManifestError("build_manifest requires a DecisionLedger")
    return LedgerManifest.from_events(ledger_path=ledger.path, events=ledger.read_events())


def write_manifest(manifest: LedgerManifest, path: str | Path) -> None:
    if not isinstance(manifest, LedgerManifest):
        raise LedgerManifestError("write_manifest requires a LedgerManifest")
    manifest_path = Path(path)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(manifest.to_canonical_json() + "\n", encoding="utf-8")


def read_manifest(path: str | Path) -> LedgerManifest:
    manifest_path = Path(path)
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise LedgerManifestError("ledger manifest contains malformed JSON") from exc
    except OSError as exc:
        raise LedgerManifestError("ledger manifest could not be read") from exc
    return LedgerManifest.from_dict(payload)


def _validate_manifest_payload(payload: dict[str, Any]) -> None:
    unknown_fields = set(payload) - MANIFEST_FIELDS
    if unknown_fields:
        raw_fields = sorted(unknown_fields & RAW_FIELD_NAMES)
        if raw_fields:
            raise LedgerManifestError(f"raw fields are not allowed in ledger manifests: {raw_fields}")
        raise LedgerManifestError(f"unknown ledger manifest fields: {sorted(unknown_fields)}")

    for field in MANIFEST_FIELDS:
        if field not in payload:
            raise LedgerManifestError(f"missing ledger manifest field: {field}")

    if payload["schema_version"] != MANIFEST_SCHEMA_VERSION:
        raise LedgerManifestError("unsupported ledger manifest schema_version")
    _require_non_empty_string(payload["ledger_path"], "ledger_path")
    _require_event_count(payload["event_count"])
    _require_optional_hash(payload["first_event_hash"], "first_event_hash")
    _require_optional_hash(payload["last_event_hash"], "last_event_hash")
    _require_utc_timestamp(payload["created_at_utc"], "created_at_utc")
    _require_utc_timestamp(payload["updated_at_utc"], "updated_at_utc")
    _require_non_empty_string(payload["ledge_version"], "ledge_version")

    if payload["event_count"] == 0:
        if payload["first_event_hash"] is not None or payload["last_event_hash"] is not None:
            raise LedgerManifestError("empty ledger manifest must not include event hashes")
    elif payload["first_event_hash"] is None or payload["last_event_hash"] is None:
        raise LedgerManifestError("non-empty ledger manifest requires first and last event hashes")

    canonical_json(payload)


def _require_non_empty_string(value: Any, field: str) -> None:
    if not isinstance(value, str) or not value:
        raise LedgerManifestError(f"{field} must be a non-empty string")


def _require_event_count(value: Any) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise LedgerManifestError("event_count must be an integer >= 0")


def _require_optional_hash(value: Any, field: str) -> None:
    if value is None:
        return
    if not isinstance(value, str) or not SHA256_HEX_RE.match(value):
        raise LedgerManifestError(f"{field} must be a lowercase SHA-256 hex string when present")


def _require_utc_timestamp(value: Any, field: str) -> None:
    if not isinstance(value, str) or not UTC_TIMESTAMP_RE.match(value):
        raise LedgerManifestError(f"{field} must be a UTC timestamp ending in Z")


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
