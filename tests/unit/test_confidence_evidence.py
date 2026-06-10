import json

import pytest

from ledge_lang.confidence import (
    ConfidenceEvidence,
    EvidenceSource,
    InvalidEvidenceError,
    InvalidEvidenceScoreError,
    InvalidEvidenceSourceError,
)

RAW_DATA_WARNING = "raw_data_included_review_storage_controls"


def source(score=0.9, status="passed"):
    return EvidenceSource(
        source_type="schema_validation",
        status=status,
        score=score,
        details={"field": "route"},
    )


@pytest.mark.parametrize(
    "score",
    [float("nan"), float("inf"), float("-inf"), True, False, -0.1, 1.1],
)
def test_confidence_evidence_rejects_invalid_score(score):
    with pytest.raises(InvalidEvidenceScoreError):
        ConfidenceEvidence(
            evidence_id="ev1",
            boundary_id="refund_route",
            score=score,
            sources=[source()],
        )


@pytest.mark.parametrize("score", [float("nan"), float("inf"), True, False, -0.1, 1.1])
def test_evidence_source_score_validation(score):
    with pytest.raises(InvalidEvidenceScoreError):
        EvidenceSource(source_type="schema_validation", status="passed", score=score)


def test_evidence_source_requires_type_and_status():
    with pytest.raises(InvalidEvidenceSourceError):
        EvidenceSource(source_type="", status="passed")
    with pytest.raises(InvalidEvidenceSourceError):
        EvidenceSource(source_type="schema_validation", status="")


def test_confidence_evidence_requires_ids():
    with pytest.raises(InvalidEvidenceError):
        ConfidenceEvidence(
            evidence_id="",
            boundary_id="refund_route",
            score=0.9,
            sources=[source()],
        )
    with pytest.raises(InvalidEvidenceError):
        ConfidenceEvidence(
            evidence_id="ev1",
            boundary_id="",
            score=0.9,
            sources=[source()],
        )


def test_evidence_serializes_and_roundtrips_dict_and_json():
    evidence = ConfidenceEvidence(
        evidence_id="ev1",
        boundary_id="refund_route",
        score=0.9,
        sources=[source()],
        warnings=["review_threshold"],
        input_hash="abc",
        output_hash="def",
        policy_id="policy/refund",
        policy_hash="policyhash",
        metadata={"case": "ok"},
    ).with_hash()

    as_dict = evidence.to_dict()
    from_dict = ConfidenceEvidence.from_dict(as_dict)
    from_json = ConfidenceEvidence.from_json(evidence.to_json())

    assert as_dict["evidence_id"] == "ev1"
    assert from_dict.to_dict() == evidence.to_dict()
    assert from_json.to_dict() == evidence.to_dict()
    assert json.loads(evidence.to_json())["evidence_hash"] == evidence.evidence_hash


def test_evidence_source_roundtrips_from_dict():
    original = source()
    restored = EvidenceSource.from_dict(original.to_dict())

    assert restored.to_dict() == original.to_dict()


def test_canonical_json_is_stable_and_display_format_does_not_affect_hash():
    evidence = ConfidenceEvidence(
        evidence_id="ev1",
        boundary_id="refund_route",
        score=0.9,
        sources=[source()],
        metadata={"b": 2, "a": 1},
    )

    assert evidence.to_canonical_json() == evidence.to_canonical_json()
    assert evidence.compute_hash() == ConfidenceEvidence.from_json(evidence.to_json()).compute_hash()


def test_evidence_hash_excludes_evidence_hash_field():
    evidence = ConfidenceEvidence(
        evidence_id="ev1",
        boundary_id="refund_route",
        score=0.9,
        sources=[source()],
    ).with_hash()

    tampered_hash_field = ConfidenceEvidence.from_dict(
        {**evidence.to_dict(), "evidence_hash": "different"}
    )

    assert tampered_hash_field.compute_hash() == evidence.compute_hash()


def test_evidence_hash_changes_when_score_source_or_warning_changes():
    base = ConfidenceEvidence(
        evidence_id="ev1",
        boundary_id="refund_route",
        score=0.9,
        sources=[source()],
        warnings=["a"],
    )
    changed_score = ConfidenceEvidence(
        evidence_id="ev1",
        boundary_id="refund_route",
        score=0.8,
        sources=[source()],
        warnings=["a"],
    )
    changed_source = ConfidenceEvidence(
        evidence_id="ev1",
        boundary_id="refund_route",
        score=0.9,
        sources=[EvidenceSource(source_type="ensemble", status="passed", score=0.9)],
        warnings=["a"],
    )
    changed_warning = ConfidenceEvidence(
        evidence_id="ev1",
        boundary_id="refund_route",
        score=0.9,
        sources=[source()],
        warnings=["b"],
    )

    assert base.compute_hash() != changed_score.compute_hash()
    assert base.compute_hash() != changed_source.compute_hash()
    assert base.compute_hash() != changed_warning.compute_hash()


def test_evidence_roundtrip_preserves_canonical_hash():
    evidence = ConfidenceEvidence(
        evidence_id="ev1",
        boundary_id="refund_route",
        score=0.9,
        sources=[source()],
    ).with_hash()

    restored = ConfidenceEvidence.from_json(evidence.to_json())

    assert restored.compute_hash() == evidence.evidence_hash


def test_raw_data_included_warning_is_added():
    evidence = ConfidenceEvidence(
        evidence_id="ev1",
        boundary_id="refund_route",
        score=0.9,
        sources=[source()],
        metadata={"raw_data_included": True},
    )

    assert RAW_DATA_WARNING in evidence.warnings


def test_raw_like_metadata_key_adds_warning():
    evidence = ConfidenceEvidence(
        evidence_id="ev1",
        boundary_id="refund_route",
        score=0.9,
        sources=[source()],
        metadata={"raw_input": "sensitive"},
    )

    assert RAW_DATA_WARNING in evidence.warnings


def test_evidence_source_details_raw_like_key_adds_warning():
    raw_source = EvidenceSource(
        source_type="schema_validation",
        status="failed",
        details={"raw_output": "sensitive model output"},
    )

    assert RAW_DATA_WARNING in raw_source.warnings


def test_evidence_source_metadata_raw_like_key_adds_warning():
    raw_source = EvidenceSource(
        source_type="schema_validation",
        status="failed",
        metadata={"prompt": "sensitive prompt"},
    )

    assert RAW_DATA_WARNING in raw_source.warnings


def test_evidence_source_raw_data_warning_is_not_duplicated():
    raw_source = EvidenceSource(
        source_type="schema_validation",
        status="failed",
        warnings=[RAW_DATA_WARNING],
        details={"raw_output": "sensitive model output"},
    )

    assert raw_source.warnings.count(RAW_DATA_WARNING) == 1


def test_evidence_source_non_raw_details_do_not_add_warning():
    clean_source = EvidenceSource(
        source_type="schema_validation",
        status="failed",
        details={"field": "category", "expected": "str", "actual": "int"},
    )

    assert RAW_DATA_WARNING not in clean_source.warnings


def test_evidence_source_roundtrip_preserves_raw_data_warning():
    raw_source = EvidenceSource(
        source_type="schema_validation",
        status="failed",
        details={"raw_output": "sensitive model output"},
    )
    restored_source = EvidenceSource.from_dict(raw_source.to_dict())
    evidence = ConfidenceEvidence(
        evidence_id="ev1",
        boundary_id="refund_route",
        score=0.0,
        sources=[raw_source],
    )
    restored_evidence = ConfidenceEvidence.from_dict(evidence.to_dict())

    assert RAW_DATA_WARNING in restored_source.warnings
    assert RAW_DATA_WARNING in restored_evidence.sources[0].warnings


def test_evidence_hash_changes_when_source_raw_data_warning_is_added():
    clean_evidence = ConfidenceEvidence(
        evidence_id="ev1",
        boundary_id="refund_route",
        score=0.9,
        sources=[
            EvidenceSource(
                source_type="schema_validation",
                status="passed",
                metadata={"field": "route"},
            )
        ],
    )
    raw_evidence = ConfidenceEvidence(
        evidence_id="ev1",
        boundary_id="refund_route",
        score=0.9,
        sources=[
            EvidenceSource(
                source_type="schema_validation",
                status="passed",
                metadata={"prompt": "sensitive prompt"},
            )
        ],
    )

    assert RAW_DATA_WARNING in raw_evidence.sources[0].warnings
    assert clean_evidence.compute_hash() != raw_evidence.compute_hash()


def test_evidence_source_details_are_isolated_from_caller_mutation():
    details = {"nested": {"field": "category"}}
    raw_source = EvidenceSource(
        source_type="schema_validation",
        status="passed",
        details=details,
    )

    details["nested"]["field"] = "mutated"

    assert raw_source.details["nested"]["field"] == "category"


def test_evidence_source_metadata_is_isolated_from_caller_mutation():
    metadata = {"policy": {"id": "p1"}}
    raw_source = EvidenceSource(
        source_type="schema_validation",
        status="passed",
        metadata=metadata,
    )

    metadata["policy"]["id"] = "mutated"

    assert raw_source.metadata["policy"]["id"] == "p1"


def test_evidence_source_warnings_are_isolated_from_caller_mutation():
    warnings = ["initial_warning"]
    raw_source = EvidenceSource(
        source_type="schema_validation",
        status="passed",
        warnings=warnings,
    )

    warnings.append("mutated")

    assert raw_source.warnings == ["initial_warning"]


def test_confidence_evidence_metadata_is_isolated_from_caller_mutation():
    metadata = {"audit": {"owner": "team-a"}}
    evidence = ConfidenceEvidence(
        evidence_id="ev_1",
        boundary_id="refund",
        score=0.8,
        sources=[EvidenceSource(source_type="schema_validation", status="passed")],
        metadata=metadata,
    )

    metadata["audit"]["owner"] = "mutated"

    assert evidence.metadata["audit"]["owner"] == "team-a"


def test_confidence_evidence_sources_are_isolated_from_caller_list_mutation():
    sources = [EvidenceSource(source_type="schema_validation", status="passed")]
    evidence = ConfidenceEvidence(
        evidence_id="ev_1",
        boundary_id="refund",
        score=0.8,
        sources=sources,
    )

    sources.append(EvidenceSource(source_type="other", status="passed"))

    assert len(evidence.sources) == 1


def test_confidence_evidence_hash_is_stable_after_caller_mutates_original_inputs():
    details = {"nested": {"field": "category"}}
    source_metadata = {"policy": {"id": "p1"}}
    evidence_metadata = {"audit": {"owner": "team-a"}}
    warnings = ["initial_warning"]
    sources = [
        EvidenceSource(
            source_type="schema_validation",
            status="passed",
            warnings=warnings,
            details=details,
            metadata=source_metadata,
        )
    ]
    evidence = ConfidenceEvidence(
        evidence_id="ev_1",
        boundary_id="refund",
        score=0.8,
        sources=sources,
        metadata=evidence_metadata,
    )
    original_hash = evidence.compute_hash()

    details["nested"]["field"] = "mutated"
    source_metadata["policy"]["id"] = "mutated"
    evidence_metadata["audit"]["owner"] = "mutated"
    warnings.append("mutated")
    sources.append(EvidenceSource(source_type="other", status="passed"))

    assert evidence.compute_hash() == original_hash


def test_raw_like_detection_survives_defensive_copying():
    details = {"raw_output": "sensitive model output"}
    raw_source = EvidenceSource(
        source_type="schema_validation",
        status="failed",
        details=details,
    )

    details.clear()

    assert raw_source.details["raw_output"] == "sensitive model output"
    assert RAW_DATA_WARNING in raw_source.warnings
