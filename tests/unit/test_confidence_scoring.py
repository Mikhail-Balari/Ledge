import pytest

from ledge_lang.confidence import (
    EvidenceSource,
    InvalidEvidenceScoreError,
    score_evidence,
)


def source(source_type="ensemble_agreement", status="passed", score=0.8, warnings=None):
    return EvidenceSource(
        source_type=source_type,
        status=status,
        score=score,
        warnings=warnings or [],
    )


@pytest.mark.parametrize(
    "base_score",
    [float("nan"), float("inf"), float("-inf"), True, False, -0.1, 1.1],
)
def test_score_evidence_rejects_invalid_base_score(base_score):
    with pytest.raises(InvalidEvidenceScoreError):
        score_evidence(
            boundary_id="refund_route",
            base_score=base_score,
            sources=[],
        )


def test_no_sources_preserves_base_score_and_adds_scoring_source():
    evidence = score_evidence(
        boundary_id="refund_route",
        base_score=0.7,
        sources=[],
    )

    assert evidence.score == 0.7
    assert evidence.sources[-1].source_type == "score_aggregation"
    assert evidence.sources[-1].details["rule"].startswith("hard failures force")
    assert evidence.sources[-1].details["boosting_allowed"] is False


def test_source_lower_than_base_lowers_final_score():
    evidence = score_evidence(
        boundary_id="refund_route",
        base_score=0.9,
        sources=[source(score=0.6)],
    )

    assert evidence.score == 0.6
    assert evidence.sources[-1].details["adjustments"][0]["rule"] == "conservative_min"


def test_source_higher_than_base_does_not_boost_score():
    evidence = score_evidence(
        boundary_id="refund_route",
        base_score=0.7,
        sources=[source(score=0.95)],
    )

    assert evidence.score == 0.7


def test_schema_validation_failure_forces_zero():
    evidence = score_evidence(
        boundary_id="refund_route",
        base_score=0.9,
        sources=[source(source_type="schema_validation", status="failed", score=0.4)],
    )

    assert evidence.score == 0.0
    assert "hard_evidence_failure" in evidence.warnings
    assert evidence.sources[-1].status == "failed"


def test_type_mismatch_warning_forces_zero():
    evidence = score_evidence(
        boundary_id="refund_route",
        base_score=0.9,
        sources=[source(score=0.8, warnings=["type_mismatch"])],
    )

    assert evidence.score == 0.0
    assert "hard_evidence_failure" in evidence.warnings


def test_hard_failure_preserves_type_mismatch_at_top_level():
    evidence = score_evidence(
        boundary_id="refund_route",
        base_score=0.9,
        sources=[source(score=0.8, warnings=["type_mismatch"])],
    )

    assert evidence.score == 0.0
    assert "type_mismatch" in evidence.warnings
    assert "hard_evidence_failure" in evidence.warnings


def test_hard_failure_preserves_schema_validation_failed_at_top_level():
    evidence = score_evidence(
        boundary_id="refund_route",
        base_score=0.9,
        sources=[source(score=0.8, warnings=["schema_validation_failed"])],
    )

    assert evidence.score == 0.0
    assert "schema_validation_failed" in evidence.warnings
    assert "hard_evidence_failure" in evidence.warnings


def test_hard_failure_preserves_critical_field_missing_at_top_level():
    evidence = score_evidence(
        boundary_id="refund_route",
        base_score=0.9,
        sources=[source(score=0.8, warnings=["critical_field_missing"])],
    )

    assert evidence.score == 0.0
    assert "critical_field_missing" in evidence.warnings
    assert "hard_evidence_failure" in evidence.warnings


def test_caller_warnings_are_preserved_on_hard_failure_path():
    evidence = score_evidence(
        boundary_id="refund_route",
        base_score=0.9,
        sources=[source(score=0.8, warnings=["type_mismatch"])],
        warnings=["manual_review_required"],
    )

    assert "manual_review_required" in evidence.warnings
    assert "type_mismatch" in evidence.warnings
    assert "hard_evidence_failure" in evidence.warnings


def test_hard_failure_top_level_warnings_are_deduplicated():
    evidence = score_evidence(
        boundary_id="refund_route",
        base_score=0.9,
        sources=[
            source(score=0.8, warnings=["type_mismatch"]),
            source(source_type="schema_validation", status="failed", score=0.0, warnings=["type_mismatch"]),
        ],
        warnings=["type_mismatch"],
    )

    assert evidence.warnings.count("type_mismatch") == 1
    assert evidence.warnings.count("hard_evidence_failure") == 1


def test_warnings_are_preserved():
    evidence = score_evidence(
        boundary_id="refund_route",
        base_score=0.9,
        sources=[source(score=0.8, warnings=["ensemble_disagreement"])],
        warnings=["manual_review_hint"],
    )

    assert "manual_review_hint" in evidence.warnings
    assert "ensemble_disagreement" in evidence.warnings


def test_scoring_source_explains_conservative_min_rule():
    evidence = score_evidence(
        boundary_id="refund_route",
        base_score=0.9,
        sources=[source(score=0.8)],
    )
    scoring_details = evidence.sources[-1].details

    assert scoring_details["base_score"] == 0.9
    assert scoring_details["final_score"] == 0.8
    assert scoring_details["boosting_allowed"] is False
    assert scoring_details["adjustments"][0]["rule"] == "conservative_min"


def test_scored_evidence_is_hashable_and_canonical_serializable():
    evidence = score_evidence(
        boundary_id="refund_route",
        base_score=0.9,
        sources=[source(score=0.8)],
    )

    assert evidence.evidence_hash == evidence.compute_hash()
    assert evidence.to_canonical_json() == evidence.to_canonical_json()


def test_scored_evidence_hash_changes_when_score_source_or_warning_changes():
    base = score_evidence(
        boundary_id="refund_route",
        base_score=0.9,
        sources=[source(score=0.8)],
        warnings=["a"],
    )
    changed_score = score_evidence(
        boundary_id="refund_route",
        base_score=0.7,
        sources=[source(score=0.8)],
        warnings=["a"],
    )
    changed_source = score_evidence(
        boundary_id="refund_route",
        base_score=0.9,
        sources=[source(source_type="logprob_signal", score=0.8)],
        warnings=["a"],
    )
    changed_warning = score_evidence(
        boundary_id="refund_route",
        base_score=0.9,
        sources=[source(score=0.8)],
        warnings=["b"],
    )

    assert base.compute_hash() != changed_score.compute_hash()
    assert base.compute_hash() != changed_source.compute_hash()
    assert base.compute_hash() != changed_warning.compute_hash()
