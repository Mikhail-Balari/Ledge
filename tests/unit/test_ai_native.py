"""
Ledge AI-Native Features — pytest test suite
Critical: These tests validate the primary innovation of Ledge.
Every test here represents a semantic guarantee the language makes.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

try:
    import pytest
    HAS_PYTEST = True
except ImportError:
    HAS_PYTEST = False
    class _raises:
        def __init__(self, *exc): self.exc = exc
        def __enter__(self): return self
        def __exit__(self, t, v, tb):
            if t and issubclass(t, self.exc): return True
            if t is None: raise AssertionError(f"Expected {self.exc}")
            return False
    class pytest:
        raises = _raises

from ledge_lang import run
from ledge_lang.interpreter import LedgeError
from ledge_lang.core_types import LedgeMap, NOTHING
from ledge_lang.ai_types import Uncertain, LedgeStream, GLOBAL_AUDIT, AuditTrail


def ledge(src, expected=None):
    lines, _ = run(src.strip(), output_fn=lambda x: None)
    if expected is not None:
        got = "\n".join(lines).strip()
        assert got == expected.strip(), f"Expected {expected!r}, got {got!r}"
    return lines


class TestUncertainType:
    """Uncertain[T] — the primary AI-native type."""

    def test_creation(self):
        lines = ledge('show type(uncertain("hi", 0.9))')
        assert lines[0].startswith("uncertain")

    def test_confidence_range(self):
        """Confidence must always be clamped to [0.0, 1.0]."""
        lines = ledge('show confidence_of(uncertain("x", 2.5))')
        assert float(lines[0]) <= 1.0

        lines = ledge('show confidence_of(uncertain("x", -0.5))')
        assert float(lines[0]) >= 0.0

    def test_is_confident_high(self):
        ledge('show is_confident(uncertain("x", 0.9))', "true")

    def test_is_confident_low(self):
        ledge('show is_confident(uncertain("x", 0.3))', "false")

    def test_is_uncertain(self):
        ledge('show is_uncertain(uncertain("x", 0.5))', "true")

    def test_value_of(self):
        ledge('show value_of(uncertain("hello", 0.9))', "hello")

    def test_confidence_of(self):
        ledge('show confidence_of(uncertain("x", 0.75))', "0.75")

    def test_when_above_threshold(self):
        ledge('show when(uncertain("yes", 0.95), 0.8, "no")', "yes")

    def test_when_below_threshold(self):
        ledge('show when(uncertain("yes", 0.5), 0.8, "no")', "no")

    def test_uncertain_nothing_value(self):
        """Uncertain can wrap nothing — represents a confident absence."""
        lines = ledge('show confidence_of(uncertain(nothing, 0.99))')
        assert lines[0] == "0.99"


class TestAIWithoutBackend:
    """
    CRITICAL: Without a real AI backend, ALL operations must return
    confidence = 0.0 and value = nothing.
    This is the most important safety invariant in Ledge.
    """

    def test_analyze_zero_confidence(self):
        lines = ledge('show confidence_of(analyze("test") using sentiment)')
        assert lines[0] == "0", f"CRITICAL FAIL: confidence={lines[0]}, expected 0"

    def test_analyze_not_confident(self):
        lines = ledge('show is_confident(analyze("test") using sentiment)')
        assert lines[0] == "false"

    def test_analyze_returns_uncertain_type(self):
        lines = ledge('show type(analyze("test") using sentiment)')
        assert lines[0].startswith("uncertain"), f"Expected uncertain[...], got {lines[0]}"

    def test_classify_zero_confidence(self):
        lines = ledge('show confidence_of(classify("test") using ["a","b"])')
        assert lines[0] == "0"

    def test_classify_not_first_label(self):
        """CRITICAL: must NOT pick first label silently."""
        lines = ledge('show value_of(classify("test") using ["positive","negative"])')
        assert lines[0] == "nothing", f"CRITICAL FAIL: got {lines[0]!r}, expected nothing"

    def test_generate_zero_confidence(self):
        lines = ledge('show confidence_of(generate("hello") using text)')
        assert lines[0] == "0"

    def test_generate_nothing_value(self):
        lines = ledge('show value_of(generate("hello") using text)')
        assert lines[0] == "nothing"

    def test_ask_zero_confidence(self):
        lines = ledge('show confidence_of(ask("what time is it?"))')
        assert lines[0] == "0"

    def test_embed_zero_confidence(self):
        lines = ledge('show confidence_of(embed("hello world"))')
        assert lines[0] == "0"

    def test_when_falls_back_without_backend(self):
        """With no backend, when() should always use fallback."""
        lines = ledge('show when(analyze("x") using y, 0.5, "fallback")')
        assert lines[0] == "fallback"


class TestAIWithBackend:
    """With a real backend, AI operations should work correctly."""

    def _backend(self, confidence=0.92):
        def analyze(text, mode):
            return LedgeMap({"tone": "positive", "score": 0.9, "confidence": confidence})
        def classify(text, labels):
            return labels[0] if labels else NOTHING
        return {"analyze": analyze, "classify": classify}

    def test_analyze_with_backend_high_confidence(self):
        lines, _ = run(
            'show confidence_of(analyze("great") using sentiment)',
            output_fn=lambda x: None,
            ai_backend=self._backend(0.92)
        )
        assert float(lines[0]) == 0.92

    def test_analyze_is_confident_with_backend(self):
        lines, _ = run(
            'show is_confident(analyze("great") using sentiment)',
            output_fn=lambda x: None,
            ai_backend=self._backend(0.92)
        )
        assert lines[0] == "true"

    def test_when_succeeds_with_backend(self):
        lines, _ = run(
            'show when(analyze("great") using sentiment, 0.8, "uncertain")',
            output_fn=lambda x: None,
            ai_backend=self._backend(0.92)
        )
        assert lines[0] != "uncertain"

    def test_classify_with_backend(self):
        lines, _ = run(
            'show value_of(classify("urgent email") using ["urgent","normal"])',
            output_fn=lambda x: None,
            ai_backend=self._backend()
        )
        assert lines[0] == "urgent"


class TestAuditTrail:
    """AuditTrail — every AI call must be logged."""

    def test_analyze_logged(self):
        lines = ledge("""
define r as analyze("test") using sentiment
define log as audit_query()
show len(log)
""")
        assert int(lines[0]) >= 1

    def test_classify_logged(self):
        lines = ledge("""
define r as classify("test") using ["a","b"]
define log as audit_query()
show len(log)
""")
        assert int(lines[0]) >= 1

    def test_multiple_calls_logged(self):
        lines = ledge("""
define r1 as analyze("a") using sentiment
define r2 as analyze("b") using sentiment
define r3 as classify("c") using ["x","y"]
define log as audit_query()
show len(log)
""")
        assert int(lines[0]) >= 3

    def test_audit_is_always_truthy(self):
        """AuditTrail must never be falsy even when empty."""
        trail = AuditTrail()
        assert bool(trail) is True, "Empty AuditTrail must be truthy"

    def test_audit_query_returns_list(self):
        lines = ledge("define log as audit_query()\nshow type(log)")
        assert lines[0] == "list"


class TestStreams:
    """Stream[T] — lazy reactive sequences."""

    def test_stream_of_list(self):
        ledge("""
define s as stream_of(list [1,2,3])
show stream_collect(s)
""", "[1, 2, 3]")

    def test_stream_where(self):
        ledge("""
define s as stream_of(list [1,2,3,4,5,6])
define evens as stream_where(s, given x: modulo(x,2)=0)
show stream_collect(evens)
""", "[2, 4, 6]")

    def test_stream_map(self):
        ledge("""
define s as stream_of(list [1,2,3])
define doubled as stream_map(s, given x: x*2)
show stream_collect(doubled)
""", "[2, 4, 6]")

    def test_stream_take(self):
        ledge("""
define s as stream_of(list [10,20,30,40,50])
show stream_collect(stream_take(s, 3))
""", "[10, 20, 30]")

    def test_stream_first(self):
        ledge("show stream_first(stream_of(list [99,88,77]))", "99")

    def test_stream_re_iterable(self):
        """Streams from lists must be re-iterable."""
        ledge("""
define s as stream_of(list [1,2,3])
define evens as stream_where(s, given x: modulo(x,2)=0)
show stream_collect(evens)
show stream_collect(evens)
""", "[2]\n[2]")

    def test_infinite_generator(self):
        """Infinite generators must work without hanging."""
        ledge("""
define naturals(n):
    while true:
        yield n
        set n to n + 1
define g as naturals(1)
show g[0]
show g[99]
""", "1\n100")

    def test_when_reactive(self):
        ledge("""
define nums as stream_of(list [10,25,5,90,15])
define results as list []
when nums has new item as n:
    if n > 20:
        set results to append(results, n)
show results
""", "[25, 90]")


class TestContracts:
    """requires:/ensures: — verifiable function contracts."""

    def test_valid_call(self):
        ledge("""
define safe_div(a: number, b: number):
    requires:
        b != 0
    return divide(a, b) or 0
show safe_div(10, 2)
""", "5")

    def test_precondition_violation(self):
        with pytest.raises(LedgeError):
            run("""
define safe_div(a: number, b: number):
    requires:
        b != 0
    return divide(a, b) or 0
safe_div(10, 0)
""", output_fn=lambda x: None)

    def test_postcondition(self):
        ledge("""
define pos_sqrt(x: number):
    requires:
        x >= 0
    ensures:
        result >= 0
    return sqrt(x) or 0
show pos_sqrt(25)
show pos_sqrt(0)
""", "5\n0")

    def test_precondition_fires_before_body(self):
        """Body must NOT execute if precondition fails."""
        lines = []
        try:
            run("""
define f(x: number):
    requires:
        x > 0
    show "body executed"
    return x
f(-1)
""", output_fn=lines.append)
        except LedgeError:
            pass
        assert "body executed" not in lines, "Body executed despite failed precondition"


class TestParallel:
    """parallel [] — concurrent execution."""

    def test_basic(self):
        ledge("define r as parallel [1+1, 2+2, 3+3]\nshow sum(r)", "12")

    def test_order_preserved(self):
        ledge("define r as parallel [10, 20, 30]\nshow r[0]\nshow r[2]", "10\n30")

    def test_empty(self):
        ledge("define r as parallel []\nshow len(r)", "0")


class TestPythonFFI:
    """Python FFI — import python: packages."""

    def test_math_module(self):
        ledge("""
import "python:math" as m
show m["sqrt"](144)
show m["pi"] > 3
""", "12\ntrue")

    def test_json_module(self):
        ledge("""
import "python:json" as j
define data as j["loads"]("{}")
show type(data)
""", "map")

    def test_import_failure_clear_error(self):
        with pytest.raises(LedgeError):
            run('import "python:nonexistent_xyz_12345" as m', output_fn=lambda x: None)
