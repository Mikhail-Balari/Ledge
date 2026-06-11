import json
import math

import pytest

from ledge_lang.confidence import InvalidEvidenceScoreError, evaluate_ensemble


def test_ensemble_empty_candidates_is_deterministic_zero_score():
    evidence = evaluate_ensemble([], boundary_id="refund_route")

    assert evidence.score == 0.0
    assert "ensemble_no_candidates" in evidence.warnings
    assert evidence.sources[0].status == "failed"


def test_ensemble_single_candidate_emits_warning():
    evidence = evaluate_ensemble([{"route": "refund"}], boundary_id="refund_route")

    assert evidence.score == 0.0
    assert "ensemble_single_candidate" in evidence.warnings
    assert evidence.sources[0].details["candidate_count"] == 1


def test_ensemble_identical_candidates_produce_full_agreement():
    evidence = evaluate_ensemble(
        [{"route": "refund"}, {"route": "refund"}, {"route": "refund"}],
        boundary_id="refund_route",
    )

    assert evidence.score == 1.0
    assert evidence.sources[0].details["agreement"] == 1.0
    assert "ensemble_disagreement" not in evidence.warnings


def test_ensemble_disagreement_lowers_score_and_emits_warning():
    evidence = evaluate_ensemble(
        [{"route": "refund"}, {"route": "review"}, {"route": "refund"}],
        boundary_id="refund_route",
        agreement_threshold=0.8,
    )

    assert evidence.score == 2 / 3
    assert "ensemble_disagreement" in evidence.warnings


def test_ensemble_stores_candidate_hashes_not_raw_values():
    evidence = evaluate_ensemble(
        ["sensitive candidate output", "other output"],
        boundary_id="refund_route",
    )
    serialized = json.dumps(evidence.to_dict(), sort_keys=True)

    assert "candidate_hashes" in evidence.sources[0].details
    assert "sensitive candidate output" not in serialized
    assert "other output" not in serialized
    assert evidence.sources[0].details["raw_candidates_stored"] is False


def test_ensemble_evidence_is_hashable_and_canonical_serializable():
    evidence = evaluate_ensemble(["refund", "refund"], boundary_id="refund_route")

    assert evidence.evidence_hash == evidence.compute_hash()
    assert evidence.to_canonical_json() == evidence.to_canonical_json()


def test_ensemble_hash_changes_when_candidates_change():
    base = evaluate_ensemble(["refund", "refund"], boundary_id="refund_route")
    changed = evaluate_ensemble(["refund", "review"], boundary_id="refund_route")

    assert base.compute_hash() != changed.compute_hash()


def test_ensemble_noncanonical_candidate_warns_without_raw_repr():
    class NonCanonical:
        pass

    evidence = evaluate_ensemble([NonCanonical()], boundary_id="refund")
    rendered = json.dumps(evidence.to_dict(), sort_keys=True)

    assert evidence.score == 0.0
    assert "ensemble_candidate_not_canonical" in evidence.warnings
    assert "object at 0x" not in rendered
    assert "__main__" not in rendered
    assert evidence.evidence_hash == evidence.compute_hash()


def test_ensemble_noncanonical_candidate_records_safe_type_name_only():
    class NonCanonical:
        pass

    evidence = evaluate_ensemble([NonCanonical()], boundary_id="refund")
    details = evidence.sources[0].details

    assert details["noncanonical_candidate_count"] == 1
    assert details["noncanonical_candidates"] == [
        {
            "index": 0,
            "reason": "non_canonical_json_value",
            "type": "NonCanonical",
        }
    ]


@pytest.mark.parametrize("candidate", [math.nan, math.inf, -math.inf])
def test_ensemble_non_finite_float_candidate_returns_conservative_evidence(candidate):
    evidence = evaluate_ensemble([candidate], boundary_id="refund")

    assert evidence.score == 0.0
    assert "ensemble_candidate_not_canonical" in evidence.warnings
    assert evidence.sources[0].details["noncanonical_candidates"] == [
        {
            "index": 0,
            "reason": "non_finite_float",
            "type": "float",
        }
    ]
    assert evidence.evidence_hash == evidence.compute_hash()


def test_ensemble_no_canonical_serialization_error_leaks_for_noncanonical_candidates():
    class NonCanonical:
        pass

    for candidate in [NonCanonical(), math.nan]:
        evidence = evaluate_ensemble([candidate], boundary_id="refund")
        rendered = json.dumps(evidence.to_dict(), sort_keys=True)
        canonical = evidence.to_canonical_json()

        assert evidence.score == 0.0
        assert "ensemble_candidate_not_canonical" in evidence.warnings
        assert "object at 0x" not in rendered
        assert "object at 0x" not in canonical
        assert "__main__" not in rendered
        assert "__main__" not in canonical


def test_ensemble_valid_finite_floats_still_work():
    evidence = evaluate_ensemble([0.7, 0.7, 0.4], boundary_id="refund")

    assert evidence.score == 2 / 3
    assert "ensemble_candidate_not_canonical" not in evidence.warnings
    assert evidence.sources[0].details["candidate_count"] == 3
    assert evidence.sources[0].details["canonical_candidate_count"] == 3


def test_ensemble_valid_json_like_candidates_still_work():
    evidence = evaluate_ensemble(
        [
            {"route": "refund", "tags": ["low", "priority"]},
            {"route": "refund", "tags": ["low", "priority"]},
        ],
        boundary_id="refund_route",
    )
    changed = evaluate_ensemble(
        [
            {"route": "refund", "tags": ["low", "priority"]},
            {"route": "review", "tags": ["low", "priority"]},
        ],
        boundary_id="refund_route",
    )

    assert evidence.score == 1.0
    assert "ensemble_disagreement" not in evidence.warnings
    assert changed.score == 0.5
    assert "ensemble_disagreement" in changed.warnings


@pytest.mark.parametrize("threshold", [float("nan"), float("inf"), True, -0.1, 1.1])
def test_ensemble_threshold_uses_confidence_score_validation(threshold):
    with pytest.raises(InvalidEvidenceScoreError):
        evaluate_ensemble(
            ["refund", "refund"],
            boundary_id="refund_route",
            agreement_threshold=threshold,
        )
