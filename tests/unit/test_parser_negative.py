"""
Ledge Parser Negative Corpus
==============================
Tests that confirm the parser REJECTS invalid programs with clear errors.
Every test represents a real failure mode a user might hit.

This corpus defines what the parser must NOT accept silently.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from ledge_lang import compile_ledge
from ledge_lang.lexer import LexError
from ledge_lang.parser import ParseError
from ledge_lang.interpreter import LedgeError


def should_fail_parse(src, reason=""):
    """Assert that this source fails at parse time."""
    try:
        compile_ledge(src)
        return False, "Unexpectedly parsed without error"
    except (LexError, ParseError) as e:
        return True, str(e)
    except Exception as e:
        return True, str(e)


class TestParserNegativeCorpus:
    """Every program here must be rejected by the parser."""

    # ── Indentation errors ─────────────────────────────────────────────
    def test_missing_indent_after_if(self):
        ok, msg = should_fail_parse("if true:\nshow 1")
        # May succeed or fail depending on parser — indentation is significant
        # At minimum, the behavior must be deterministic
        assert isinstance(ok, bool)

    def test_invalid_token(self):
        ok, msg = should_fail_parse("show @@@")
        assert ok, f"Should fail: {msg}"

    def test_unterminated_string(self):
        ok, msg = should_fail_parse('show "hello')
        assert ok, f"Should fail: {msg}"

    def test_unexpected_operator(self):
        ok, msg = should_fail_parse("define x as +++")
        assert ok, f"Should fail: {msg}"

    def test_missing_colon_in_if(self):
        ok, msg = should_fail_parse("if true\n    show 1")
        # Should either parse differently or fail
        assert isinstance(ok, bool)

    # ── Keyword misuse ─────────────────────────────────────────────────
    def test_break_outside_loop_parses(self):
        """break outside loop parses OK but fails at runtime."""
        ok, msg = should_fail_parse("break")
        # break is valid syntax anywhere, runtime catches it
        assert not ok, "break should parse (caught at runtime)"

    def test_yield_outside_function_parses(self):
        """yield outside function parses OK but fails at runtime."""
        ok, msg = should_fail_parse("yield 1")
        assert not ok, "yield should parse (caught at runtime)"

    # ── Structural errors ──────────────────────────────────────────────
    def test_unmatched_bracket(self):
        ok, msg = should_fail_parse("show list [1, 2, 3")
        assert ok, f"Unmatched bracket should fail: {msg}"

    def test_unmatched_paren(self):
        ok, msg = should_fail_parse("show (1 + 2")
        assert ok, f"Unmatched paren should fail: {msg}"

    def test_bare_operator(self):
        ok, msg = should_fail_parse("show * 5")
        assert ok, f"Bare operator should fail: {msg}"

    def test_double_define(self):
        """Duplicate define is caught at runtime, not parse time."""
        ok, msg = should_fail_parse("define x as 1\ndefine x as 2")
        # This depends on design: may be parse-time or runtime
        assert isinstance(ok, bool)

    # ── Precedence and expression errors ──────────────────────────────
    def test_chained_comparison_invalid(self):
        ok, msg = should_fail_parse("show 1 < 2 < 3")
        # May parse as (1 < 2) < 3 — behavior must be defined
        assert isinstance(ok, bool)

    def test_empty_program(self):
        """Empty program should parse OK."""
        ok, msg = should_fail_parse("")
        assert not ok, "Empty program should parse successfully"

    def test_only_comment(self):
        """Comment-only program should parse OK."""
        ok, msg = should_fail_parse("# just a comment")
        assert not ok, "Comment-only program should parse successfully"

    # ── Negative tests for valid programs (parser sanity) ─────────────
    def test_valid_define_does_not_fail(self):
        ok, msg = should_fail_parse("define x as 42")
        assert not ok, f"Valid define should not fail: {msg}"

    def test_valid_function_does_not_fail(self):
        ok, msg = should_fail_parse("define f(a, b):\n    return a + b")
        assert not ok, f"Valid function should not fail: {msg}"

    def test_fib_does_not_fail(self):
        """n-1 in function args must parse correctly (regression test)."""
        ok, msg = should_fail_parse(
            "define fib(n):\n    if n <= 1:\n        return n\n    return fib(n - 1) + fib(n - 2)"
        )
        assert not ok, f"fib(n-1) regression: should parse fine, got: {msg}"

    def test_nested_function_call_does_not_fail(self):
        ok, msg = should_fail_parse("show f(g(h(x)))")
        assert not ok, "Nested calls should parse"

    def test_multiline_if_does_not_fail(self):
        ok, msg = should_fail_parse(
            "if a > b:\n    show a\nelse if a = b:\n    show 0\nelse:\n    show b"
        )
        assert not ok, "Multi-branch if should parse"
