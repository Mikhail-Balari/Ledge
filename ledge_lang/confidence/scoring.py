"""Conservative explainable confidence scoring."""

from __future__ import annotations

from typing import Any

from .evidence import ConfidenceEvidence, EvidenceSource, _coerce_score

HARD_FAILURE_WARNINGS = {
    "critical_field_missing",
    "schema_validation_failed",
    "type_mismatch",
}


def score_evidence(
    *,
    boundary_id: str,
    base_score: float,
    sources: list[EvidenceSource],
    warnings: list[str] | None = None,
    evidence_id: str | None = None,
    policy_id: str | None = None,
    policy_hash: str | None = None,
    input_hash: str | None = None,
    output_hash: str | None = None,
    metadata: dict | None = None,
) -> ConfidenceEvidence:
    """Combine evidence sources using a conservative min rule."""
    final_score = _coerce_score(base_score, "base_score")
    source_records = [
        source if isinstance(source, EvidenceSource) else EvidenceSource.from_dict(source)
        for source in list(sources or [])
    ]
    combined_warnings = _dedupe(list(warnings or []))
    for source in source_records:
        combined_warnings = _dedupe(combined_warnings + source.warnings)
    adjustments: list[dict[str, Any]] = []

    hard_failure = any(_is_hard_failure(source) for source in source_records)
    if hard_failure:
        final_score = 0.0
        combined_warnings = _dedupe(combined_warnings + ["hard_evidence_failure"])
        adjustments.append(
            {
                "rule": "hard_failure_forces_zero",
                "reason": "schema/type critical failure present",
                "score_after": final_score,
            }
        )
    else:
        for source in source_records:
            if source.score is None:
                continue
            before = final_score
            final_score = min(final_score, source.score)
            adjustments.append(
                {
                    "rule": "conservative_min",
                    "source_type": source.source_type,
                    "source_status": source.status,
                    "source_score": source.score,
                    "score_before": before,
                    "score_after": final_score,
                }
            )

    scoring_source = EvidenceSource(
        source_type="score_aggregation",
        status="passed" if not hard_failure else "failed",
        score=final_score,
        impact="conservative_aggregation",
        warnings=["hard_evidence_failure"] if hard_failure else [],
        details={
            "base_score": float(base_score),
            "final_score": final_score,
            "hard_failure": hard_failure,
            "rule": "hard failures force 0.0; otherwise final score is the min of base and source scores",
            "boosting_allowed": False,
            "adjustments": adjustments,
        },
        metadata={"opaque_weights_used": False},
    )
    final_sources = source_records + [scoring_source]
    combined_warnings = _dedupe(combined_warnings + scoring_source.warnings)

    return ConfidenceEvidence(
        evidence_id=evidence_id or f"{boundary_id}:score_aggregation",
        boundary_id=boundary_id,
        score=final_score,
        sources=final_sources,
        warnings=combined_warnings,
        input_hash=input_hash,
        output_hash=output_hash,
        policy_id=policy_id,
        policy_hash=policy_hash,
        redaction_applied=True,
        redaction_strategy="hash_only",
        metadata={
            **(metadata or {}),
            "scoring_rule": "conservative_min",
            "opaque_weights_used": False,
        },
    ).with_hash()


def _is_hard_failure(source: EvidenceSource) -> bool:
    source_type = source.source_type.lower()
    status = source.status.lower()
    warnings = set(source.warnings)
    if source_type == "schema_validation" and status == "failed":
        return True
    return bool(warnings & HARD_FAILURE_WARNINGS)


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    deduped: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            deduped.append(value)
    return deduped
