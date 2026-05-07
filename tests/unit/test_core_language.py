"""
Ledge Core Language — pytest test suite
Tests: literals, arithmetic, variables, control flow, functions, collections
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

try:
    import pytest
    HAS_PYTEST = True
except ImportError:
    HAS_PYTEST = False
    # Minimal pytest compatibility shim
    class _raises:
        def __init__(self, *exc_types): self.exc_types = exc_types
        def __enter__(self): return self
        def __exit__(self, exc_type, exc_val, tb):
            if exc_type and issubclass(exc_type, self.exc_types):
                return True
            if exc_type is None:
                raise AssertionError(f"Expected one of {self.exc_types}, nothing raised")
            return False
    class pytest:
        raises = _raises
        @staticmethod
        def mark(*a, **kw):
            def decorator(fn): return fn
            return decorator
from ledge_lang import run
from ledge_lang.interpreter import LedgeError
from ledge_lang.lexer import LexError
from ledge_lang.parser import ParseError


def ledge(src, expected=None):
    """Run Ledge source and return output lines."""
    lines, _ = run(src.strip(), output_fn=lambda x: None)
    if expected is not None:
        assert "\n".join(lines).strip() == expected.strip(), \
            f"Expected {expected!r}, got {lines!r}"
    return lines


def ledge_error(src):
    """Assert that source raises a LedgeError."""
    with pytest.raises((LedgeError, LexError, ParseError)):
        run(src.strip(), output_fn=lambda x: None)


# ── Literals ──────────────────────────────────────────────────────────────────

class TestLiterals:
    def test_integer(self):          ledge("show 42", "42")
    def test_negative(self):         ledge("show -5", "-5")
    def test_float(self):            ledge("show 3.14", "3.14")
    def test_float_whole(self):      ledge("show 1.0", "1")
    def test_string(self):           ledge('show "hello"', "hello")
    def test_string_empty(self):     ledge('show ""', "")
    def test_bool_true(self):        ledge("show true", "true")
    def test_bool_false(self):       ledge("show false", "false")
    def test_nothing(self):          ledge("show nothing", "nothing")
    def test_list_empty(self):       ledge("show list []", "[]")
    def test_list_basic(self):       ledge("show list [1,2,3]", "[1, 2, 3]")
    def test_map_empty(self):        ledge("show map {}", "{}")
    def test_map_basic(self):        ledge('show map {"k":1}["k"]', "1")
    def test_interpolation(self):    ledge('define x as 42\nshow "x={x}"', "x=42")
    def test_interp_expr(self):      ledge('show "2+2={2+2}"', "2+2=4")


# ── Arithmetic ────────────────────────────────────────────────────────────────

class TestArithmetic:
    def test_add_int(self):       ledge("show 3 + 4", "7")
    def test_sub(self):           ledge("show 10 - 3", "7")
    def test_mul(self):           ledge("show 6 * 7", "42")
    def test_div(self):           ledge("show 10 / 4", "2.5")
    def test_div_zero_nothing(self): ledge("show divide(1, 0)", "nothing")
    def test_div_zero_fallback(self): ledge("show divide(1, 0) or -1", "-1")
    def test_mod(self):           ledge("show modulo(17, 5)", "2")
    def test_power(self):         ledge("show power(2, 10)", "1024")
    def test_sqrt(self):          ledge("show sqrt(25)", "5")
    def test_sqrt_neg_nothing(self): ledge("show sqrt(-1) or 0", "0")
    def test_precedence(self):    ledge("show 2 + 3 * 4", "14")
    def test_parens(self):        ledge("show (2 + 3) * 4", "20")
    def test_str_concat(self):    ledge('show "a" + "b"', "ab")
    def test_str_num_concat(self): ledge('show "n=" + 42', "n=42")
    def test_abs(self):           ledge("show abs(-42)", "42")
    def test_floor(self):         ledge("show floor(3.9)", "3")
    def test_ceil(self):          ledge("show ceil(3.1)", "4")
    def test_round(self):         ledge("show round(3.14159, 2)", "3.14")


# ── Type safety — critical invariants ────────────────────────────────────────

class TestTypeSafety:
    """These invariants are core to Ledge's identity."""

    def test_true_not_equal_1(self):
        ledge("show true = 1", "false")

    def test_false_not_equal_0(self):
        ledge("show false = 0", "false")

    def test_nothing_not_equal_false(self):
        ledge("show nothing = false", "false")

    def test_nothing_not_equal_0(self):
        ledge("show nothing = 0", "false")

    def test_nothing_equals_nothing(self):
        ledge("show nothing = nothing", "true")

    def test_type_annotation_enforced(self):
        ledge_error('define x: number as "hello"')

    def test_set_type_enforced(self):
        ledge_error('define x: number as 1\nset x to "string"')

    def test_set_undefined_error(self):
        ledge_error('set x to 10')

    def test_undefined_var_error(self):
        ledge_error('show undefined_xyz_var')

    def test_call_non_function_error(self):
        ledge_error('define x as 5\nx()')


# ── Variables and scoping ─────────────────────────────────────────────────────

class TestVariables:
    def test_define_use(self):
        ledge("define x as 10\nshow x", "10")

    def test_set_mutates(self):
        ledge("define x as 1\nset x to 99\nshow x", "99")

    def test_closure_captures(self):
        ledge("define x as 10\ndefine f():\n    return x\nshow f()", "10")

    def test_closure_mutation(self):
        ledge("""
define counter():
    define n as 0
    define inc():
        set n to n + 1
        return n
    return inc
define c as counter()
show c()
show c()
show c()
""", "1\n2\n3")

    def test_shadow_inner(self):
        ledge("""
define x as 1
define f():
    define x as 2
    return x
show f()
show x
""", "2\n1")


# ── Control flow ──────────────────────────────────────────────────────────────

class TestControlFlow:
    def test_if_true(self):      ledge("if true:\n    show 1", "1")
    def test_if_false(self):     ledge("if false:\n    show 1", "")
    def test_else(self):         ledge("if false:\n    show 1\nelse:\n    show 2", "2")
    def test_elif(self):
        ledge("define x as 2\nif x=1:\n    show \"one\"\nelse if x=2:\n    show \"two\"\nelse:\n    show \"other\"", "two")
    def test_for_list(self):     ledge("for each x in list [1,2,3]:\n    show x", "1\n2\n3")
    def test_while(self):        ledge("define x as 0\nwhile x < 5:\n    set x to x + 1\nshow x", "5")
    def test_repeat_n(self):     ledge("define x as 0\nrepeat 5 times:\n    set x to x + 1\nshow x", "5")
    def test_break(self):
        ledge("define x as 0\nwhile true:\n    set x to x + 1\n    if x = 3:\n        break\nshow x", "3")
    def test_continue(self):
        ledge("""
define r as list []
for each n in list [1,2,3,4,5]:
    if modulo(n, 2) = 0:
        continue
    set r to append(r, n)
show r
""", "[1, 3, 5]")
    def test_match_hit(self):
        ledge("match 2:\n    case 1:\n        show \"one\"\n    case 2:\n        show \"two\"", "two")
    def test_match_otherwise(self):
        ledge("match 99:\n    case 1:\n        show \"one\"\n    otherwise:\n        show \"other\"", "other")


# ── Functions ─────────────────────────────────────────────────────────────────

class TestFunctions:
    def test_basic(self):
        ledge("define f():\n    return 42\nshow f()", "42")

    def test_args(self):
        ledge("define add(a, b):\n    return a + b\nshow add(3, 4)", "7")

    def test_recursion(self):
        ledge("""
define fact(n):
    if n <= 1:
        return 1
    return n * fact(n - 1)
show fact(10)
""", "3628800")

    def test_mutual_recursion(self):
        ledge("""
define is_even(n):
    if n = 0:
        return true
    return is_odd(n - 1)
define is_odd(n):
    if n = 0:
        return false
    return is_even(n - 1)
show is_even(10)
show is_odd(7)
""", "true\ntrue")

    def test_lambda(self):
        ledge("define f as given x: x * 2\nshow f(21)", "42")

    def test_higher_order(self):
        ledge("""
define apply(f, x):
    return f(x)
define double(x):
    return x * 2
show apply(double, 21)
""", "42")


# ── Error handling ────────────────────────────────────────────────────────────

class TestErrorHandling:
    def test_check_ok(self):
        ledge("check:\n    show 1", "1")

    def test_check_recover(self):
        ledge("check:\n    error(\"boom\")\nrecover e:\n    show e", "boom")

    def test_check_always(self):
        ledge("check:\n    show 1\nalways:\n    show 2", "1\n2")

    def test_or_fallback_nothing(self):
        ledge("show nothing or \"default\"", "default")

    def test_or_fallback_div(self):
        ledge("show divide(1, 0) or 0", "0")

    def test_or_fallback_index(self):
        ledge("show list [1][99] or \"miss\"", "miss")

    def test_or_present_skips(self):
        ledge("show 42 or 0", "42")

    def test_yield_outside_fn_error(self):
        ledge_error("yield 1")

    def test_break_outside_loop_error(self):
        ledge_error("break")

    def test_continue_outside_loop_error(self):
        ledge_error("continue")


# ── Collections ───────────────────────────────────────────────────────────────

class TestCollections:
    def test_list_index(self):       ledge("show list [10,20,30][1]", "20")
    def test_list_oob_nothing(self): ledge("show list [1][99]", "nothing")
    def test_list_append(self):      ledge("show len(append(list [1,2], 3))", "3")
    def test_list_sum(self):         ledge("show sum(list [1,2,3,4,5])", "15")
    def test_list_max(self):         ledge("show max(list [3,1,4,1,5,9])", "9")
    def test_list_map(self):         ledge("show map(list [1,2,3], given x: x*2)", "[2, 4, 6]")
    def test_list_filter(self):      ledge("show filter(list [1,2,3,4,5], given x: x>3)", "[4, 5]")
    def test_list_sort(self):        ledge("show sort(list [3,1,4,1,5])", "[1, 1, 3, 4, 5]")
    def test_map_access(self):       ledge('show map {"x":42}["x"]', "42")
    def test_map_missing(self):      ledge('show map {}["k"]', "nothing")
    def test_map_merge(self):        ledge('show merge(map {"a":1}, map {"b":2})["b"]', "2")
    def test_json_roundtrip(self):
        ledge("""
define d as map {"n": 42}
define s as json_stringify(d)
define d2 as json_parse(s)
show d2["n"]
""", "42")


# ── AI-native safety — CRITICAL tests ────────────────────────────────────────

class TestAINativeSafety:
    """
    These tests verify the primary innovation of Ledge:
    AI operations never return high confidence without a real backend.
    """

    def test_analyze_no_backend_zero_confidence(self):
        """CRITICAL: analyze without backend MUST return 0.0 confidence."""
        lines, _ = run('show confidence_of(analyze("x") using y)', output_fn=lambda x: None)
        assert lines[0] == "0", f"Expected 0, got {lines[0]}"

    def test_classify_no_backend_zero_confidence(self):
        """CRITICAL: classify without backend MUST return 0.0 confidence."""
        lines, _ = run('show confidence_of(classify("x") using ["a","b"])', output_fn=lambda x: None)
        assert lines[0] == "0", f"Expected 0, got {lines[0]}"

    def test_classify_no_backend_not_first_label(self):
        """CRITICAL: classify without backend MUST NOT pick first label."""
        lines, _ = run('show value_of(classify("x") using ["positive","negative"])', output_fn=lambda x: None)
        assert lines[0] == "nothing", f"Expected nothing, got {lines[0]}"

    def test_analyze_not_confident_without_backend(self):
        lines, _ = run('show is_confident(analyze("x") using y)', output_fn=lambda x: None)
        assert lines[0] == "false", f"Expected false, got {lines[0]}"

    def test_uncertain_type_from_analyze(self):
        lines, _ = run('show type(analyze("x") using y)', output_fn=lambda x: None)
        assert lines[0].startswith("uncertain"), f"Expected uncertain[...], got {lines[0]}"

    def test_uncertain_when_low_confidence(self):
        ledge("""
define r as analyze("test") using sentiment
show when(r, 0.8, "not confident")
""", "not confident")

    def test_audit_logs_ai_calls(self):
        lines, _ = run("""
define r1 as analyze("a") using sentiment
define r2 as classify("b") using ["x","y"]
define log as audit_query()
show len(log)
""", output_fn=lambda x: None)
        assert int(lines[0]) >= 2, f"Expected >= 2 audit entries, got {lines[0]}"

    def test_uncertain_confidence_clamped(self):
        """Confidence must always be in [0.0, 1.0]."""
        lines, _ = run('show confidence_of(uncertain("x", 2.5))', output_fn=lambda x: None)
        assert float(lines[0]) <= 1.0, f"Confidence exceeds 1.0: {lines[0]}"

    def test_uncertain_from_backend(self):
        """With real backend, confidence can be high."""
        def fake_analyze(text, mode):
            from ledge_lang.core_types import LedgeMap
            return LedgeMap({"tone": "positive", "confidence": 0.95})

        lines, _ = run('define r as analyze("great") using sentiment\nshow confidence_of(r)',
                      output_fn=lambda x: None,
                      ai_backend={"analyze": fake_analyze})
        assert float(lines[0]) == 0.95, f"Expected 0.95, got {lines[0]}"
