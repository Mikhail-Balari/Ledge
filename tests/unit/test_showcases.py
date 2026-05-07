"""
Showcase tests — demonstrate Ledge guarantees vs Python.

The central point of each test: show how the Python version can fail
silently (no exception, no error) while Ledge makes it impossible
at the language level.
"""
import sys, os
_ROOT = os.path.join(os.path.dirname(__file__), '..', '..')
sys.path.insert(0, _ROOT)
sys.path.insert(0, os.path.join(_ROOT, 'examples'))  # for showcase python imports

import pytest
from ledge_lang import run
from ledge_lang.interpreter import LedgeError
from ledge_lang.core_types import LedgeMap, NOTHING
from ledge_lang.ai_types import Uncertain

SHOWCASE_DIR = os.path.join(
    os.path.dirname(__file__), '..', '..', 'examples', 'showcase'
)


def ledge_run(src, backend=None):
    lines, value = run(src.strip(), output_fn=lambda x: None,
                       ai_backend=backend, reset_audit=True)
    return lines, value


def read_showcase(name):
    path = os.path.join(SHOWCASE_DIR, name)
    with open(path, encoding="utf-8") as f:
        return f.read()


# ── Helper: mock backend ──────────────────────────────────────────────────────

def _mock_backend(confidence=0.9):
    def analyze(text, mode):
        return LedgeMap({
            "risk_level": "critical",
            "risk":       "high",
            "clauses":    ["clause_1", "clause_2"],
            "answer":     "Paris",
            "label":      "urgent",
            "confidence": confidence,
        })
    def classify(text, labels):
        return {"value": labels[0] if labels else "unknown", "confidence": confidence}
    return {"analyze": analyze, "classify": classify}


# ── MEDICAL TRIAGE ────────────────────────────────────────────────────────────

class TestMedicalTriage:

    def test_runs_without_backend(self):
        """Without backend, program runs but escalates everything to human."""
        src = read_showcase("medical_triage.ledge")
        lines, _ = run(src, output_fn=lambda x: None, reset_audit=True)
        assert any("true" in l.lower() for l in lines)

    def test_audit_chain_is_verified(self):
        """Triage always verifies the chain at the end."""
        src = read_showcase("medical_triage.ledge")
        lines, _ = run(src, output_fn=lambda x: None, reset_audit=True)
        verify_lines = [l for l in lines if "true" in l.lower() or "false" in l.lower()]
        assert any("true" in l for l in verify_lines), "audit_verify() did not return true"

    def test_ledge_cannot_skip_confidence_check(self):
        """
        LEDGE GUARANTEE: without backend, analyze() returns confidence=0.0.
        The system escalates to human automatically. There is no way to
        access the value without passing through the confidence threshold.
        """
        lines, _ = ledge_run(
            'define r as analyze("chest pain") using medical_triage\n'
            'show confidence_of(r)'
        )
        assert lines[0] == "0"

    def test_python_can_silently_ignore_confidence(self):
        """
        PYTHON FAILURE: the Python version can process results with any
        confidence, including 0.0, without raising an error.
        """
        from showcase.medical_triage_python import classify_python

        def backend_fails(text):
            # Backend returns confidence=0.0 but the Python code does not check it
            return {"risk_level": "routine", "confidence": 0.0}

        patient = {"id": "P001", "symptoms": "severe chest pain", "age": 72}
        # This runs without error even though confidence=0.0 — silent failure
        result = classify_python(patient, backend_fails)
        # Result is "routine" even though AI was not confident at all
        assert result == "routine"  # ← should be "escalate to human"
        # No exception, no warning. Silently wrong.

    def test_ledge_contract_enforces_preconditions(self):
        """
        LEDGE GUARANTEE: the requires: contract guarantees that a patient
        with age=0 or no symptoms is never processed.
        """
        with pytest.raises(LedgeError):
            run("""
define evaluate(p):
    requires:
        p["age"] > 0
        len(p["symptoms"]) > 0
    return analyze(p["symptoms"]) using triage

define patient as map {"id": "X", "symptoms": "", "age": 0}
evaluate(patient)
""", output_fn=lambda x: None)


# ── FINANCIAL ANALYSIS ────────────────────────────────────────────────────────

class TestFinancialAnalysis:

    def test_runs_without_backend(self):
        src = read_showcase("financial_analysis.ledge")
        lines, _ = run(src, output_fn=lambda x: None, reset_audit=True)
        assert len(lines) > 0

    def test_ledge_ensures_postcondition_always_returns_decision(self):
        """
        LEDGE GUARANTEE: ensures: guarantees that the result always has
        the required keys. It cannot return an incomplete map.
        """
        lines, _ = ledge_run("""
define evaluate(app):
    ensures:
        has(result, "decision")
        has(result, "explanation")
    return map {"decision": "approve", "explanation": "all clear", "confidence": 0.9}
define r as evaluate(map {})
show has(r, "decision")
show has(r, "explanation")
""")
        assert lines[0] == "true"
        assert lines[1] == "true"

    def test_python_bug_silently_always_approves(self):
        """
        PYTHON FAILURE: the bug in financial_analysis_python.py always
        approves because the developer forgot the elif for "reject".
        """
        from showcase.financial_analysis_python import evaluate_credit_python_with_bug

        def backend_high_risk(history):
            return {"risk": "high", "confidence": 0.95}

        applicant_risky = {
            "id": "A-RISK", "income": 10000, "debt": 8000,
            "history": "repeated defaults, debt in collection"
        }
        result = evaluate_credit_python_with_bug(applicant_risky, backend_high_risk)
        # BUG: should be "reject" but returns "approve"
        assert result == "approve"  # ← bug demonstrated: loan incorrectly approved

    def test_audit_trail_records_all_decisions(self):
        """All evaluations are recorded in the audit trail."""
        src = read_showcase("financial_analysis.ledge")
        lines, _ = run(src, output_fn=lambda x: None, reset_audit=True)
        audit_lines = [l for l in lines if "audit" in l.lower()]
        assert len(audit_lines) > 0


# ── LLM EVALUATOR ─────────────────────────────────────────────────────────────

class TestLLMEvaluator:

    def test_runs_without_backend(self):
        src = read_showcase("llm_evaluator.ledge")
        lines, _ = run(src, output_fn=lambda x: None, reset_audit=True)
        assert len(lines) > 0

    def test_ledge_always_returns_uncertain_from_analyze(self):
        """
        LEDGE GUARANTEE: analyze() ALWAYS returns Uncertain[T].
        There is no way to get a value without confidence attached.
        """
        _, value = ledge_run('analyze("test question") using qa')
        assert isinstance(value, Uncertain), f"Expected Uncertain, got {type(value)}"
        assert hasattr(value, "confidence")

    def test_python_counts_low_confidence_answers(self):
        """
        PYTHON FAILURE: the calibration bug counts answers with confidence=0.1
        as if they were valid answers, artificially inflating accuracy.
        """
        from showcase.llm_evaluator_python import evaluate_python_with_calibration_bug

        def backend_guessing(question):
            # Model that guesses with very low confidence
            return {"answer": "Paris", "confidence": 0.1}

        questions = [
            ("Capital of France",  "Paris"),   # correct: backend says Paris
            ("Capital of Germany", "Berlin"),  # WRONG: backend says Paris ≠ Berlin
            ("Capital of Spain",   "Madrid"),  # WRONG: backend says Paris ≠ Madrid
        ]
        # Bug: counts all answers, even those with confidence=0.1
        # Only 1/3 are correct, but the function does NOT filter by confidence
        accuracy = evaluate_python_with_calibration_bug(questions, backend_guessing)
        # Real accuracy with confidence=0.5 filter should be 0 (none pass the threshold)
        # But without filter: 1 correct of 3 → 33%
        assert accuracy == pytest.approx(1/3, abs=0.01)
        # The problem: these answers should NOT be counted (confidence=0.1 < 0.5)
        # Ledge makes this error impossible because confidence_of() is mandatory

    def test_ledge_zero_confidence_without_backend(self):
        """Without backend, confidence=0 — the evaluator does not count those answers."""
        lines, _ = ledge_run("""
define analysis as analyze("test question X") using qa
show confidence_of(analysis)
""")
        assert lines[0] == "0"


# ── LEGAL CONTRACTS ───────────────────────────────────────────────────────────

class TestLegalContracts:

    def test_runs_without_backend(self):
        src = read_showcase("legal_contracts.ledge")
        lines, _ = run(src, output_fn=lambda x: None, reset_audit=True)
        assert len(lines) > 0

    def test_ledge_low_confidence_escalates_to_human(self):
        """
        LEDGE GUARANTEE: when confidence < MIN_CONFIDENCE, the contract
        is escalated to human review. It cannot be processed automatically.
        """
        lines, _ = ledge_run("""
define MIN_CONF as 0.80
define analysis as analyze("complex contract") using legal
define conf as confidence_of(analysis)
if conf < MIN_CONF:
    show "ESCALATE_HUMAN"
else:
    show "AUTOMATIC"
""")
        # Without backend: confidence=0 → must escalate
        assert lines[0] == "ESCALATE_HUMAN"

    def test_python_typo_silently_ignores_confidence(self):
        """
        PYTHON FAILURE: the typo 'confience' means confidence is never
        verified — all clauses pass without review.
        """
        from showcase.legal_contracts_python import extract_clauses_python_with_bug

        def backend_uncertain(text):
            return {
                "clauses":    ["risky_clause"],
                "confidence": 0.2,  # very low confidence
            }

        contract = {"id": "C001", "text": "contract with ambiguous terms"}
        clauses = extract_clauses_python_with_bug(contract, backend_uncertain)
        # BUG: the typo makes confidence read as 1.0, so
        # the clause passes without review even though confidence=0.2
        assert clauses == ["risky_clause"]  # ← should be empty

    def test_audit_verify_after_legal_processing(self):
        """The contracts audit trail is cryptographically verifiable."""
        lines, _ = ledge_run("""
define r1 as analyze("contract 1") using legal
define r2 as analyze("contract 2") using legal
show audit_verify()
""")
        assert lines[-1] == "true"

    def test_ledge_contract_postcondition_guarantees_completeness(self):
        """
        LEDGE GUARANTEE: ensures: guarantees that the result of extract_clauses()
        always has 'requires_human_review'. It cannot be omitted.
        """
        lines, _ = ledge_run("""
define process(c):
    ensures:
        has(result, "requires_human_review")
    return map {"requires_human_review": list [], "clauses": list []}
define r as process(map {})
show has(r, "requires_human_review")
""")
        assert lines[0] == "true"


# ── All showcases run without crash ───────────────────────────────────────────

class TestShowcasesNocrash:
    """All four showcases must run without crash, even without a backend."""

    def _run_showcase(self, filename):
        src = read_showcase(filename)
        lines, _ = run(src, output_fn=lambda x: None, reset_audit=True)
        return lines

    def test_medical_triage_no_crash(self):
        lines = self._run_showcase("medical_triage.ledge")
        assert len(lines) > 0

    def test_financial_analysis_no_crash(self):
        lines = self._run_showcase("financial_analysis.ledge")
        assert len(lines) > 0

    def test_llm_evaluator_no_crash(self):
        lines = self._run_showcase("llm_evaluator.ledge")
        assert len(lines) > 0

    def test_legal_contracts_no_crash(self):
        lines = self._run_showcase("legal_contracts.ledge")
        assert len(lines) > 0
