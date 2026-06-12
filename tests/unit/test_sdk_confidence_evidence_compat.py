from __future__ import annotations

from dataclasses import dataclass
import math

from ledge_lang.confidence import ConfidenceEvidence as AuditConfidenceEvidence
from ledge_lang.confidence import EvidenceSource
from ledge_lang.sdk import ConfidenceEvidence, DecisionPolicy, Uncertain
from ledge_lang.sdk._evidence_compat import extract_evidence_context


def handle_with(evidence):
    return Uncertain(
        value="ok",
        confidence=0.9,
        evidence=evidence,
    ).handle(DecisionPolicy(min_confidence=0.8))


def rendered_result_payload(result) -> str:
    return f"{result.metadata} {result.warnings}"


def test_no_evidence_behavior_is_unchanged():
    result = handle_with(None)
    context = extract_evidence_context(None)

    assert result.action == "allow"
    assert result.metadata == {}
    assert result.warnings == []
    assert context.evidence_kind == "none"
    assert context.evidence_valid is False
    assert context.evidence_score is None
    assert context.metadata == {}
    assert context.warnings == ()


def test_old_sdk_evidence_is_recognized_and_preserves_behavior():
    evidence = ConfidenceEvidence(
        score=0.9,
        source="fixture",
        signals={"kind": "deterministic"},
        warnings=["weak_schema"],
        metadata={"case": "A"},
    )
    before = {
        "score": evidence.score,
        "source": evidence.source,
        "signals": dict(evidence.signals),
        "warnings": list(evidence.warnings),
        "metadata": dict(evidence.metadata),
    }

    result = handle_with(evidence)
    context = extract_evidence_context(evidence)

    assert context.evidence_kind == "sdk"
    assert context.evidence_valid is True
    assert context.evidence_score == 0.9
    assert result.metadata["evidence_kind"] == "sdk"
    assert result.metadata["evidence_valid"] is True
    assert result.metadata["evidence_score"] == 0.9
    assert result.metadata["evidence_source"] == "fixture"
    assert result.metadata["evidence_signals"] == {"kind": "deterministic"}
    assert result.metadata["evidence_metadata"] == {"case": "A"}
    assert result.metadata["evidence_warnings"] == ["weak_schema"]
    assert result.warnings == ["weak_schema"]
    assert before == {
        "score": evidence.score,
        "source": evidence.source,
        "signals": dict(evidence.signals),
        "warnings": list(evidence.warnings),
        "metadata": dict(evidence.metadata),
    }


def test_new_confidence_evidence_is_recognized_and_metadata_propagates():
    evidence = AuditConfidenceEvidence(
        evidence_id="ev_refund_001",
        boundary_id="refund_routing",
        score=0.82,
        sources=[EvidenceSource(source_type="schema_validation", status="passed")],
        warnings=["low_sample_size"],
        policy_id="refund_policy_v1",
        policy_hash="sha256:policy",
        input_hash="sha256:input",
        output_hash="sha256:output",
        metadata={"safe": "value"},
    ).with_hash()
    before = evidence.to_dict()

    result = handle_with(evidence)
    context = extract_evidence_context(evidence)

    assert context.evidence_kind == "confidence"
    assert context.evidence_valid is True
    assert context.evidence_score == 0.82
    assert result.metadata["evidence_kind"] == "confidence"
    assert result.metadata["evidence_valid"] is True
    assert result.metadata["evidence_score"] == 0.82
    assert result.metadata["evidence_id"] == "ev_refund_001"
    assert result.metadata["evidence_hash"] == evidence.evidence_hash
    assert result.metadata["evidence_boundary_id"] == "refund_routing"
    assert result.metadata["evidence_schema_version"] == "confidence-evidence/v1"
    assert result.metadata["evidence_policy_id"] == "refund_policy_v1"
    assert result.metadata["evidence_policy_hash"] == "sha256:policy"
    assert result.metadata["evidence_input_hash"] == "sha256:input"
    assert result.metadata["evidence_output_hash"] == "sha256:output"
    assert result.metadata["evidence_redaction_applied"] is True
    assert result.metadata["evidence_metadata"] == {"safe": "value"}
    assert result.metadata["evidence_warnings"] == ["low_sample_size"]
    assert result.warnings == ["low_sample_size"]
    assert evidence.to_dict() == before


def test_new_confidence_evidence_without_precomputed_hash_is_computed_without_mutation():
    evidence = AuditConfidenceEvidence(
        evidence_id="ev_refund_002",
        boundary_id="refund_routing",
        score=0.74,
        sources=[EvidenceSource(source_type="ensemble_agreement", status="warning")],
    )
    before = evidence.to_dict()

    result = handle_with(evidence)

    assert evidence.evidence_hash is None
    assert result.metadata["evidence_hash"] == evidence.compute_hash()
    assert "evidence_hash_unavailable" not in result.warnings
    assert evidence.to_dict() == before


def test_audit_like_evidence_with_unavailable_hash_is_visible():
    class HashUnavailableEvidence:
        score = 0.7
        evidence_id = "ev_no_hash"
        boundary_id = "refund_routing"
        schema_version = "confidence-evidence/v1"
        evidence_hash = None
        policy_id = None
        policy_hash = None
        input_hash = None
        output_hash = None
        redaction_applied = True
        warnings = []
        metadata = {}

        def compute_hash(self):
            raise RuntimeError("hash failed")

    result = handle_with(HashUnavailableEvidence())

    assert result.metadata["evidence_kind"] == "confidence"
    assert result.metadata["evidence_valid"] is True
    assert "evidence_hash" not in result.metadata
    assert "evidence_hash_unavailable" in result.warnings


def test_unknown_evidence_object_is_visible_but_not_trusted():
    @dataclass
    class UnknownEvidence:
        score: float = 0.7
        warnings: list[str] | None = None

    evidence = UnknownEvidence(warnings=["custom_warning"])

    result = handle_with(evidence)

    assert result.metadata["evidence_kind"] == "unknown"
    assert result.metadata["evidence_valid"] is False
    assert result.metadata["evidence_type"] == "UnknownEvidence"
    assert "evidence_score" not in result.metadata
    assert result.metadata["evidence_warnings"] == [
        "custom_warning",
        "unknown_evidence_shape",
    ]
    assert result.warnings == ["custom_warning", "unknown_evidence_shape"]


def test_malicious_repr_does_not_leak():
    class MaliciousRepr:
        def __repr__(self):
            return "SECRET_SHOULD_NOT_LEAK"

    result = handle_with(MaliciousRepr())
    rendered = rendered_result_payload(result)

    assert result.metadata["evidence_kind"] == "unknown"
    assert result.metadata["evidence_valid"] is False
    assert "unknown_evidence_shape" in result.warnings
    assert "SECRET_SHOULD_NOT_LEAK" not in rendered
    assert "object at 0x" not in rendered


@dataclass
class EvidenceLike:
    score: object
    warnings: object = None
    metadata: object = None


def test_malformed_evidence_like_score_is_rejected_without_raw_error():
    for score in (True, False, math.nan, math.inf, -math.inf, 1.1, -0.1):
        result = handle_with(EvidenceLike(score=score))

        assert result.metadata["evidence_kind"] == "unknown"
        assert result.metadata["evidence_valid"] is False
        assert "evidence_score" not in result.metadata
        assert "invalid_evidence_score" in result.warnings
        assert "AttributeError" not in rendered_result_payload(result)
        assert "ValueError" not in rendered_result_payload(result)
        assert "TypeError" not in rendered_result_payload(result)


def test_string_evidence_like_score_is_rejected():
    result = handle_with(EvidenceLike(score="0.8"))

    assert result.metadata["evidence_kind"] == "unknown"
    assert result.metadata["evidence_valid"] is False
    assert "evidence_score" not in result.metadata
    assert "invalid_evidence_score" in result.warnings


def test_object_evidence_like_score_is_rejected_without_repr_leak():
    class MaliciousScore:
        def __repr__(self):
            return "SECRET_SHOULD_NOT_LEAK"

    result = handle_with(EvidenceLike(score=MaliciousScore()))
    rendered = rendered_result_payload(result)

    assert result.metadata["evidence_kind"] == "unknown"
    assert result.metadata["evidence_valid"] is False
    assert "evidence_score" not in result.metadata
    assert "invalid_evidence_score" in result.warnings
    assert "SECRET_SHOULD_NOT_LEAK" not in rendered
    assert "object at 0x" not in rendered


def test_warning_normalization_accepts_list_and_tuple_and_dedupes():
    list_result = handle_with(EvidenceLike(score=0.5, warnings=["a", "b", "a"]))
    tuple_result = handle_with(EvidenceLike(score=0.5, warnings=("a", "b", "a")))

    assert list_result.warnings == ["a", "b", "unknown_evidence_shape"]
    assert tuple_result.warnings == ["a", "b", "unknown_evidence_shape"]


def test_malformed_warnings_do_not_call_repr_or_crash():
    class BadWarning:
        def __repr__(self):
            return "SECRET_SHOULD_NOT_LEAK"

    result = handle_with(EvidenceLike(score=0.5, warnings=[BadWarning()]))
    rendered = rendered_result_payload(result)

    assert "invalid_evidence_warnings" in result.warnings
    assert "SECRET_SHOULD_NOT_LEAK" not in rendered
    assert "object at 0x" not in rendered


def test_safe_sdk_metadata_propagates_and_unsafe_metadata_is_redacted():
    class SecretObject:
        def __repr__(self):
            return "SECRET_SHOULD_NOT_LEAK"

    evidence = ConfidenceEvidence(
        score=0.9,
        source="fixture",
        signals={"safe_signal": ["a", 1, 0.5, True, None]},
        metadata={
            "safe": {"nested": ["x", 2]},
            "prompt": "sensitive prompt",
            "custom": SecretObject(),
        },
    )
    before_metadata = dict(evidence.metadata)

    result = handle_with(evidence)
    rendered = rendered_result_payload(result)

    assert result.metadata["evidence_metadata"]["safe"] == {"nested": ["x", 2]}
    assert result.metadata["evidence_metadata"]["prompt"] == "[redacted]"
    assert result.metadata["evidence_metadata"]["custom"] == "[redacted]"
    assert "unsafe_evidence_metadata_redacted" in result.warnings
    assert "sensitive prompt" not in rendered
    assert "SECRET_SHOULD_NOT_LEAK" not in rendered
    assert evidence.metadata == before_metadata


def test_audit_metadata_with_raw_like_keys_is_redacted():
    evidence = AuditConfidenceEvidence(
        evidence_id="ev_sensitive",
        boundary_id="refund_routing",
        score=0.8,
        sources=[EvidenceSource(source_type="schema_validation", status="passed")],
        metadata={"raw_output": "sensitive model output", "safe": "ok"},
    )

    result = handle_with(evidence)
    rendered = rendered_result_payload(result)

    assert result.metadata["evidence_metadata"]["raw_output"] == "[redacted]"
    assert result.metadata["evidence_metadata"]["safe"] == "ok"
    assert "unsafe_evidence_metadata_redacted" in result.warnings
    assert "sensitive model output" not in rendered


def test_extract_evidence_context_is_immutable_enough_for_callers():
    context = extract_evidence_context(
        ConfidenceEvidence(score=0.9, source="fixture", warnings=["a"])
    )

    assert context.evidence_kind == "sdk"
    assert context.evidence_valid is True
    assert context.evidence_score == 0.9
    assert context.warnings == ("a",)
    try:
        context.metadata["new"] = "value"
    except TypeError:
        pass
    else:
        raise AssertionError("context metadata should be read-only")
