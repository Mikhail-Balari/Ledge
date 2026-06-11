"""Backend-provided logprob signal evidence."""

from __future__ import annotations

import math
from typing import Any

from .evidence import ConfidenceEvidence, EvidenceSource
from .hashing import hash_text


def extract_logprob_signal(
    logprobs: Any | None,
    boundary_id: str,
    *,
    evidence_id: str | None = None,
    policy_id: str | None = None,
    policy_hash: str | None = None,
    input_hash: str | None = None,
    metadata: dict | None = None,
) -> ConfidenceEvidence:
    """Build evidence from backend-provided logprobs without inventing values."""
    warnings: list[str] = []
    token_hashes: list[str] = []

    if logprobs is None:
        warnings.append("logprobs_unavailable")
        source = EvidenceSource(
            source_type="logprob_signal",
            status="unavailable",
            score=None,
            impact="missing_signal",
            warnings=warnings,
            details={
                "count": 0,
                "logprobs_provided": False,
                "raw_token_text_stored": False,
                "score_rule": "score set to 0.0 because backend logprobs were unavailable",
            },
            metadata={"raw_token_text_stored": False},
        )
        return _logprob_evidence(
            boundary_id=boundary_id,
            evidence_id=evidence_id,
            score=0.0,
            source=source,
            warnings=warnings,
            policy_id=policy_id,
            policy_hash=policy_hash,
            input_hash=input_hash,
            metadata=metadata,
        )

    raw_items = _as_logprob_items(logprobs)
    values: list[float] = []
    invalid_count = 0
    for item in raw_items:
        value, token = _extract_value_and_token(item)
        if token is not None:
            token_hashes.append(hash_text(str(token)))
        if _is_valid_logprob(value):
            values.append(float(value))
        else:
            invalid_count += 1

    if invalid_count:
        warnings.append("invalid_logprob_value")
    if not values:
        if "logprobs_unavailable" not in warnings:
            warnings.append("logprobs_invalid")
        source = EvidenceSource(
            source_type="logprob_signal",
            status="failed",
            score=0.0,
            impact="invalid_signal",
            warnings=warnings,
            details={
                "count": 0,
                "invalid_count": invalid_count,
                "logprobs_provided": True,
                "raw_token_text_stored": False,
                "token_hashes": token_hashes,
                "score_rule": "score set to 0.0 because no valid numeric logprobs were provided",
            },
            metadata={"raw_token_text_stored": False},
        )
        return _logprob_evidence(
            boundary_id=boundary_id,
            evidence_id=evidence_id,
            score=0.0,
            source=source,
            warnings=warnings,
            policy_id=policy_id,
            policy_hash=policy_hash,
            input_hash=input_hash,
            metadata=metadata,
        )

    mean_logprob = sum(values) / len(values)
    min_logprob = min(values)
    max_logprob = max(values)
    score = 1.0 if mean_logprob >= 0.0 else max(0.0, min(1.0, math.exp(mean_logprob)))
    status = "passed" if not invalid_count else "warning"
    source = EvidenceSource(
        source_type="logprob_signal",
        status=status,
        score=score,
        impact="backend_signal",
        warnings=warnings,
        details={
            "count": len(values),
            "invalid_count": invalid_count,
            "mean_logprob": mean_logprob,
            "min_logprob": min_logprob,
            "max_logprob": max_logprob,
            "logprobs_provided": True,
            "raw_token_text_stored": False,
            "token_hashes": token_hashes,
            "score_rule": "score = clamp(exp(mean_logprob), 0.0, 1.0)",
        },
        metadata={"raw_token_text_stored": False},
    )
    return _logprob_evidence(
        boundary_id=boundary_id,
        evidence_id=evidence_id,
        score=score,
        source=source,
        warnings=warnings,
        policy_id=policy_id,
        policy_hash=policy_hash,
        input_hash=input_hash,
        metadata=metadata,
    )


def _as_logprob_items(logprobs: Any) -> list[Any]:
    if isinstance(logprobs, dict):
        if isinstance(logprobs.get("logprobs"), list):
            return list(logprobs["logprobs"])
        if isinstance(logprobs.get("tokens"), list):
            return list(logprobs["tokens"])
        return [logprobs]
    if isinstance(logprobs, list):
        return list(logprobs)
    return [logprobs]


def _extract_value_and_token(item: Any) -> tuple[Any, Any | None]:
    if isinstance(item, dict):
        return item.get("logprob"), item.get("token")
    return item, None


def _is_valid_logprob(value: Any) -> bool:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    coerced = float(value)
    return math.isfinite(coerced)


def _logprob_evidence(
    *,
    boundary_id: str,
    evidence_id: str | None,
    score: float,
    source: EvidenceSource,
    warnings: list[str],
    policy_id: str | None,
    policy_hash: str | None,
    input_hash: str | None,
    metadata: dict | None,
) -> ConfidenceEvidence:
    return ConfidenceEvidence(
        evidence_id=evidence_id or f"{boundary_id}:logprob_signal",
        boundary_id=boundary_id,
        score=score,
        sources=[source],
        warnings=warnings,
        input_hash=input_hash,
        policy_id=policy_id,
        policy_hash=policy_hash,
        redaction_applied=True,
        redaction_strategy="hash_only",
        metadata={
            **(metadata or {}),
            "raw_token_text_stored": False,
        },
    ).with_hash()
