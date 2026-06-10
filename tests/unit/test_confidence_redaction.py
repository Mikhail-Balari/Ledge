from ledge_lang.confidence import ConfidenceEvidence, EvidenceSource
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
