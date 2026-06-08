import pytest

from ledge_lang.sdk import ConfidenceEvidence, InvalidConfidenceError


def test_confidence_evidence_accepts_valid_score():
    evidence = ConfidenceEvidence(
        score=1.0,
        source="fixture",
        signals={"kind": "deterministic"},
        warnings=["synthetic"],
        metadata={"case": "ok"},
    )
    assert evidence.score == 1.0
    assert evidence.signals["kind"] == "deterministic"


def test_confidence_evidence_rejects_invalid_score():
    with pytest.raises(InvalidConfidenceError):
        ConfidenceEvidence(score=-0.1)
    with pytest.raises(InvalidConfidenceError):
        ConfidenceEvidence(score=1.1)


@pytest.mark.parametrize(
    "score",
    [
        float("nan"),
        float("inf"),
        float("-inf"),
        True,
        False,
    ],
)
def test_confidence_evidence_rejects_non_finite_and_bool_score(score):
    with pytest.raises(InvalidConfidenceError):
        ConfidenceEvidence(score=score)
