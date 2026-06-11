import json

import pytest

from ledge_lang.confidence import (
    CalibrationOutcome,
    ConfidenceEvidence,
    EvidenceSource,
    InvalidEvidenceError,
    generate_calibration_report,
    render_calibration_report,
    render_confidence_report,
)


def sample_evidence():
    return ConfidenceEvidence(
        evidence_id="ev_refund_001",
        boundary_id="refund_routing",
        score=0.72,
        sources=[
            EvidenceSource(
                source_type="schema_validation",
                status="passed",
                score=1.0,
            ),
            EvidenceSource(
                source_type="ensemble_agreement",
                status="warning",
                score=0.72,
                warnings=["ensemble_disagreement"],
                details={"candidate_hashes": ["abc"], "candidate_count": 3},
            ),
        ],
        warnings=["ensemble_disagreement"],
        input_hash="sha256:input",
        output_hash="sha256:output",
    ).with_hash()


def sample_calibration_report():
    return generate_calibration_report(
        [
            CalibrationOutcome("refund_routing", "pred_1", 0.8, True),
            CalibrationOutcome("refund_routing", "pred_2", 0.2, False),
        ],
        bins=2,
        min_samples=3,
    )


def test_confidence_report_text_includes_sources_warnings_and_no_truth_guarantee():
    rendered = render_confidence_report(sample_evidence())

    assert "Final score" in rendered
    assert "Sources:" in rendered
    assert "ensemble_disagreement" in rendered
    assert "No truth guarantee." in rendered


def test_confidence_report_json_is_valid_and_stable():
    data = json.loads(render_confidence_report(sample_evidence(), format="json"))

    assert data["boundary_id"] == "refund_routing"
    assert data["final_score"] == 0.72
    assert data["no_truth_guarantee"] is True
    assert data["sources"][0]["source_type"] == "schema_validation"


def test_calibration_report_text_includes_metrics_limitations_and_caveat():
    rendered = render_calibration_report(sample_calibration_report())

    assert "Brier score" in rendered
    assert "ECE" in rendered
    assert "Limitations:" in rendered
    assert "Calibration report is not a guarantee of truth or compliance." in rendered


def test_calibration_report_json_is_valid():
    data = json.loads(render_calibration_report(sample_calibration_report(), format="json"))

    assert data["boundary_id"] == "refund_routing"
    assert data["sample_count"] == 2
    assert "low_sample_size" in data["warnings"]


@pytest.mark.parametrize(
    "renderer, value",
    [
        (render_confidence_report, sample_evidence()),
        (render_calibration_report, sample_calibration_report()),
    ],
)
def test_invalid_report_format_raises_controlled_error(renderer, value):
    with pytest.raises(InvalidEvidenceError, match="unsupported report format"):
        renderer(value, format="xml")


def test_report_output_does_not_include_raw_sensitive_data():
    rendered = render_confidence_report(sample_evidence(), format="json")

    assert "customer@example.com" not in rendered
    assert "refund reason contains private details" not in rendered
    assert "sha256:input" in rendered


def test_confidence_json_report_redacts_source_details_and_metadata_values():
    source = EvidenceSource(
        source_type="schema_validation",
        status="failed",
        score=0.0,
        impact="hard_failure",
        details={"raw_output": "sensitive model output"},
        metadata={"prompt": "sensitive prompt"},
    )
    evidence = ConfidenceEvidence(
        evidence_id="ev_sensitive",
        boundary_id="refund_routing",
        score=0.0,
        sources=[source],
    ).with_hash()

    rendered = render_confidence_report(evidence, format="json")
    data = json.loads(rendered)
    safe_source = data["sources"][0]

    assert "sensitive model output" not in rendered
    assert "sensitive prompt" not in rendered
    assert safe_source["detail_keys"] == ["raw_output"]
    assert safe_source["metadata_keys"] == ["prompt"]
    assert safe_source["details_redacted"] is True
    assert safe_source["metadata_redacted"] is True
    assert "raw_data_included_review_storage_controls" in safe_source["warnings"]


def test_confidence_json_report_rendering_does_not_mutate_evidence():
    source = EvidenceSource(
        source_type="schema_validation",
        status="failed",
        details={"raw_output": "sensitive model output"},
        metadata={"prompt": "sensitive prompt"},
    )
    evidence = ConfidenceEvidence(
        evidence_id="ev_sensitive",
        boundary_id="refund_routing",
        score=0.0,
        sources=[source],
    )
    before = evidence.to_dict()

    render_confidence_report(evidence, format="json")

    assert evidence.to_dict() == before


def test_confidence_text_report_lists_keys_without_raw_values():
    source = EvidenceSource(
        source_type="schema_validation",
        status="failed",
        details={"raw_output": "sensitive model output"},
        metadata={"prompt": "sensitive prompt"},
    )
    evidence = ConfidenceEvidence(
        evidence_id="ev_sensitive",
        boundary_id="refund_routing",
        score=0.0,
        sources=[source],
    )

    rendered = render_confidence_report(evidence)

    assert "detail fields: raw_output" in rendered
    assert "sensitive model output" not in rendered
    assert "sensitive prompt" not in rendered
