"""Local audit review export packages for decision ledgers."""

from __future__ import annotations

import shutil
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .canonical import canonical_json
from .event import DecisionEvent
from .exceptions import LedgerExportError, LedgerManifestError, LedgerStoreError
from .manifest import LedgerManifest, build_manifest, read_manifest
from .store import DecisionLedger
from .verifier import LedgerVerificationResult, verify_ledger


EXPORT_SUMMARY_SCHEMA_VERSION = "ledge.ledger_review_export.v1"
EXPORT_FILES = (
    "ledger_events.jsonl",
    "ledger_manifest.json",
    "verification_report.json",
    "verification_report.md",
    "decision_summary.json",
    "README.md",
)


@dataclass(frozen=True)
class LedgerExportResult:
    """Summary of a local audit review package export."""

    output_dir: str
    events_exported: int
    verification_status: str
    boundary_filter: str | None
    files: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "output_dir": self.output_dir,
            "events_exported": self.events_exported,
            "verification_status": self.verification_status,
            "boundary_filter": self.boundary_filter,
            "files": list(self.files),
        }


def export_ledger_review_package(
    store_path: str | Path,
    out_dir: str | Path,
    manifest_path: str | Path | None = None,
    boundary_id: str | None = None,
    force: bool = False,
) -> LedgerExportResult:
    """Write a local audit review package for a verified decision ledger."""

    store = Path(store_path)
    output = Path(out_dir)
    manifest = Path(manifest_path) if manifest_path is not None else None

    if output.exists() and not output.is_dir():
        raise LedgerExportError("output path exists and is not a directory")
    if output.exists() and any(output.iterdir()) and not force:
        raise LedgerExportError("output directory already exists and is not empty; use force to overwrite")

    verification = verify_ledger(store, manifest)
    if verification.status == "failed":
        raise LedgerExportError("ledger verification failed; refusing to export review package")

    ledger = DecisionLedger(store)
    try:
        events = ledger.read_events()
    except LedgerStoreError as exc:
        raise LedgerExportError("ledger could not be read for export") from exc

    if manifest is None:
        try:
            export_manifest = build_manifest(ledger)
        except LedgerManifestError as exc:
            raise LedgerExportError("ledger manifest could not be built for export") from exc
    else:
        try:
            export_manifest = read_manifest(manifest)
        except LedgerManifestError as exc:
            raise LedgerExportError("ledger manifest could not be read for export") from exc

    exported_events = _filter_events(events, boundary_id)
    summary = _decision_summary(
        store=store,
        boundary_id=boundary_id,
        exported_events=exported_events,
        verification=verification,
    )

    temp_dir = output.with_name(f".{output.name}.tmp")
    _remove_tree(temp_dir)
    try:
        temp_dir.mkdir(parents=True, exist_ok=False)
        _write_events(temp_dir / "ledger_events.jsonl", exported_events)
        (temp_dir / "ledger_manifest.json").write_text(
            export_manifest.to_canonical_json() + "\n",
            encoding="utf-8",
        )
        (temp_dir / "verification_report.json").write_text(
            verification.to_json() + "\n",
            encoding="utf-8",
        )
        (temp_dir / "verification_report.md").write_text(
            _verification_markdown(verification),
            encoding="utf-8",
        )
        (temp_dir / "decision_summary.json").write_text(
            canonical_json(summary) + "\n",
            encoding="utf-8",
        )
        (temp_dir / "README.md").write_text(
            _readme(boundary_id=boundary_id, verification=verification),
            encoding="utf-8",
        )

        if output.exists():
            _remove_tree(output)
        output.parent.mkdir(parents=True, exist_ok=True)
        temp_dir.replace(output)
    except Exception:
        _remove_tree(temp_dir)
        raise

    return LedgerExportResult(
        output_dir=str(output),
        events_exported=len(exported_events),
        verification_status=verification.status,
        boundary_filter=boundary_id,
        files=EXPORT_FILES,
    )


def _filter_events(events: list[DecisionEvent], boundary_id: str | None) -> list[DecisionEvent]:
    if boundary_id is None:
        return list(events)
    return [event for event in events if event.boundary_id == boundary_id]


def _write_events(path: Path, events: list[DecisionEvent]) -> None:
    path.write_text("".join(event.to_canonical_json() + "\n" for event in events), encoding="utf-8")


def _decision_summary(
    *,
    store: Path,
    boundary_id: str | None,
    exported_events: list[DecisionEvent],
    verification: LedgerVerificationResult,
) -> dict[str, Any]:
    policy_results = Counter(event.policy_result for event in exported_events)
    actions = Counter(event.action for event in exported_events)
    warning_count = sum(len(event.warnings) for event in exported_events)
    boundaries = sorted({event.boundary_id for event in exported_events})
    return {
        "schema_version": EXPORT_SUMMARY_SCHEMA_VERSION,
        "generated_at_utc": _utc_now(),
        "source_ledger": str(store),
        "boundary_filter": boundary_id,
        "events_exported": len(exported_events),
        "total_events_checked": verification.events_checked,
        "verification_status": verification.status,
        "first_event_hash": verification.first_event_hash,
        "last_event_hash": verification.last_event_hash,
        "boundaries": boundaries,
        "policy_results_count": dict(sorted(policy_results.items())),
        "actions_count": dict(sorted(actions.items())),
        "warnings_count": warning_count,
        "critical_findings_count": len(verification.critical_findings),
        "export_limitations": [
            "local audit review package, not compliance certification",
            "tamper-evident, not tamper-proof",
            "append-oriented local records, not immutable storage",
            "full-ledger verification remains the integrity source for filtered exports",
        ],
    }


def _verification_markdown(result: LedgerVerificationResult) -> str:
    lines = [
        "# Ledger Verification Report",
        "",
        "This report is generated for a local audit review package.",
        "",
        "```text",
        result.to_text(),
        "```",
        "",
        "## Limitations",
        "",
        "- Local audit review package, not compliance certification.",
        "- Tamper-evident, not tamper-proof.",
        "- Append-oriented local records, not immutable storage.",
        "- Does not guarantee truth or prevent hallucinations.",
        "",
    ]
    return "\n".join(lines)


def _readme(*, boundary_id: str | None, verification: LedgerVerificationResult) -> str:
    filtered_text = (
        f"This package is filtered to boundary `{boundary_id}`. "
        "The verification reports still describe the full source ledger because "
        "filtering breaks full-chain continuity."
        if boundary_id is not None
        else "This package includes all exported events from the source ledger."
    )
    return "\n".join(
        [
            "# Ledge Local Audit Review Package",
            "",
            "This folder contains a local audit review package for a Ledge decision ledger.",
            "",
            filtered_text,
            "",
            "## Files",
            "",
            "- `ledger_events.jsonl`: exported semantic decision boundary events.",
            "- `ledger_manifest.json`: local ledger manifest for review.",
            "- `verification_report.json`: machine-readable full-ledger verification result.",
            "- `verification_report.md`: human-readable full-ledger verification report.",
            "- `decision_summary.json`: safe aggregate summary.",
            "- `README.md`: package description and limitations.",
            "",
            "## Verification Status",
            "",
            f"Full-ledger verification status: `{verification.status}`",
            "",
            "## Limitations",
            "",
            "- This is a local audit review package, not compliance certification.",
            "- The ledger is tamper-evident, not tamper-proof.",
            "- Local files are append-oriented records, not immutable storage.",
            "- This package does not guarantee truth or prevent hallucinations.",
            "- This package does not replace human review, SIEM, observability, legal review, or governance processes.",
            "- Stronger guarantees require controls outside this package, such as access control, signatures, object lock, external anchoring, or independent custody.",
            "",
        ]
    )


def _remove_tree(path: Path) -> None:
    if path.exists():
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
