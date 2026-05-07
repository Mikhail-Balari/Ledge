"""
Ledge Model Comparison
======================
Runs the same Ledge program against two AI backends and compares their behaviour.

Usage:
    from ledge_lang.comparison import compare_models

    report = compare_models(
        program_source='classify(test_input) using ["urgent","normal"]',
        test_cases=[...],
        backend_a=openai_backend(),
        backend_b=anthropic_backend(),
        name_a="GPT-4",
        name_b="Claude",
    )
    print(report.more_conservative)   # "GPT-4" or "Claude"
    print(report.more_accurate)        # which one was right more often
    print(report.disagreements)        # cases where they gave different answers
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from .core_types import NOTHING, LedgeMap, _repr
from .calibration import (
    CalibrationReport, _inject_input, _extract_value, _values_equal, calibrate
)


# ── AuditStore-based migration analysis ──────────────────────────────────────

class ModelMigrationAnalyzer:
    """
    Analyzes the impact of switching from one model to another based on
    historical AuditStore outcomes for the same inputs.
    """

    def __init__(self, store):
        self.store = store

    def _decisions_by_hash(self, model: str,
                            program_id: Optional[str]) -> Tuple[List, Dict]:
        rows = self.store.query(program_id=program_id, model=model,
                                limit=1_000_000)
        lookup: Dict[str, Dict] = {}
        for r in sorted(rows, key=lambda x: x["timestamp"]):
            lookup[r["input_hash"]] = r   # keep most-recent per hash
        return rows, lookup

    def compare_models(self, model_a: str, model_b: str,
                        program_id: Optional[str] = None,
                        domain: Optional[str] = None) -> Dict:
        pid = program_id or domain

        rows_a, lookup_a = self._decisions_by_hash(model_a, pid)
        rows_b, lookup_b = self._decisions_by_hash(model_b, pid)

        common_hashes  = set(lookup_a.keys()) & set(lookup_b.keys())
        comparable_pairs = len(common_hashes)

        outcomes_a = [r for r in rows_a if r["outcome_correct"] is not None]
        outcomes_b = [r for r in rows_b if r["outcome_correct"] is not None]

        acc_a = (sum(1 for r in outcomes_a if r["outcome_correct"] == 1)
                 / len(outcomes_a)) if outcomes_a else None
        acc_b = (sum(1 for r in outcomes_b if r["outcome_correct"] == 1)
                 / len(outcomes_b)) if outcomes_b else None

        would_differ = 0
        critical_differences: List[Dict] = []

        for h in common_hashes:
            da, db = lookup_a[h], lookup_b[h]
            if da["outcome_correct"] is not None and db["outcome_correct"] is not None:
                if da["outcome_correct"] != db["outcome_correct"]:
                    would_differ += 1
                    critical_differences.append({
                        "input_hash":          h,
                        "model_a_correct":     bool(da["outcome_correct"]),
                        "model_b_correct":     bool(db["outcome_correct"]),
                        "model_a_confidence":  round(da["confidence"], 3),
                        "model_b_confidence":  round(db["confidence"], 3),
                    })

        diff_rate = (round(would_differ / comparable_pairs, 3)
                     if comparable_pairs > 0 else 0.0)

        if acc_a is not None and acc_b is not None:
            recommendation = (model_b if acc_b > acc_a
                              else model_a if acc_a > acc_b else None)
        else:
            recommendation = None

        return {
            "model_a":              model_a,
            "model_b":              model_b,
            "total_decisions_a":    len(rows_a),
            "total_decisions_b":    len(rows_b),
            "comparable_pairs":     comparable_pairs,
            "would_have_differed":  would_differ,
            "diff_rate":            diff_rate,
            "model_a_accuracy":     round(acc_a, 3) if acc_a is not None else None,
            "model_b_accuracy":     round(acc_b, 3) if acc_b is not None else None,
            "recommendation":       recommendation,
            "critical_differences": critical_differences,
            "safe_to_migrate":      diff_rate < 0.1,
        }

    def migration_risk(self, from_model: str, to_model: str,
                        program_id: Optional[str] = None) -> Dict:
        cmp = self.compare_models(from_model, to_model, program_id=program_id)

        would_improve = sum(
            1 for d in cmp["critical_differences"]
            if not d["model_a_correct"] and d["model_b_correct"]
        )
        would_regress = sum(
            1 for d in cmp["critical_differences"]
            if d["model_a_correct"] and not d["model_b_correct"]
        )

        acc_a, acc_b = cmp["model_a_accuracy"], cmp["model_b_accuracy"]
        net_change = (round(acc_b - acc_a, 3)
                      if acc_a is not None and acc_b is not None else None)

        dr = cmp["diff_rate"]
        if dr >= 0.3:
            risk_level = "HIGH"
        elif dr >= 0.1:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        if cmp["safe_to_migrate"]:
            rec = f"Safe to migrate from {from_model} to {to_model}."
        elif risk_level == "HIGH":
            rec = (f"High risk: {cmp['would_have_differed']} decisions would change. "
                   f"Test thoroughly before migrating.")
        else:
            rec = (f"Moderate risk: {cmp['would_have_differed']} decisions would change. "
                   f"Migrate with caution.")

        return {
            "risk_level":                   risk_level,
            "decisions_that_would_change":  cmp["would_have_differed"],
            "decisions_that_would_improve": would_improve,
            "decisions_that_would_regress": would_regress,
            "net_accuracy_change":          net_change,
            "recommendation":               rec,
        }


@dataclass
class ModelComparisonReport:
    """
    Result of running the same program against two AI backends.

    name_a / name_b:        display names for each backend
    accuracy_a / accuracy_b: fraction correct on cases with known expected
    avg_confidence_a / avg_confidence_b: mean stated confidence
    more_conservative:  which model produced lower avg confidence
    more_accurate:      which model was correct more often (None if tied)
    disagreements:      cases where the two models gave different answers
    a_only_correct:     cases where A was right and B was wrong
    b_only_correct:     cases where B was right and A was wrong
    agreement_rate:     fraction of cases where both models agree
    calibration_a / calibration_b: CalibrationReport for each (if expected provided)
    """
    name_a: str
    name_b: str
    accuracy_a: float
    accuracy_b: float
    avg_confidence_a: float
    avg_confidence_b: float
    more_conservative: Optional[str]   # name of model with lower avg confidence
    more_accurate: Optional[str]       # name of more accurate model, None if tied
    disagreements: List[Dict]
    a_only_correct: List[Dict]
    b_only_correct: List[Dict]
    agreement_rate: float
    calibration_a: Optional[CalibrationReport] = None
    calibration_b: Optional[CalibrationReport] = None
    results: List[Dict] = field(default_factory=list)

    def __repr__(self) -> str:
        return (
            f"ModelComparisonReport("
            f"{self.name_a} acc={self.accuracy_a:.1%} conf={self.avg_confidence_a:.1%} | "
            f"{self.name_b} acc={self.accuracy_b:.1%} conf={self.avg_confidence_b:.1%} | "
            f"disagree={len(self.disagreements)}/{len(self.results)})"
        )

    def summary(self) -> str:
        lines = [
            f"Model Comparison Report",
            f"  {self.name_a:<20} accuracy={self.accuracy_a:.1%}  avg_confidence={self.avg_confidence_a:.1%}",
            f"  {self.name_b:<20} accuracy={self.accuracy_b:.1%}  avg_confidence={self.avg_confidence_b:.1%}",
            f"",
            f"  More conservative:  {self.more_conservative or 'tied'}",
            f"  More accurate:      {self.more_accurate or 'tied'}",
            f"  Agreement rate:     {self.agreement_rate:.1%}",
            f"  Disagreements:      {len(self.disagreements)}",
            f"  Only {self.name_a} correct: {len(self.a_only_correct)}",
            f"  Only {self.name_b} correct: {len(self.b_only_correct)}",
        ]
        return "\n".join(lines)


def compare_models(
    program_source: str,
    test_cases: List[Dict],
    backend_a: Optional[Dict],
    backend_b: Optional[Dict],
    name_a: str = "model_a",
    name_b: str = "model_b",
) -> ModelComparisonReport:
    """
    Run program_source against two backends and compare their behaviour.

    program_source: Ledge program using `test_input` as input variable,
                    ending with an expression that returns Uncertain[T].
    test_cases: list of dicts with:
        "input"    — the input value
        "expected" — (optional) correct answer for accuracy measurement
        "key"      — (optional) map key to extract from Uncertain.value
    backend_a / backend_b: Ledge AI backend dicts
    name_a / name_b: display names for the report
    """
    from ledge_lang import run
    from ledge_lang.ai_types import Uncertain

    results = []
    disagreements = []
    a_only_correct = []
    b_only_correct = []

    for case in test_cases:
        inp = case.get("input", "")
        expected = case.get("expected", NOTHING)
        has_expected = expected is not NOTHING
        extract_key = case.get("key", None)

        injected = _inject_input(program_source, inp)

        val_a, conf_a = _run_one(injected, backend_a)
        val_b, conf_b = _run_one(injected, backend_b)

        pred_a = _extract_value(val_a, extract_key)
        pred_b = _extract_value(val_b, extract_key)

        correct_a = _values_equal(pred_a, expected) if has_expected else None
        correct_b = _values_equal(pred_b, expected) if has_expected else None
        agree = _values_equal(pred_a, pred_b)

        row = {
            "input": inp,
            "expected": expected,
            "predicted_a": pred_a,
            "predicted_b": pred_b,
            "confidence_a": conf_a,
            "confidence_b": conf_b,
            "correct_a": correct_a,
            "correct_b": correct_b,
            "agree": agree,
        }
        results.append(row)

        if not agree:
            disagreements.append(row)

        if has_expected:
            if correct_a and not correct_b:
                a_only_correct.append(row)
            elif correct_b and not correct_a:
                b_only_correct.append(row)

    n = len(results)
    agreement_rate = sum(1 for r in results if r["agree"]) / n if n else 1.0

    # Accuracy (only for cases with expected answers)
    cases_with_expected = [r for r in results if r["correct_a"] is not None]
    nk = len(cases_with_expected)
    accuracy_a = sum(1 for r in cases_with_expected if r["correct_a"]) / nk if nk else 0.0
    accuracy_b = sum(1 for r in cases_with_expected if r["correct_b"]) / nk if nk else 0.0

    avg_confidence_a = sum(r["confidence_a"] for r in results) / n if n else 0.0
    avg_confidence_b = sum(r["confidence_b"] for r in results) / n if n else 0.0

    # Which model is more conservative (lower confidence)?
    if abs(avg_confidence_a - avg_confidence_b) < 0.01:
        more_conservative = None  # essentially tied
    elif avg_confidence_a < avg_confidence_b:
        more_conservative = name_a
    else:
        more_conservative = name_b

    # Which model is more accurate?
    if accuracy_a > accuracy_b:
        more_accurate = name_a
    elif accuracy_b > accuracy_a:
        more_accurate = name_b
    else:
        more_accurate = None  # tied

    # Individual calibration reports (only if expected answers are present)
    cal_a = cal_b = None
    if cases_with_expected:
        cal_a = calibrate(program_source, test_cases, backend=backend_a)
        cal_b = calibrate(program_source, test_cases, backend=backend_b)

    return ModelComparisonReport(
        name_a=name_a,
        name_b=name_b,
        accuracy_a=accuracy_a,
        accuracy_b=accuracy_b,
        avg_confidence_a=avg_confidence_a,
        avg_confidence_b=avg_confidence_b,
        more_conservative=more_conservative,
        more_accurate=more_accurate,
        disagreements=disagreements,
        a_only_correct=a_only_correct,
        b_only_correct=b_only_correct,
        agreement_rate=agreement_rate,
        calibration_a=cal_a,
        calibration_b=cal_b,
        results=results,
    )


# ── Internal ──────────────────────────────────────────────────────────────────

def _run_one(injected_source: str, backend: Optional[Dict]):
    """Run once, return (value, confidence). Never raises."""
    from ledge_lang import run
    from ledge_lang.ai_types import Uncertain

    try:
        _, value = run(
            injected_source,
            output_fn=lambda x: None,
            ai_backend=backend,
            reset_audit=True,
        )
    except Exception:
        return NOTHING, 0.0

    if isinstance(value, Uncertain):
        return value.value, value.confidence
    if value is not None and value is not NOTHING:
        return value, 1.0
    return NOTHING, 0.0
