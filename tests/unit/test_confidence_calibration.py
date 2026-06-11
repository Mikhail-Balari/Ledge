import json
import math

import pytest

from ledge_lang.confidence import (
    CalibrationOutcome,
    InvalidEvidenceError,
    InvalidEvidenceScoreError,
    generate_calibration_report,
    load_outcomes,
)


def outcome(prediction_id, score, result, boundary_id="refund_routing"):
    return CalibrationOutcome(
        boundary_id=boundary_id,
        prediction_id=prediction_id,
        score=score,
        outcome=result,
        action="allow",
    )


@pytest.mark.parametrize("score", [True, False, math.nan, math.inf, -math.inf, -0.1, 1.1])
def test_calibration_outcome_rejects_invalid_score(score):
    with pytest.raises(InvalidEvidenceScoreError):
        outcome("pred_invalid", score, True)


@pytest.mark.parametrize("result", [1, 0, "true", None])
def test_calibration_outcome_requires_bool_outcome(result):
    with pytest.raises(InvalidEvidenceError, match="outcome must be bool"):
        outcome("pred_invalid", 0.8, result)


def test_brier_score_is_deterministic():
    report = generate_calibration_report(
        [outcome("pred_1", 0.8, True), outcome("pred_2", 0.2, False)],
        min_samples=2,
    )

    assert report.brier_score == pytest.approx(0.04)


def test_ece_is_deterministic():
    report = generate_calibration_report(
        [outcome("pred_1", 0.25, False), outcome("pred_2", 0.75, True)],
        bins=2,
        min_samples=2,
    )

    assert report.ece == pytest.approx(0.25)
    assert len(report.bins) == 2


def test_low_sample_size_emits_warning():
    report = generate_calibration_report(
        [outcome("pred_1", 0.8, True), outcome("pred_2", 0.2, False)],
        min_samples=3,
    )

    assert "low_sample_size" in report.warnings
    assert report.suggested_threshold is None


def test_sufficient_samples_do_not_emit_low_sample_warning():
    report = generate_calibration_report(
        [outcome("pred_1", 0.8, True), outcome("pred_2", 0.2, False)],
        min_samples=2,
    )

    assert "low_sample_size" not in report.warnings


def test_suggested_threshold_is_deterministic_when_enough_data():
    report = generate_calibration_report(
        [
            outcome("pred_1", 0.9, True),
            outcome("pred_2", 0.8, True),
            outcome("pred_3", 0.7, True),
            outcome("pred_4", 0.6, False),
        ],
        min_samples=4,
    )

    assert report.suggested_threshold == pytest.approx(0.7)


def test_per_boundary_filtering_works():
    report = generate_calibration_report(
        [
            outcome("pred_1", 0.9, True, boundary_id="refund_routing"),
            outcome("pred_2", 0.1, False, boundary_id="support_triage"),
        ],
        boundary_id="support_triage",
        min_samples=1,
    )

    assert report.boundary_id == "support_triage"
    assert report.sample_count == 1
    assert report.brier_score == pytest.approx(0.01)


def test_no_matching_outcomes_is_clear():
    report = generate_calibration_report(
        [outcome("pred_1", 0.9, True)],
        boundary_id="missing_boundary",
    )

    assert report.boundary_id == "missing_boundary"
    assert report.sample_count == 0
    assert report.brier_score is None
    assert "no_matching_outcomes" in report.warnings


def test_report_serializes_to_dict_and_json():
    report = generate_calibration_report([outcome("pred_1", 0.9, True)], min_samples=1)

    data = report.to_dict()
    rendered = json.loads(report.to_json())

    assert data["boundary_id"] == "refund_routing"
    assert rendered["sample_count"] == 1


def test_load_outcomes_reads_json_file(tmp_path):
    path = tmp_path / "outcomes.json"
    path.write_text(
        json.dumps(
            [
                {
                    "boundary_id": "refund_routing",
                    "prediction_id": "pred_001",
                    "score": 0.82,
                    "outcome": True,
                    "action": "allow",
                }
            ]
        ),
        encoding="utf-8",
    )

    records = load_outcomes(path)

    assert len(records) == 1
    assert records[0].prediction_id == "pred_001"


def test_outcome_metadata_must_be_dictionary():
    with pytest.raises(InvalidEvidenceError, match="metadata must be a dictionary"):
        CalibrationOutcome.from_dict(
            {
                "boundary_id": "refund_routing",
                "prediction_id": "pred_bad",
                "score": 0.8,
                "outcome": True,
                "metadata": "not-a-dict",
            }
        )


def test_outcome_valid_dict_metadata_still_works():
    record = CalibrationOutcome.from_dict(
        {
            "boundary_id": "refund_routing",
            "prediction_id": "pred_001",
            "score": 0.8,
            "outcome": True,
            "metadata": {"source": "fixture"},
        }
    )

    assert record.metadata == {"source": "fixture"}


def test_outcome_missing_metadata_still_works():
    record = CalibrationOutcome.from_dict(
        {
            "boundary_id": "refund_routing",
            "prediction_id": "pred_001",
            "score": 0.8,
            "outcome": True,
        }
    )

    assert record.metadata == {}


def test_constructor_metadata_must_be_dictionary():
    with pytest.raises(InvalidEvidenceError, match="metadata must be a dictionary") as exc_info:
        CalibrationOutcome(
            boundary_id="refund_routing",
            prediction_id="pred_bad",
            score=0.8,
            outcome=True,
            metadata="not-a-dict",
        )

    assert not isinstance(exc_info.value, ValueError)


def test_constructor_valid_dict_metadata_still_works():
    record = CalibrationOutcome(
        boundary_id="refund_routing",
        prediction_id="pred_001",
        score=0.8,
        outcome=True,
        metadata={"source": "fixture"},
    )

    assert record.metadata == {"source": "fixture"}


def test_constructor_missing_metadata_still_works():
    record = CalibrationOutcome(
        boundary_id="refund_routing",
        prediction_id="pred_001",
        score=0.8,
        outcome=True,
    )

    assert record.metadata == {}


def test_constructor_metadata_is_defensively_copied():
    metadata = {"review": {"owner": "support"}}
    record = CalibrationOutcome(
        boundary_id="refund_routing",
        prediction_id="pred_001",
        score=0.8,
        outcome=True,
        metadata=metadata,
    )

    metadata["review"]["owner"] = "mutated"

    assert record.metadata["review"]["owner"] == "support"


def test_load_outcomes_rejects_malformed_file(tmp_path):
    path = tmp_path / "outcomes.json"
    path.write_text("{not json", encoding="utf-8")

    with pytest.raises(InvalidEvidenceError, match="malformed outcomes JSON"):
        load_outcomes(path)
