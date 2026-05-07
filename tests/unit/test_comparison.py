"""
Model Comparison — pytest test suite

Tests that compare_models() correctly identifies differences between two AI backends.
The core use case: a medical system operator wants to know if switching from
GPT-4 to Claude changes the triage behaviour of their system.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import pytest
from ledge_lang.comparison import compare_models, ModelComparisonReport
from ledge_lang.core_types import LedgeMap, NOTHING


# ── Mock backends ────────────────────────────────────────────────────────────

def _classify_backend(answers, confidence=0.9):
    """Backend that returns fixed answers in order."""
    call_idx = [0]

    def classify(text, labels):
        i = call_idx[0]
        call_idx[0] += 1
        ans = answers[i % len(answers)]
        return {"value": ans, "confidence": confidence}

    return {"classify": classify}


PROGRAM = 'classify(test_input) using ["urgent", "normal", "routine"]'

CASES = [
    {"input": "chest pain, shortness of breath", "expected": "urgent"},
    {"input": "mild headache",                   "expected": "routine"},
    {"input": "high fever, rash",                "expected": "urgent"},
    {"input": "annual checkup",                  "expected": "routine"},
]


# ── Report structure ──────────────────────────────────────────────────────────

class TestComparisonReportStructure:

    def test_report_has_required_fields(self):
        report = compare_models(PROGRAM, CASES,
                                backend_a=_classify_backend(["urgent"] * 4),
                                backend_b=_classify_backend(["urgent"] * 4))
        assert hasattr(report, "more_conservative")
        assert hasattr(report, "more_accurate")
        assert hasattr(report, "disagreements")
        assert hasattr(report, "a_only_correct")
        assert hasattr(report, "b_only_correct")
        assert hasattr(report, "agreement_rate")
        assert hasattr(report, "accuracy_a")
        assert hasattr(report, "accuracy_b")
        assert hasattr(report, "avg_confidence_a")
        assert hasattr(report, "avg_confidence_b")

    def test_report_results_length(self):
        report = compare_models(PROGRAM, CASES,
                                backend_a=_classify_backend(["urgent"] * 4),
                                backend_b=_classify_backend(["urgent"] * 4))
        assert len(report.results) == len(CASES)

    def test_empty_cases(self):
        report = compare_models(PROGRAM, [],
                                backend_a=_classify_backend(["urgent"]),
                                backend_b=_classify_backend(["urgent"]))
        assert report.agreement_rate == 1.0
        assert len(report.disagreements) == 0


# ── Conservative model detection ─────────────────────────────────────────────

class TestConservativeDetection:

    def test_lower_confidence_is_more_conservative(self):
        """Model A with confidence=0.7 is more conservative than B with 0.9."""
        report = compare_models(
            PROGRAM, CASES,
            backend_a=_classify_backend(["urgent"] * 4, confidence=0.7),
            backend_b=_classify_backend(["urgent"] * 4, confidence=0.9),
            name_a="cautious_model",
            name_b="confident_model",
        )
        assert report.more_conservative == "cautious_model"

    def test_tied_confidence_returns_none(self):
        report = compare_models(
            PROGRAM, CASES,
            backend_a=_classify_backend(["urgent"] * 4, confidence=0.85),
            backend_b=_classify_backend(["urgent"] * 4, confidence=0.85),
        )
        assert report.more_conservative is None

    def test_avg_confidence_values_are_correct(self):
        report = compare_models(
            PROGRAM, CASES,
            backend_a=_classify_backend(["urgent"] * 4, confidence=0.7),
            backend_b=_classify_backend(["urgent"] * 4, confidence=0.9),
        )
        assert abs(report.avg_confidence_a - 0.7) < 0.01
        assert abs(report.avg_confidence_b - 0.9) < 0.01


# ── Accuracy comparison ───────────────────────────────────────────────────────

class TestAccuracyComparison:

    def test_more_accurate_model_detected(self):
        """Model A: 4/4 correct. Model B: 2/4 correct."""
        a_answers = ["urgent", "routine", "urgent", "routine"]  # all correct
        b_answers = ["urgent", "urgent",  "urgent", "urgent"]   # 2 wrong
        report = compare_models(
            PROGRAM, CASES,
            backend_a=_classify_backend(a_answers),
            backend_b=_classify_backend(b_answers),
            name_a="accurate",
            name_b="imprecise",
        )
        assert report.more_accurate == "accurate"
        assert report.accuracy_a == 1.0
        assert abs(report.accuracy_b - 0.5) < 0.01

    def test_tied_accuracy_returns_none(self):
        answers = ["urgent", "routine", "urgent", "routine"]  # all correct
        report = compare_models(
            PROGRAM, CASES,
            backend_a=_classify_backend(answers),
            backend_b=_classify_backend(answers),
        )
        assert report.more_accurate is None

    def test_accuracy_without_expected_is_zero(self):
        """Cases without expected: accuracy = 0 (undefined, not computed)."""
        no_expected = [{"input": "symptom X"} for _ in range(3)]
        report = compare_models(
            PROGRAM, no_expected,
            backend_a=_classify_backend(["urgent"] * 3),
            backend_b=_classify_backend(["normal"] * 3),
        )
        assert report.accuracy_a == 0.0
        assert report.accuracy_b == 0.0


# ── Disagreement detection ────────────────────────────────────────────────────

class TestDisagreements:

    def test_perfect_agreement(self):
        answers = ["urgent", "routine", "urgent", "routine"]
        report = compare_models(
            PROGRAM, CASES,
            backend_a=_classify_backend(answers),
            backend_b=_classify_backend(answers),
        )
        assert report.agreement_rate == 1.0
        assert len(report.disagreements) == 0

    def test_all_disagree(self):
        a_answers = ["urgent",  "urgent",  "urgent",  "urgent"]
        b_answers = ["routine", "routine", "routine", "routine"]
        report = compare_models(
            PROGRAM, CASES,
            backend_a=_classify_backend(a_answers),
            backend_b=_classify_backend(b_answers),
        )
        assert report.agreement_rate == 0.0
        assert len(report.disagreements) == 4

    def test_partial_disagreement(self):
        a_answers = ["urgent",  "routine", "urgent",  "routine"]
        b_answers = ["urgent",  "normal",  "urgent",  "routine"]  # case 2 differs
        report = compare_models(
            PROGRAM, CASES,
            backend_a=_classify_backend(a_answers),
            backend_b=_classify_backend(b_answers),
        )
        assert len(report.disagreements) == 1
        assert abs(report.agreement_rate - 3/4) < 0.01

    def test_a_only_correct(self):
        """Cases where A is correct and B is wrong."""
        a_answers = ["urgent", "routine", "urgent", "routine"]  # all correct
        b_answers = ["urgent", "urgent",  "urgent", "urgent"]   # cases 2,4 wrong
        report = compare_models(
            PROGRAM, CASES,
            backend_a=_classify_backend(a_answers),
            backend_b=_classify_backend(b_answers),
        )
        assert len(report.a_only_correct) == 2
        assert len(report.b_only_correct) == 0

    def test_b_only_correct(self):
        """Cases where B is correct and A is wrong."""
        a_answers = ["urgent", "urgent",  "urgent", "urgent"]   # cases 2,4 wrong
        b_answers = ["urgent", "routine", "urgent", "routine"]  # all correct
        report = compare_models(
            PROGRAM, CASES,
            backend_a=_classify_backend(a_answers),
            backend_b=_classify_backend(b_answers),
        )
        assert len(report.b_only_correct) == 2
        assert len(report.a_only_correct) == 0


# ── No backend (safety invariant) ────────────────────────────────────────────

class TestNoBackend:

    def test_no_backend_zero_confidence(self):
        report = compare_models(PROGRAM, CASES,
                                backend_a=None, backend_b=None)
        assert report.avg_confidence_a == 0.0
        assert report.avg_confidence_b == 0.0

    def test_real_vs_no_backend_difference(self):
        """A real backend vs no backend shows clear accuracy difference."""
        real = _classify_backend(["urgent", "routine", "urgent", "routine"])
        report = compare_models(PROGRAM, CASES,
                                backend_a=real, backend_b=None,
                                name_a="real", name_b="no_backend")
        assert report.accuracy_a > report.accuracy_b
        assert report.more_accurate == "real"


# ── Medical use-case: changing model changes triage ─────────────────────────

class TestMedicalUseCase:

    def test_conservative_model_escalates_more(self):
        """
        A conservative triage model marks 'chest pain' as urgent even with
        low-confidence symptoms. An aggressive model might classify as normal.
        This test demonstrates the semantic difference visible to a doctor.
        """
        # Conservative GPT: always marks ambiguous cases as urgent (high recall)
        gpt_answers = ["urgent", "urgent", "urgent", "urgent"]   # over-escalates
        # Claude: more precise
        claude_answers = ["urgent", "routine", "urgent", "routine"]  # accurate

        report = compare_models(
            PROGRAM, CASES,
            backend_a=_classify_backend(gpt_answers,  confidence=0.6),
            backend_b=_classify_backend(claude_answers, confidence=0.85),
            name_a="GPT-conservative",
            name_b="Claude-precise",
        )

        # GPT is more conservative (lower confidence and over-escalates)
        assert report.more_conservative == "GPT-conservative"
        # Claude is more accurate
        assert report.more_accurate == "Claude-precise"
        # There ARE cases where they disagree
        assert len(report.disagreements) > 0
        # Those cases tell the doctor exactly where the models differ
        for d in report.disagreements:
            assert d["predicted_a"] != d["predicted_b"]
