"""Deterministic ensemble agreement evidence."""

from __future__ import annotations

from collections import Counter
import math
from typing import Any

from .evidence import ConfidenceEvidence, EvidenceSource, _coerce_score
from .hashing import hash_text, stable_json_dumps


def evaluate_ensemble(
    candidates: list[Any],
    boundary_id: str,
    *,
    agreement_threshold: float = 0.8,
    evidence_id: str | None = None,
    policy_id: str | None = None,
    policy_hash: str | None = None,
    input_hash: str | None = None,
    metadata: dict | None = None,
) -> ConfidenceEvidence:
    """Evaluate exact ensemble agreement as a stability signal, not truth."""
    agreement_threshold = _coerce_score(agreement_threshold, "agreement_threshold")
    if candidates is None:
        candidates = []
    candidate_count = len(candidates)
    candidate_hashes: list[str] = []
    noncanonical_candidates: list[dict[str, Any]] = []
    for index, candidate in enumerate(candidates):
        noncanonical_reason = _noncanonical_reason(candidate)
        if noncanonical_reason is not None:
            noncanonical_candidates.append(
                {
                    "index": index,
                    "reason": noncanonical_reason,
                    "type": type(candidate).__name__,
                }
            )
        else:
            candidate_hashes.append(_hash_candidate(candidate))
    warnings: list[str] = []
    status = "passed"

    if noncanonical_candidates:
        warnings.append("ensemble_candidate_not_canonical")
        agreement = 0.0
        status = "failed"
        most_common_count = 0
    elif candidate_count == 0:
        warnings.append("ensemble_no_candidates")
        agreement = 0.0
        status = "failed"
        most_common_count = 0
    else:
        counts = Counter(candidate_hashes)
        most_common_count = counts.most_common(1)[0][1]
        agreement = most_common_count / candidate_count
        if candidate_count == 1:
            warnings.append("ensemble_single_candidate")
            agreement = 0.0
            status = "warning"
        elif agreement < agreement_threshold:
            warnings.append("ensemble_disagreement")
            status = "warning"

    details = {
        "agreement": agreement,
        "agreement_threshold": agreement_threshold,
        "candidate_count": candidate_count,
        "candidate_hashes": candidate_hashes,
        "canonical_candidate_count": len(candidate_hashes),
        "noncanonical_candidate_count": len(noncanonical_candidates),
        "noncanonical_candidates": noncanonical_candidates,
        "raw_candidates_stored": False,
        "unique_candidate_count": len(set(candidate_hashes)),
        "most_common_count": most_common_count,
        "calculation": "most_common_candidate_count / total_candidates",
        "meaning": "exact output stability, not correctness",
    }
    source = EvidenceSource(
        source_type="ensemble_agreement",
        status=status,
        score=agreement,
        impact="stability_signal",
        warnings=warnings,
        details=details,
        metadata={"raw_candidates_stored": False},
    )
    return ConfidenceEvidence(
        evidence_id=evidence_id or f"{boundary_id}:ensemble_agreement",
        boundary_id=boundary_id,
        score=agreement,
        sources=[source],
        warnings=warnings,
        input_hash=input_hash,
        policy_id=policy_id,
        policy_hash=policy_hash,
        redaction_applied=True,
        redaction_strategy="hash_only",
        metadata={
            **(metadata or {}),
            "raw_candidates_stored": False,
        },
    ).with_hash()


def _hash_candidate(candidate: Any) -> str:
    normalized = stable_json_dumps(candidate)
    return hash_text(normalized)


def _noncanonical_reason(value: Any) -> str | None:
    if isinstance(value, float) and not math.isfinite(value):
        return "non_finite_float"
    if not _is_json_like(value):
        return "non_canonical_json_value"
    return None


def _is_json_like(value: Any) -> bool:
    if value is None or isinstance(value, (str, bool)):
        return True
    if isinstance(value, float):
        return math.isfinite(value)
    if isinstance(value, int) and not isinstance(value, bool):
        return True
    if isinstance(value, list):
        return all(_is_json_like(item) for item in value)
    if isinstance(value, dict):
        return all(isinstance(key, str) and _is_json_like(item) for key, item in value.items())
    return False
