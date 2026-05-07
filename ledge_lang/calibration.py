"""
Ledge Calibration Testing
=========================
Measures whether a model's declared confidence matches its actual accuracy.

A model is well-calibrated if, across predictions where it says confidence=X,
it's actually correct roughly X*100% of the time.

Usage:
    from ledge_lang.calibration import calibrate

    report = calibrate(
        program_source='classify(test_input) using ["positive", "negative"]',
        test_cases=[
            {"input": "I love this!", "expected": "positive"},
            {"input": "Terrible experience", "expected": "negative"},
        ],
        backend=my_backend
    )
    print(report.is_calibrated)  # True if error < 0.1
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

from .core_types import NOTHING, LedgeMap, _repr


@dataclass
class CalibrationReport:
    """
    Result of a calibration test run.

    accuracy:           fraction of test cases answered correctly
    avg_confidence:     mean confidence declared by the model across all cases
    calibration_error:  |accuracy - avg_confidence|  (simplified ECE)
    is_calibrated:      True if calibration_error < 0.1
    total_cases:        number of test cases run
    correct_cases:      number of correct predictions
    results:            per-case detail list
    """
    accuracy: float
    avg_confidence: float
    calibration_error: float
    is_calibrated: bool
    total_cases: int
    correct_cases: int
    results: List[Dict] = field(default_factory=list)

    def __repr__(self) -> str:
        status = "CALIBRATED" if self.is_calibrated else "NOT CALIBRATED"
        return (
            f"CalibrationReport({status}: accuracy={self.accuracy:.1%}, "
            f"avg_confidence={self.avg_confidence:.1%}, "
            f"error={self.calibration_error:.3f}, "
            f"n={self.total_cases})"
        )

    def summary(self) -> str:
        lines = [
            f"Calibration Report",
            f"  Total cases:        {self.total_cases}",
            f"  Correct:            {self.correct_cases}",
            f"  Accuracy:           {self.accuracy:.1%}",
            f"  Avg confidence:     {self.avg_confidence:.1%}",
            f"  Calibration error:  {self.calibration_error:.3f}",
            f"  Is calibrated:      {self.is_calibrated}",
        ]
        return "\n".join(lines)


def calibrate(
    program_source: str,
    test_cases: List[Dict],
    backend: Optional[Dict] = None,
) -> CalibrationReport:
    """
    Run program_source against each test case and measure calibration.

    The program should:
    1. Use the variable `test_input` to receive each case's input
    2. End with an expression that returns Uncertain[T] (not `show`)

    test_cases: list of dicts with keys:
        "input"    — the input value (str, number)
        "expected" — the correct answer to compare against
        "key"      — optional: if Uncertain.value is a map, extract this key
                     before comparing to expected
    backend: Ledge AI backend dict (see ledge_lang.backends)
    """
    from ledge_lang import run
    from ledge_lang.ai_types import Uncertain

    results = []

    for case in test_cases:
        inp = case.get("input", "")
        expected = case.get("expected", NOTHING)
        extract_key = case.get("key", None)

        injected = _inject_input(program_source, inp)

        try:
            _, value = run(
                injected,
                output_fn=lambda x: None,
                ai_backend=backend,
                reset_audit=True,
            )
        except Exception as e:
            results.append({
                "input": inp,
                "expected": expected,
                "predicted": NOTHING,
                "confidence": 0.0,
                "correct": False,
                "error": str(e),
            })
            continue

        if isinstance(value, Uncertain):
            raw = value.value
            confidence = value.confidence
        else:
            raw = value
            confidence = 1.0 if (value is not None and value is not NOTHING) else 0.0

        predicted = _extract_value(raw, extract_key)
        correct = _values_equal(predicted, expected)

        results.append({
            "input": inp,
            "expected": expected,
            "predicted": predicted,
            "confidence": confidence,
            "correct": correct,
        })

    if not results:
        return CalibrationReport(
            accuracy=0.0, avg_confidence=0.0,
            calibration_error=0.0, is_calibrated=True,
            total_cases=0, correct_cases=0, results=[],
        )

    n = len(results)
    correct_cases = sum(1 for r in results if r["correct"])
    accuracy = correct_cases / n
    avg_confidence = sum(r["confidence"] for r in results) / n
    calibration_error = abs(accuracy - avg_confidence)
    is_calibrated = calibration_error < 0.1

    return CalibrationReport(
        accuracy=accuracy,
        avg_confidence=avg_confidence,
        calibration_error=calibration_error,
        is_calibrated=is_calibrated,
        total_cases=n,
        correct_cases=correct_cases,
        results=results,
    )


# ── Internal helpers ──────────────────────────────────────────────────────────

class DomainCalibrator:
    """
    Learns real model accuracy per domain from AuditStore historical outcomes
    and suggests calibrated confidence thresholds.

    If a model reports 0.9 confidence but is only correct 60% of the time in
    a given domain, the threshold required to guarantee 85% accuracy is higher.
    """

    def __init__(self, store):
        self.store = store

    def _outcomes_for(self, model: str, domain: str) -> List[Dict]:
        rows = self.store.query(program_id=domain, model=model, limit=1_000_000)
        return [r for r in rows if r["outcome_correct"] is not None]

    def get_calibrated_threshold(self, model: str, domain: str,
                                  desired_accuracy: float = 0.85,
                                  min_samples: int = 10) -> Dict:
        outcomes = self._outcomes_for(model, domain)

        if len(outcomes) < min_samples:
            return {
                "threshold": 0.85,
                "calibrated": False,
                "sample_size": len(outcomes),
                "actual_accuracy_at_threshold": None,
                "warning": (
                    f"Insufficient data: {len(outcomes)} samples "
                    f"(need {min_samples})"
                ),
            }

        confidences = sorted(set(r["confidence"] for r in outcomes))
        candidates: List[Tuple[float, float, int]] = []
        for conf in confidences:
            subset = [r for r in outcomes if r["confidence"] >= conf]
            if subset:
                acc = sum(1 for r in subset if r["outcome_correct"] == 1) / len(subset)
                candidates.append((conf, acc, len(subset)))

        # Lowest threshold where accuracy >= desired
        for conf, acc, count in candidates:
            if acc >= desired_accuracy:
                return {
                    "threshold": round(conf, 3),
                    "calibrated": True,
                    "sample_size": len(outcomes),
                    "actual_accuracy_at_threshold": round(acc, 3),
                    "warning": None,
                }

        # desired_accuracy not achievable — return threshold with best accuracy
        best = max(candidates, key=lambda x: x[1])
        return {
            "threshold": round(best[0], 3),
            "calibrated": True,
            "sample_size": len(outcomes),
            "actual_accuracy_at_threshold": round(best[1], 3),
            "warning": (
                f"Desired accuracy {desired_accuracy:.0%} not achievable; "
                f"best is {best[1]:.1%}"
            ),
        }

    def get_calibration_report(self, model: str, domain: str) -> List[Dict]:
        outcomes = self._outcomes_for(model, domain)
        buckets = []
        ranges = [
            (0.0, 0.5, "0.0-0.5"),
            (0.5, 0.6, "0.5-0.6"),
            (0.6, 0.7, "0.6-0.7"),
            (0.7, 0.8, "0.7-0.8"),
            (0.8, 0.9, "0.8-0.9"),
            (0.9, 1.001, "0.9-1.0"),
        ]
        for lo, hi, label in ranges:
            subset = [r for r in outcomes if lo <= r["confidence"] < hi]
            if not subset:
                continue
            mid = (lo + min(hi, 1.0)) / 2
            acc = sum(1 for r in subset if r["outcome_correct"] == 1) / len(subset)
            buckets.append({
                "range": label,
                "count": len(subset),
                "accuracy": round(acc, 3),
                "calibration_error": round(abs(acc - mid), 3),
            })
        return buckets

    def get_calibration_metrics(self, model: str, domain: str,
                                min_samples: int = 10) -> Optional[Dict]:
        """
        Returns statistical calibration quality metrics.

        Brier Score: mean squared error between declared confidence and binary
        outcome (0=wrong, 1=correct). Perfect=0.0, random=0.25.

        ECE: weighted average of |bucket_confidence - bucket_accuracy|
        across 10 buckets of 0.1 width.

        False Accept Rate: decisions where confidence>=threshold but wrong.
        False Reject Rate: decisions where confidence<threshold but correct.

        Returns None if fewer than min_samples outcomes are available.
        """
        outcomes = self._outcomes_for(model, domain)
        if len(outcomes) < min_samples:
            return None

        n = len(outcomes)

        # Brier score
        brier = sum(
            (r["confidence"] - r["outcome_correct"]) ** 2 for r in outcomes
        ) / n

        # ECE — 10 buckets of 0.1 width
        buckets: Dict[float, List] = {}
        for r in outcomes:
            b = min(int(r["confidence"] * 10) / 10, 0.9)
            if b not in buckets:
                buckets[b] = []
            buckets[b].append(r)

        ece = 0.0
        reliability_table: List[Dict] = []
        for b_start in sorted(buckets.keys()):
            bucket    = buckets[b_start]
            mean_conf = sum(r["confidence"] for r in bucket) / len(bucket)
            real_acc  = sum(r["outcome_correct"] for r in bucket) / len(bucket)
            cal_error = abs(mean_conf - real_acc)
            ece      += (len(bucket) / n) * cal_error
            reliability_table.append({
                "bucket":            f"{b_start:.1f}-{b_start + 0.1:.1f}",
                "count":             len(bucket),
                "mean_confidence":   round(mean_conf, 3),
                "real_accuracy":     round(real_acc, 3),
                "calibration_error": round(cal_error, 3),
            })

        # False Accept / Reject rates
        threshold = self.get_calibrated_threshold(model, domain)["threshold"]
        above = [r for r in outcomes if r["confidence"] >= threshold]
        below = [r for r in outcomes if r["confidence"] < threshold]
        false_accept = [r for r in above if not r["outcome_correct"]]
        false_reject = [r for r in below if r["outcome_correct"]]
        far = len(false_accept) / len(above) if above else None
        frr = len(false_reject) / len(below) if below else None

        # Overconfidence: high-bucket accuracy vs declared confidence
        high_bucket = [r for r in outcomes if r["confidence"] >= 0.9]
        overconfident = False
        note = "Well calibrated"
        if high_bucket:
            high_acc = (
                sum(r["outcome_correct"] for r in high_bucket) / len(high_bucket)
            )
            if high_acc < 0.8:
                overconfident = True
                note = (
                    f"Overconfident in 0.9-1.0 range: declares 0.9+ "
                    f"but achieves {high_acc:.0%}"
                )

        return {
            "brier_score":       round(brier, 4),
            "ece":               round(ece, 4),
            "false_accept_rate": round(far, 4) if far is not None else None,
            "false_reject_rate": round(frr, 4) if frr is not None else None,
            "sample_size":       n,
            "threshold_used":    threshold,
            "reliability_table": reliability_table,
            "well_calibrated":   ece < 0.1 and not overconfident,
            "calibration_note":  note,
        }

    def is_model_trustworthy(self, model: str, domain: str,
                              min_accuracy: float = 0.80,
                              min_samples: int = 10) -> bool:
        outcomes = self._outcomes_for(model, domain)
        if len(outcomes) < min_samples:
            return False
        acc = sum(1 for r in outcomes if r["outcome_correct"] == 1) / len(outcomes)
        return acc >= min_accuracy


def _inject_input(program_source: str, inp: Any) -> str:
    """Prepend `define test_input as <inp>` to the program."""
    if isinstance(inp, bool):
        ledge_val = "true" if inp else "false"
    elif isinstance(inp, str):
        escaped = inp.replace("\\", "\\\\").replace('"', '\\"')
        ledge_val = f'"{escaped}"'
    elif isinstance(inp, (int, float)):
        ledge_val = str(inp)
    else:
        escaped = str(inp).replace("\\", "\\\\").replace('"', '\\"')
        ledge_val = f'"{escaped}"'
    return f"define test_input as {ledge_val}\n{program_source}"


def _extract_value(value: Any, key: Optional[str]) -> Any:
    """Extract a sub-value if key is given and value is a map."""
    if key is None:
        return value
    if isinstance(value, (dict, LedgeMap)):
        return value.get(key, NOTHING)
    return value


def _values_equal(predicted: Any, expected: Any) -> bool:
    """Flexible equality: case-insensitive string comparison."""
    if predicted is NOTHING or predicted is None:
        return expected is NOTHING or expected is None
    if expected is NOTHING or expected is None:
        return False
    try:
        return str(predicted).strip().lower() == str(expected).strip().lower()
    except Exception:
        return predicted == expected
