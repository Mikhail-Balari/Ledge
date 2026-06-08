import pytest

from ledge_lang.sdk import DecisionResult, InvalidConfidenceError


def test_decision_result_sets_allowed_for_allow():
    result = DecisionResult(
        action="allow",
        allowed=False,
        value="ok",
        confidence=0.9,
        reason="test",
    )
    assert result.allowed is True


def test_decision_result_sets_not_allowed_for_review_or_block():
    review = DecisionResult(
        action="human_review",
        allowed=True,
        value="maybe",
        confidence=0.5,
        reason="test",
    )
    block = DecisionResult(
        action="block",
        allowed=True,
        value=None,
        confidence=0.0,
        reason="test",
    )
    assert review.allowed is False
    assert block.allowed is False


def test_decision_result_accepts_boundary_confidence_values():
    zero = DecisionResult(
        action="block",
        allowed=True,
        value=None,
        confidence=0.0,
        reason="test",
    )
    one = DecisionResult(
        action="allow",
        allowed=False,
        value="ok",
        confidence=1.0,
        reason="test",
    )
    assert zero.confidence == 0.0
    assert one.confidence == 1.0


@pytest.mark.parametrize(
    "confidence",
    [
        -0.1,
        1.1,
        float("nan"),
        float("inf"),
        float("-inf"),
        True,
        False,
    ],
)
def test_decision_result_rejects_invalid_non_finite_and_bool_confidence(confidence):
    with pytest.raises(InvalidConfidenceError):
        DecisionResult(
            action="allow",
            allowed=False,
            value="ok",
            confidence=confidence,
            reason="test",
        )
