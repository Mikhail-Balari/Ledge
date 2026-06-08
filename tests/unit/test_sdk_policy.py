import pytest

from ledge_lang.sdk import DecisionPolicy, InvalidConfidenceError, PolicyValidationError


def test_policy_accepts_boundary_confidence_values():
    assert DecisionPolicy(min_confidence=0.0).min_confidence == 0.0
    assert DecisionPolicy(min_confidence=1.0).min_confidence == 1.0


def test_policy_rejects_invalid_min_confidence():
    with pytest.raises(InvalidConfidenceError):
        DecisionPolicy(min_confidence=-0.01)
    with pytest.raises(InvalidConfidenceError):
        DecisionPolicy(min_confidence=1.01)


@pytest.mark.parametrize(
    "min_confidence",
    [
        float("nan"),
        float("inf"),
        float("-inf"),
        True,
        False,
    ],
)
def test_policy_rejects_non_finite_and_bool_min_confidence(min_confidence):
    with pytest.raises(InvalidConfidenceError):
        DecisionPolicy(min_confidence=min_confidence)


def test_policy_normalizes_action_strings():
    policy = DecisionPolicy(
        min_confidence=0.7,
        on_low_confidence="Human_Review",
        on_missing_value="BLOCK",
        on_schema_error="allow",
    )
    assert policy.on_low_confidence == "human_review"
    assert policy.on_missing_value == "block"
    assert policy.on_schema_error == "allow"


def test_policy_rejects_invalid_actions():
    with pytest.raises(PolicyValidationError):
        DecisionPolicy(min_confidence=0.7, on_low_confidence="escalate")
