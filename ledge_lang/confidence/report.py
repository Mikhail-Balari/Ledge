"""Text and JSON rendering for confidence evidence reports."""

from __future__ import annotations

import json
from typing import Any

from .calibration import CalibrationReport
from .evidence import ConfidenceEvidence
from .exceptions import InvalidEvidenceError

CONFIDENCE_LIMITATIONS = [
    "no truth guarantee",
    "not a compliance guarantee",
    "not formal verification",
    "does not replace code review, evals, monitoring, or governance",
]


def render_confidence_report(evidence: ConfidenceEvidence, *, format: str = "text") -> str:
    """Render a confidence evidence report."""
    if not isinstance(evidence, ConfidenceEvidence):
        evidence = ConfidenceEvidence.from_dict(evidence)
    if format == "json":
        return json.dumps(_confidence_report_dict(evidence), indent=2, sort_keys=True)
    if format != "text":
        raise InvalidEvidenceError(f"unsupported report format: {format}")
    evidence_hash = evidence.evidence_hash or evidence.compute_hash()
    lines = [
        "Ledge Confidence Evidence Report",
        f"Boundary ID: {evidence.boundary_id}",
        f"Evidence ID: {evidence.evidence_id}",
        f"Final score: {evidence.score:.4f}",
        f"Evidence hash: {evidence_hash}",
        f"Input hash: {evidence.input_hash or 'n/a'}",
        f"Output hash: {evidence.output_hash or 'n/a'}",
        f"Redaction: applied={evidence.redaction_applied} strategy={evidence.redaction_strategy}",
        "",
        "Sources:",
    ]
    for source in evidence.sources:
        score = "n/a" if source.score is None else f"{source.score:.4f}"
        lines.append(f"- {source.source_type}: status={source.status} score={score}")
        if source.warnings:
            lines.append(f"  warnings: {', '.join(source.warnings)}")
        if source.details:
            detail_keys = ", ".join(sorted(source.details.keys()))
            lines.append(f"  detail fields: {detail_keys}")
    lines.extend(["", "Warnings:"])
    if evidence.warnings:
        lines.extend(f"- {warning}" for warning in evidence.warnings)
    else:
        lines.append("- none")
    lines.extend(["", "Limitations:"])
    lines.extend(f"- {item}" for item in CONFIDENCE_LIMITATIONS)
    lines.append("")
    lines.append("No truth guarantee.")
    return "\n".join(lines)


def render_calibration_report(report: CalibrationReport, *, format: str = "text") -> str:
    """Render a calibration report."""
    if not isinstance(report, CalibrationReport):
        report = CalibrationReport.from_dict(report)
    if format == "json":
        return json.dumps(report.to_dict(), indent=2, sort_keys=True)
    if format != "text":
        raise InvalidEvidenceError(f"unsupported report format: {format}")
    brier = "n/a" if report.brier_score is None else f"{report.brier_score:.4f}"
    ece = "n/a" if report.ece is None else f"{report.ece:.4f}"
    threshold = "n/a" if report.suggested_threshold is None else f"{report.suggested_threshold:.4f}"
    lines = [
        "Ledge Calibration Report",
        f"Boundary ID: {report.boundary_id}",
        f"Sample count: {report.sample_count}",
        f"Brier score: {brier}",
        f"ECE: {ece}",
        f"Suggested threshold: {threshold}",
        "",
        "Warnings:",
    ]
    if report.warnings:
        lines.extend(f"- {warning}" for warning in report.warnings)
    else:
        lines.append("- none")
    lines.extend(["", "Limitations:"])
    if report.limitations:
        lines.extend(f"- {item}" for item in report.limitations)
    else:
        lines.append("- calibration requires representative historical outcomes")
    lines.append("- calibration report is not a guarantee of truth or compliance")
    lines.append("")
    lines.append("Calibration report is not a guarantee of truth or compliance.")
    return "\n".join(lines)


def _confidence_report_dict(evidence: ConfidenceEvidence) -> dict[str, Any]:
    evidence_hash = evidence.evidence_hash or evidence.compute_hash()
    return {
        "boundary_id": evidence.boundary_id,
        "evidence_id": evidence.evidence_id,
        "final_score": evidence.score,
        "evidence_hash": evidence_hash,
        "input_hash": evidence.input_hash,
        "output_hash": evidence.output_hash,
        "policy_id": evidence.policy_id,
        "policy_hash": evidence.policy_hash,
        "sources": [_safe_source_report_dict(source) for source in evidence.sources],
        "warnings": list(evidence.warnings),
        "redaction": {
            "applied": evidence.redaction_applied,
            "strategy": evidence.redaction_strategy,
        },
        "limitations": list(CONFIDENCE_LIMITATIONS),
        "no_truth_guarantee": True,
    }


def _safe_source_report_dict(source: Any) -> dict[str, Any]:
    details = dict(source.details or {})
    metadata = dict(source.metadata or {})
    return {
        "source_type": source.source_type,
        "status": source.status,
        "score": source.score,
        "impact": source.impact,
        "warnings": list(source.warnings),
        "detail_keys": sorted(str(key) for key in details.keys()),
        "metadata_keys": sorted(str(key) for key in metadata.keys()),
        "details_redacted": bool(details),
        "metadata_redacted": bool(metadata),
    }
