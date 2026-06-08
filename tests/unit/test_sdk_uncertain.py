import pytest

from ledge_lang.sdk import (
    ConfidenceEvidence,
    DecisionPolicy,
    InvalidConfidenceError,
    Uncertain,
    UnsafeUnwrapError,
)


def test_uncertain_accepts_boundary_confidence_values():
    assert Uncertain(value="zero", confidence=0.0).confidence == 0.0
    assert Uncertain(value="one", confidence=1.0).confidence == 1.0


def test_uncertain_rejects_invalid_confidence():
    with pytest.raises(InvalidConfidenceError):
        Uncertain(value="bad", confidence=-0.1)
    with pytest.raises(InvalidConfidenceError):
        Uncertain(value="bad", confidence=1.1)


@pytest.mark.parametrize(
    "confidence",
    [
        float("nan"),
        float("inf"),
        float("-inf"),
        True,
        False,
    ],
)
def test_uncertain_rejects_non_finite_and_bool_confidence(confidence):
    with pytest.raises(InvalidConfidenceError):
        Uncertain(value="bad", confidence=confidence)


def test_is_usable_requires_value_and_threshold():
    policy = DecisionPolicy(min_confidence=0.8)
    assert Uncertain(value="ok", confidence=0.8).is_usable(policy)
    assert not Uncertain(value="ok", confidence=0.79).is_usable(policy)
    assert not Uncertain(value=None, confidence=0.9).is_usable(policy)


def test_is_usable_can_allow_missing_value():
    policy = DecisionPolicy(min_confidence=0.8, allow_missing_value=True)
    assert Uncertain(value=None, confidence=0.9).is_usable(policy)


def test_handle_allows_when_confidence_meets_threshold():
    policy = DecisionPolicy(min_confidence=0.8, name="demo")
    result = Uncertain(value="refund", confidence=0.91).handle(policy)
    assert result.action == "allow"
    assert result.allowed is True
    assert result.value == "refund"
    assert result.policy_name == "demo"


def test_handle_routes_low_confidence_to_human_review():
    policy = DecisionPolicy(min_confidence=0.8)
    result = Uncertain(value="refund", confidence=0.4).handle(policy)
    assert result.action == "human_review"
    assert result.allowed is False
    assert "low confidence" in result.reason


def test_handle_can_override_low_confidence_action():
    policy = DecisionPolicy(min_confidence=0.8)
    result = Uncertain(value="refund", confidence=0.4).handle(
        policy,
        on_low_confidence="block",
    )
    assert result.action == "block"
    assert result.allowed is False


def test_handle_blocks_missing_value_when_policy_disallows_missing():
    policy = DecisionPolicy(min_confidence=0.8)
    result = Uncertain(value=None, confidence=0.9).handle(policy)
    assert result.action == "block"
    assert result.allowed is False
    assert result.value is None
    assert "missing value" in result.reason


def test_handle_includes_warnings_metadata_and_evidence():
    policy = DecisionPolicy(min_confidence=0.8)
    evidence = ConfidenceEvidence(
        score=0.9,
        source="fixture",
        warnings=["weak schema"],
    )
    result = Uncertain(
        value="ok",
        confidence=0.9,
        source="fake",
        warnings=["synthetic"],
        metadata={"case": "A"},
        evidence=evidence,
    ).handle(policy)
    assert result.warnings == ["synthetic", "weak schema"]
    assert result.metadata["case"] == "A"
    assert result.metadata["source"] == "fake"
    assert result.metadata["evidence_score"] == 0.9
    assert result.metadata["evidence_source"] == "fixture"


def test_unsafe_unwrap_succeeds_with_non_empty_reason():
    assert Uncertain(value="ok", confidence=0.0).unsafe_unwrap("manual debug") == "ok"


def test_unsafe_unwrap_requires_reason():
    with pytest.raises(UnsafeUnwrapError):
        Uncertain(value="ok", confidence=1.0).unsafe_unwrap("")
    with pytest.raises(UnsafeUnwrapError):
        Uncertain(value="ok", confidence=1.0).unsafe_unwrap("   ")


def test_unsafe_unwrap_fails_when_value_missing():
    with pytest.raises(UnsafeUnwrapError):
        Uncertain(value=None, confidence=1.0).unsafe_unwrap("manual debug")
