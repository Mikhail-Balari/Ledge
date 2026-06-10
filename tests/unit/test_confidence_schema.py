import pytest

from ledge_lang.confidence import SchemaEvidenceError, evaluate_schema


def warning_set(evidence):
    return set(evidence.warnings)


def test_invalid_json_forces_score_zero():
    evidence = evaluate_schema("{not json", boundary_id="refund_route")

    assert evidence.score == 0.0
    assert "schema_validation_failed" in warning_set(evidence)
    assert evidence.sources[0].status == "failed"


def test_valid_json_passes():
    evidence = evaluate_schema(
        '{"route": "review", "priority": 1}',
        required_fields=["route"],
        expected_types={"route": "str", "priority": "int"},
        boundary_id="refund_route",
    )

    assert evidence.score == 1.0
    assert evidence.sources[0].status == "passed"
    assert evidence.warnings == []


def test_missing_required_field_emits_warning():
    evidence = evaluate_schema(
        {"priority": 1},
        required_fields=["route"],
        boundary_id="refund_route",
    )

    assert evidence.score == 0.5
    assert "required_field_missing" in warning_set(evidence)


def test_missing_critical_field_emits_stronger_warning_and_zero_score():
    evidence = evaluate_schema(
        {"priority": 1},
        required_fields=["route"],
        critical_fields=["route"],
        boundary_id="refund_route",
    )

    assert evidence.score == 0.0
    assert "critical_field_missing" in warning_set(evidence)


def test_type_mismatch_emits_warning_and_zero_score():
    evidence = evaluate_schema(
        {"route": 3},
        expected_types={"route": "str"},
        boundary_id="refund_route",
    )

    assert evidence.score == 0.0
    assert "type_mismatch" in warning_set(evidence)


def test_bool_does_not_satisfy_int():
    evidence = evaluate_schema(
        {"priority": True},
        expected_types={"priority": "int"},
        boundary_id="refund_route",
    )

    assert evidence.score == 0.0
    assert "type_mismatch" in warning_set(evidence)


def test_invalid_expected_type_spec_fails_clearly():
    with pytest.raises(SchemaEvidenceError, match="invalid expected type"):
        evaluate_schema(
            {"route": "review"},
            expected_types={"route": "string"},
            boundary_id="refund_route",
        )


def test_schema_evidence_has_hashable_canonical_serialization():
    evidence = evaluate_schema(
        {"route": "review"},
        required_fields=["route"],
        boundary_id="refund_route",
    )

    assert evidence.evidence_hash == evidence.compute_hash()
    assert evidence.to_canonical_json()


def test_schema_evidence_does_not_store_raw_output():
    evidence = evaluate_schema(
        {"route": "review", "customer_email": "person@example.com"},
        boundary_id="refund_route",
    )

    data = evidence.to_dict()
    rendered = evidence.to_json()

    assert data["output_hash"]
    assert "person@example.com" not in rendered
    assert data["metadata"]["raw_output_stored"] is False
