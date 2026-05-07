"""
Calibration Testing — pytest test suite

Tests that calibrate() correctly measures whether a model's declared
confidence corresponds to its actual accuracy.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import pytest
from ledge_lang.calibration import calibrate, CalibrationReport
from ledge_lang.core_types import LedgeMap, NOTHING


# ── Mock backends for controlled calibration scenarios ────────────────────────

def _classify_backend(predictions):
    """
    Mock backend where each prediction is {"value": label, "confidence": float}.
    predictions: list of dicts, consumed in order per classify() call.
    """
    call_idx = [0]

    def classify(text, labels):
        i = call_idx[0]
        call_idx[0] += 1
        if i < len(predictions):
            return predictions[i]   # dict with "value" + "confidence"
        return {"value": labels[0] if labels else NOTHING, "confidence": 0.0}

    return {"classify": classify}


# A program that classifies test_input and returns the Uncertain directly
CLASSIFY_PROGRAM = 'classify(test_input) using ["positive", "negative"]'

# A program that uses analyze — returns Uncertain[Map] with a "label" key
ANALYZE_PROGRAM = 'analyze(test_input) using sentiment'


def _analyze_backend(predictions):
    """Mock backend for analyze() with per-prediction confidence."""
    call_idx = [0]

    def analyze(text, mode):
        i = call_idx[0]
        call_idx[0] += 1
        if i < len(predictions):
            p = predictions[i]
            return LedgeMap({"label": p["label"], "confidence": p["confidence"]})
        return LedgeMap({"label": NOTHING, "confidence": 0.0})

    return {"analyze": analyze}


# ── CalibrationReport structure ───────────────────────────────────────────────

class TestCalibrationReport:

    def test_report_has_required_fields(self):
        report = calibrate(CLASSIFY_PROGRAM, [], backend=None)
        assert hasattr(report, "accuracy")
        assert hasattr(report, "avg_confidence")
        assert hasattr(report, "calibration_error")
        assert hasattr(report, "is_calibrated")
        assert hasattr(report, "total_cases")
        assert hasattr(report, "correct_cases")

    def test_empty_test_cases_returns_valid_report(self):
        report = calibrate(CLASSIFY_PROGRAM, [], backend=None)
        assert report.total_cases == 0
        assert report.accuracy == 0.0
        assert report.is_calibrated is True  # no error to detect

    def test_report_repr_shows_status(self):
        report = calibrate(CLASSIFY_PROGRAM, [], backend=None)
        r = repr(report)
        assert "CalibrationReport" in r


# ── Perfect calibration ───────────────────────────────────────────────────────

class TestPerfectCalibration:

    def test_perfect_calibration_is_detected(self):
        """Model correct 90% of time with confidence 0.9 → calibrated."""
        cases = [
            {"input": f"text_{i}", "expected": "positive"}
            for i in range(10)
        ]
        # 9 correct (confidence=0.9), 1 wrong (confidence=0.9)
        predictions = (
            [{"value": "positive", "confidence": 0.9}] * 9 +
            [{"value": "negative", "confidence": 0.9}]  # wrong answer
        )
        report = calibrate(CLASSIFY_PROGRAM, cases,
                           backend=_classify_backend(predictions))
        assert report.total_cases == 10
        assert report.correct_cases == 9
        assert abs(report.accuracy - 0.9) < 0.01
        assert abs(report.avg_confidence - 0.9) < 0.01
        assert report.calibration_error < 0.01
        assert report.is_calibrated is True

    def test_all_correct_high_confidence(self):
        """All 5 cases correct with confidence=0.92 → calibration_error=0.08 → calibrated."""
        cases = [{"input": f"t{i}", "expected": "positive"} for i in range(5)]
        predictions = [{"value": "positive", "confidence": 0.92}] * 5
        report = calibrate(CLASSIFY_PROGRAM, cases,
                           backend=_classify_backend(predictions))
        assert report.accuracy == 1.0
        assert abs(report.avg_confidence - 0.92) < 0.001
        assert abs(report.calibration_error - abs(1.0 - 0.92)) < 1e-9
        assert report.is_calibrated is True  # 0.08 < 0.1


# ── Overconfident model ───────────────────────────────────────────────────────

class TestOverconfidentModel:

    def test_overconfident_not_calibrated(self):
        """Model correct 50% with confidence 0.9 → big calibration error."""
        cases = [
            {"input": f"text_{i}", "expected": "positive" if i % 2 == 0 else "negative"}
            for i in range(10)
        ]
        # Alternating correct/wrong, all high confidence
        predictions = [
            {"value": "positive", "confidence": 0.9}
        ] * 10
        report = calibrate(CLASSIFY_PROGRAM, cases,
                           backend=_classify_backend(predictions))
        assert report.total_cases == 10
        assert abs(report.accuracy - 0.5) < 0.01
        assert abs(report.avg_confidence - 0.9) < 0.01
        assert abs(report.calibration_error - 0.4) < 0.01
        assert report.is_calibrated is False

    def test_underconfident_not_calibrated(self):
        """Model always correct but says confidence=0.5 → calibration error=0.5."""
        cases = [{"input": f"t{i}", "expected": "positive"} for i in range(4)]
        predictions = [{"value": "positive", "confidence": 0.5}] * 4
        report = calibrate(CLASSIFY_PROGRAM, cases,
                           backend=_classify_backend(predictions))
        assert report.accuracy == 1.0
        assert abs(report.avg_confidence - 0.5) < 0.001
        assert abs(report.calibration_error - 0.5) < 0.001
        assert report.is_calibrated is False


# ── No backend (safety invariant) ────────────────────────────────────────────

class TestNoBackend:

    def test_no_backend_zero_confidence(self):
        """Without backend: confidence=0.0 on all cases."""
        cases = [{"input": "x", "expected": "positive"}]
        report = calibrate(CLASSIFY_PROGRAM, cases, backend=None)
        assert report.avg_confidence == 0.0

    def test_no_backend_nothing_predicted(self):
        """Without backend: predicted value is nothing → all wrong."""
        cases = [{"input": "x", "expected": "positive"}]
        report = calibrate(CLASSIFY_PROGRAM, cases, backend=None)
        assert report.correct_cases == 0
        assert report.accuracy == 0.0


# ── Analyze-based calibration (with map key extraction) ───────────────────────

class TestAnalyzeCalibration:

    def test_analyze_calibration_with_key(self):
        """Calibrate on analyze() output, extracting a specific map key."""
        cases = [
            {"input": "love this", "expected": "positive", "key": "label"},
            {"input": "hate this", "expected": "negative", "key": "label"},
            {"input": "neutral",   "expected": "positive", "key": "label"},  # wrong
        ]
        predictions = [
            {"label": "positive", "confidence": 0.85},
            {"label": "negative", "confidence": 0.85},
            {"label": "negative", "confidence": 0.85},  # wrong label returned
        ]
        report = calibrate(ANALYZE_PROGRAM, cases,
                           backend=_analyze_backend(predictions))
        assert report.total_cases == 3
        assert report.correct_cases == 2
        assert abs(report.accuracy - 2/3) < 0.01


# ── Per-case results ──────────────────────────────────────────────────────────

class TestPerCaseResults:

    def test_results_contain_all_cases(self):
        cases = [{"input": f"t{i}", "expected": "positive"} for i in range(5)]
        predictions = [{"value": "positive", "confidence": 0.8}] * 5
        report = calibrate(CLASSIFY_PROGRAM, cases,
                           backend=_classify_backend(predictions))
        assert len(report.results) == 5

    def test_results_have_correct_flag(self):
        cases = [
            {"input": "good", "expected": "positive"},
            {"input": "bad",  "expected": "positive"},  # wrong: backend returns negative
        ]
        predictions = [
            {"value": "positive", "confidence": 0.9},
            {"value": "negative", "confidence": 0.9},
        ]
        report = calibrate(CLASSIFY_PROGRAM, cases,
                           backend=_classify_backend(predictions))
        assert report.results[0]["correct"] is True
        assert report.results[1]["correct"] is False
