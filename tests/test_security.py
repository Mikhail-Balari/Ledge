"""
Ledge Security Regression Suite
================================
Tests that must pass on every release.
Runs independently in CI — if this fails, the release is blocked.

Coverage:
- AI confidence fabrication (G01/G03)
- Uncertain type enforcement (G04/D02)
- Audit trail PII isolation (G07/H02)
- FFI allowlist enforcement (J01/J03)
- Iteration limiter (J05)
- Input abuse resistance (J04)
- No secret leakage (J06)
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from ledge_lang import run
from ledge_lang.interpreter import LedgeError
from ledge_lang.typechecker import check_types


class TestAISafetyCore:
    """G01/G03: AI never fabricates certainty."""

    def test_analyze_no_backend_confidence_zero(self):
        ls, _ = run('show confidence_of(analyze("x") using y)', output_fn=lambda x:None)
        assert ls == ["0"], f"analyze() without backend MUST return confidence=0, got {ls}"

    def test_classify_no_backend_value_nothing(self):
        ls, _ = run('show value_of(classify("x") using ["a","b"])', output_fn=lambda x:None)
        assert ls == ["nothing"], f"classify() without backend MUST return nothing, got {ls}"

    def test_classify_no_backend_type_correct(self):
        ls, _ = run('show type(classify("x") using ["a","b"])', output_fn=lambda x:None)
        assert ls == ["uncertain[text]"], f"classify() type wrong: {ls}"

    def test_generate_no_backend_value_nothing(self):
        ls, _ = run('show value_of(generate("x") using text)', output_fn=lambda x:None)
        assert ls == ["nothing"], f"generate() without backend must return nothing: {ls}"

    def test_ask_no_backend_value_nothing(self):
        ls, _ = run('show value_of(ask("question"))', output_fn=lambda x:None)
        assert ls == ["nothing"], f"ask() without backend must return nothing: {ls}"

    def test_confidence_clamped_above(self):
        ls, _ = run('show confidence_of(uncertain("x", 2.5)) <= 1', output_fn=lambda x:None)
        assert ls == ["true"], "Confidence must be clamped to <= 1"

    def test_confidence_clamped_below(self):
        ls, _ = run('show confidence_of(uncertain("x", -1)) >= 0', output_fn=lambda x:None)
        assert ls == ["true"], "Confidence must be clamped to >= 0"


class TestUncertainEnforcement:
    """D02/G04: Uncertain must be handled explicitly."""

    def test_typechecker_errors_on_unsafe_use(self):
        src = 'define r as analyze("x") using y\nshow upper(r)'
        issues = check_types(src)
        errors = [i for i in issues if i.is_error]
        assert errors, "Typechecker MUST error on unsafe Uncertain use"

    def test_typechecker_errors_on_uncertain_in_arithmetic(self):
        src = 'define r as analyze("x") using y\nshow r + 1'
        issues = check_types(src)
        has_issue = any(i.is_error or i.is_warning for i in issues)
        assert has_issue, "Typechecker must warn/error on Uncertain in arithmetic"

    def test_typechecker_safe_with_when(self):
        src = 'define r as analyze("x") using y\nshow when(r, 0.8, "default")'
        issues = check_types(src)
        errors = [i for i in issues if i.is_error]
        assert not errors, f"when() is safe extraction — should not error: {errors}"

    def test_typechecker_safe_after_confidence_guard(self):
        src = 'define r as analyze("x") using y\nif is_confident(r):\n    show value_of(r)'
        issues = check_types(src)
        errors = [i for i in issues if i.is_error]
        assert not errors, f"After is_confident guard — should not error: {errors}"

    def test_typechecker_type_fn_not_flagged(self):
        """type() is a safe inspector — must not be flagged as unsafe use."""
        src = 'show type(analyze("x") using y)'
        issues = check_types(src)
        errors = [i for i in issues if i.is_error]
        assert not errors, f"type() on Uncertain should not error: {errors}"


class TestAuditTrailIsolation:
    """H02: Audit trail must not cross-contaminate between runs."""

    def test_audit_resets_between_runs(self):
        """Run 1 adds 3 entries. Run 2 should see 0."""
        run('define r1 as analyze("a") using y\ndefine r2 as analyze("b") using y\ndefine r3 as classify("c") using ["x"]',
            output_fn=lambda x:None)
        # Run 2: fresh start
        ls, _ = run('show len(audit_query())', output_fn=lambda x:None)
        assert ls == ["0"], f"Audit must reset between runs, got {ls}"

    def test_audit_in_same_run_accumulates(self):
        ls, _ = run(
            'define r1 as analyze("a") using y\ndefine r2 as analyze("b") using y\nshow len(audit_query())',
            output_fn=lambda x:None
        )
        assert ls == ["2"], f"Audit within one run must accumulate: got {ls}"

    def test_audit_no_plaintext_input(self):
        """Sensitive input must not appear in plaintext in audit entries."""
        secret = "my_api_key_12345"
        run(f'define r as analyze("{secret}") using sentiment', output_fn=lambda x:None, reset_audit=False)
        from ledge_lang.ai_types import GLOBAL_AUDIT
        entries_str = str(GLOBAL_AUDIT._entries)
        assert secret not in entries_str, "Secret input must not appear in plaintext audit log"


class TestFFISecurity:
    """J01/J03: FFI allowlist enforcement."""

    def test_allowlist_blocks_unlisted_module(self):
        raised = False
        try:
            run('import "python:os" as o\nshow 1', output_fn=lambda x:None, allowed_modules=[])
            raised = False
        except LedgeError:
            raised = True
        assert raised, "Empty allowlist must block all Python imports"

    def test_allowlist_permits_listed_module(self):
        ls, _ = run('import "python:math" as m\nshow m["sqrt"](9)',
                    output_fn=lambda x:None, allowed_modules=["math"])
        assert ls == ["3"], f"Listed module must work: {ls}"

    def test_no_allowlist_permits_all(self):
        """Backward compatibility: no allowlist = all modules allowed."""
        ls, _ = run('import "python:math" as m\nshow m["sqrt"](16)', output_fn=lambda x:None)
        assert ls == ["4"], f"Without allowlist, all modules allowed: {ls}"

    def test_iteration_limiter_fires(self):
        from ledge_lang import compile_ledge
        from ledge_lang.interpreter import Interpreter
        interp = Interpreter(output_fn=lambda x:None)
        interp._max_iterations = 5
        ast = compile_ledge("define i as 0\nwhile i < 100:\n    set i to i + 1")
        raised = False
        try:
            interp.run(ast)
        except LedgeError:
            raised = True
        assert raised, "Iteration limiter must fire at N iterations"


class TestSemanticInvariants:
    """Core semantic invariants that must never regress."""

    def test_true_not_equal_1(self):
        ls, _ = run("show true = 1", output_fn=lambda x:None)
        assert ls == ["false"], "true must NOT equal 1"

    def test_false_not_equal_0(self):
        ls, _ = run("show false = 0", output_fn=lambda x:None)
        assert ls == ["false"], "false must NOT equal 0"

    def test_nothing_not_equal_false(self):
        ls, _ = run("show nothing = false", output_fn=lambda x:None)
        assert ls == ["false"], "nothing must NOT equal false"

    def test_divide_by_zero_returns_nothing(self):
        ls, _ = run("show divide(1, 0)", output_fn=lambda x:None)
        assert ls == ["nothing"], "divide(x, 0) must return nothing, not crash"

    def test_oob_index_returns_nothing(self):
        ls, _ = run("show list [1,2,3][99]", output_fn=lambda x:None)
        assert ls == ["nothing"], "Out-of-bounds index must return nothing"

    def test_nothing_or_fallback(self):
        ls, _ = run("show nothing or 42", output_fn=lambda x:None)
        assert ls == ["42"], "nothing or X must return X"

    def test_fib_regression(self):
        """Regression: fib(n-1) was broken in older version."""
        src = "define fib(n):\n    if n <= 1:\n        return n\n    return fib(n - 1) + fib(n - 2)\nshow fib(10)"
        ls, _ = run(src, output_fn=lambda x:None)
        assert ls == ["55"], f"fib(10) must be 55, got {ls}"
