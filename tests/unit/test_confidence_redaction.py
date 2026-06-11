import math

import pytest

from ledge_lang.confidence import ConfidenceEvidence, EvidenceSource
from ledge_lang.confidence.exceptions import CanonicalSerializationError
from ledge_lang.confidence.redaction import hash_input, hash_output, redacted_summary


def test_input_hash_is_stable():
    value = {"customer_id": "123", "text": "refund requested"}

    assert hash_input(value) == hash_input({"text": "refund requested", "customer_id": "123"})


def test_output_hash_is_stable():
    value = {"route": "review"}

    assert hash_output(value) == hash_output({"route": "review"})


def test_redacted_summary_does_not_include_full_raw_value():
    raw = "customer email is person@example.com and wants a refund"

    summary = redacted_summary(raw)

    assert summary.startswith("[redacted str;")
    assert "person@example.com" not in summary
    assert raw not in summary


def test_evidence_does_not_store_raw_input_or_output_by_default():
    evidence = ConfidenceEvidence(
        evidence_id="ev1",
        boundary_id="refund_route",
        score=0.9,
        sources=[EvidenceSource(source_type="schema_validation", status="passed", score=0.9)],
        input_hash=hash_input("sensitive input"),
        output_hash=hash_output({"route": "review"}),
        metadata={"raw_data_included": False},
    )

    as_dict = evidence.to_dict()

    assert "raw_input" not in as_dict
    assert "raw_output" not in as_dict
    assert as_dict["input_hash"]
    assert as_dict["output_hash"]
    assert as_dict["redaction_applied"] is True
    assert as_dict["redaction_strategy"] == "hash_only"


def test_redaction_metadata_preserved():
    evidence = ConfidenceEvidence(
        evidence_id="ev1",
        boundary_id="refund_route",
        score=0.9,
        sources=[EvidenceSource(source_type="schema_validation", status="passed", score=0.9)],
        redaction_applied=True,
        redaction_strategy="hash_only",
        metadata={"redaction_note": "fixture"},
    )

    restored = ConfidenceEvidence.from_dict(evidence.to_dict())

    assert restored.redaction_applied is True
    assert restored.redaction_strategy == "hash_only"
    assert restored.metadata["redaction_note"] == "fixture"


def test_hash_input_rejects_unsupported_object_without_repr_hashing():
    class NonCanonical:
        pass

    with pytest.raises(CanonicalSerializationError) as exc_info:
        hash_input(NonCanonical())

    assert "NonCanonical" in str(exc_info.value)
    assert "object at 0x" not in str(exc_info.value)


def test_hash_output_rejects_unsupported_object_without_repr_hashing():
    class NonCanonical:
        pass

    with pytest.raises(CanonicalSerializationError) as exc_info:
        hash_output(NonCanonical())

    assert "NonCanonical" in str(exc_info.value)
    assert "object at 0x" not in str(exc_info.value)


@pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf])
def test_hash_helpers_reject_non_finite_floats(value):
    with pytest.raises(CanonicalSerializationError):
        hash_input(value)

    with pytest.raises(CanonicalSerializationError):
        hash_output(value)


def test_valid_json_like_values_hash_deterministically():
    values = [
        "refund",
        {"route": "review", "score": 0.7},
        ["refund", {"route": "review"}],
        0.7,
        True,
        None,
        b"refund bytes",
    ]

    for value in values:
        assert hash_input(value) == hash_input(value)
        assert hash_output(value) == hash_output(value)
