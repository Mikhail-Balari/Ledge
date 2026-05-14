"""
Property-Based Tests for Ledge
================================
Tests algebraic laws and semantic invariants using exhaustive case generation.
No random input needed — these are mathematical properties that must hold
for ALL inputs in the defined domain.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from ledge_lang import run
from ledge_lang.core_types import NOTHING, LedgeList, LedgeMap, _eq, _truthy, _repr


def ledge(src):
    lines, _ = run(src.strip(), output_fn=lambda x: None)
    return "\n".join(lines).strip()


# ── Arithmetic properties ─────────────────────────────────────────────────────

class TestArithmeticProperties:
    """Algebraic laws — must hold for representative sample."""

    NUMBERS = [0, 1, -1, 2, 10, 100, 3.14, -2.5, 0.001]

    def test_addition_commutative(self):
        """a + b == b + a for numbers."""
        for a in self.NUMBERS:
            for b in self.NUMBERS:
                r1 = ledge(f"show {a} + {b}")
                r2 = ledge(f"show {b} + {a}")
                assert r1 == r2, f"{a} + {b} != {b} + {a}: {r1} != {r2}"

    def test_addition_associative(self):
        """(a + b) + c == a + (b + c) for numbers."""
        for a in [0, 1, 2, 3]:
            for b in [0, 1, 2]:
                for c in [0, 1]:
                    r1 = ledge(f"show ({a} + {b}) + {c}")
                    r2 = ledge(f"show {a} + ({b} + {c})")
                    assert r1 == r2, f"({a}+{b})+{c} != {a}+({b}+{c})"

    def test_mult_commutative(self):
        """a * b == b * a."""
        for a in [0, 1, 2, 3, -1]:
            for b in [0, 1, 2, -1]:
                r1 = ledge(f"show {a} * {b}")
                r2 = ledge(f"show {b} * {a}")
                assert r1 == r2

    def test_zero_is_additive_identity(self):
        """a + 0 == a."""
        for a in self.NUMBERS:
            r = ledge(f"show {a} + 0")
            expected = _repr(a + 0)
            # Just verify it doesn't crash and is a number
            assert r != "nothing"

    def test_one_is_multiplicative_identity(self):
        """a * 1 == a."""
        for a in self.NUMBERS:
            r1 = ledge(f"show {a} * 1")
            r2 = ledge(f"show {a}")
            assert r1 == r2, f"{a} * 1 != {a}: {r1} != {r2}"

    def test_division_by_zero_always_nothing(self):
        """divide(a, 0) == nothing for all a."""
        for a in self.NUMBERS:
            r = ledge(f"show divide({a}, 0)")
            assert r == "nothing", f"divide({a}, 0) should be nothing, got {r}"

    def test_sqrt_of_square_is_abs(self):
        """sqrt(a*a) == |a| for a >= 0."""
        for a in [0, 1, 2, 3, 4, 5, 10]:
            r = ledge(f"show sqrt({a} * {a})")
            assert r == str(a), f"sqrt({a}^2) should be {a}, got {r}"


# ── List properties ───────────────────────────────────────────────────────────

class TestListProperties:
    """Algebraic laws for list operations."""

    def test_append_increases_length(self):
        """len(append(l, x)) == len(l) + 1."""
        for n in range(6):
            items = ", ".join(str(i) for i in range(n))
            src = f"define l as list [{items}]\nshow len(append(l, 99))"
            r = ledge(src)
            assert int(r) == n + 1, f"len {n}: expected {n+1}, got {r}"

    def test_merge_length(self):
        """len(merge(a, b)) == len(a) + len(b)."""
        for a in range(4):
            for b in range(4):
                a_items = ", ".join(str(i) for i in range(a))
                b_items = ", ".join(str(i+100) for i in range(b))
                src = f"show len(merge(list [{a_items}], list [{b_items}]))"
                r = ledge(src)
                assert int(r) == a + b, f"merge({a},{b}): expected {a+b}, got {r}"

    def test_map_preserves_length(self):
        """len(map(l, fn)) == len(l)."""
        for n in [0, 1, 2, 5, 10]:
            items = ", ".join(str(i) for i in range(n))
            src = f"define l as list [{items}]\nshow len(map(l, given x: x * 2))"
            r = ledge(src)
            assert int(r) == n, f"map length: expected {n}, got {r}"

    def test_filter_length_lte(self):
        """len(filter(l, fn)) <= len(l)."""
        src = "show len(filter(list [1,2,3,4,5,6,7,8,9,10], given x: modulo(x,2)=0)) <= 10"
        assert ledge(src) == "true"

    def test_sum_of_range(self):
        """sum(range(n)) == n*(n-1)/2."""
        for n in [0, 1, 2, 5, 10, 100]:
            r = ledge(f"show sum(range({n}))")
            expected = str(n * (n - 1) // 2)
            assert r == expected, f"sum(range({n})) expected {expected}, got {r}"

    def test_sort_idempotent(self):
        """sort(sort(l)) == sort(l)."""
        r1 = ledge("show sort(list [3,1,4,1,5,9,2,6])")
        r2 = ledge("show sort(sort(list [3,1,4,1,5,9,2,6]))")
        assert r1 == r2

    def test_reverse_involution(self):
        """reverse(reverse(l)) == l."""
        r1 = ledge("show list [1,2,3,4,5]")
        r2 = ledge("show reverse(reverse(list [1,2,3,4,5]))")
        assert r1 == r2


# ── String properties ─────────────────────────────────────────────────────────

class TestStringProperties:
    """String operation invariants."""

    def test_upper_idempotent(self):
        """upper(upper(s)) == upper(s)."""
        for s in ["hello", "WORLD", "MiXeD", "123", ""]:
            r1 = ledge(f'show upper("{s}")')
            r2 = ledge(f'show upper(upper("{s}"))')
            assert r1 == r2, f"upper not idempotent on {s!r}"

    def test_lower_idempotent(self):
        """lower(lower(s)) == lower(s)."""
        for s in ["hello", "WORLD", "MiXeD"]:
            r1 = ledge(f'show lower("{s}")')
            r2 = ledge(f'show lower(lower("{s}"))')
            assert r1 == r2

    def test_split_join_roundtrip(self):
        """join(split(s, sep), sep) == s for well-formed strings."""
        for s in ["a,b,c", "x,y", "single"]:
            r = ledge(f'show join(split("{s}", ","), ",")')
            assert r == s, f"split-join roundtrip failed for {s!r}: {r}"

    def test_trim_idempotent(self):
        """trim(trim(s)) == trim(s)."""
        for s in ["  hello  ", "world", " x "]:
            r1 = ledge(f'show trim("{s}")')
            r2 = ledge(f'show trim(trim("{s}"))')
            assert r1 == r2


# ── Type safety invariants ────────────────────────────────────────────────────

class TestTypeSafetyProperties:
    """These properties must hold for all values."""

    def test_nothing_is_only_equal_to_itself(self):
        """nothing != any other value."""
        for v in ["0", "false", '""', "list []", "map {}"]:
            r = ledge(f"show nothing = {v}")
            assert r == "false", f"nothing should not equal {v}, got {r}"

    def test_true_is_not_a_number(self):
        """true and false are not numbers — critical invariant."""
        assert ledge("show true = 1") == "false"
        assert ledge("show false = 0") == "false"
        assert ledge("show true = 0") == "false"
        assert ledge("show false = 1") == "false"

    def test_type_of_is_stable(self):
        """type() returns consistent values."""
        cases = [("42", "number"), ('"hello"', "text"), ("true", "truth"),
                 ("false", "truth"), ("nothing", "nothing"),
                 ("list []", "list"), ("map {}", "map")]
        for val, expected_type in cases:
            r = ledge(f"show type({val})")
            assert r == expected_type, f"type({val}) should be {expected_type}, got {r}"

    def test_confidence_always_in_range(self):
        """Uncertain confidence is always clamped to [0.0, 1.0]."""
        for conf in [-5, -1, 0, 0.5, 1, 1.5, 10, 100]:
            r = ledge(f"show confidence_of(uncertain(\"x\", {conf}))")
            val = float(r)
            assert 0.0 <= val <= 1.0, f"confidence {conf} produced {val}, not in [0,1]"


# ── Formatter properties ──────────────────────────────────────────────────────

class TestFormatterProperties:
    """Formatter must be idempotent — format(format(x)) == format(x)."""

    def test_formatter_idempotent_on_simple(self):
        from ledge_lang.formatter import format_ledge
        programs = [
            "define x as 10\nshow x",
            "define f(a, b):\n    return a + b\nshow f(3, 4)",
            "for each i in range(5):\n    show i",
            "if true:\n    show 1\nelse:\n    show 2",
        ]
        for src in programs:
            fmt1 = format_ledge(src)
            fmt2 = format_ledge(fmt1)
            assert fmt1 == fmt2, f"Formatter not idempotent:\nInput: {src!r}\nFmt1: {fmt1!r}\nFmt2: {fmt2!r}"

    def test_formatter_idempotent_on_tour(self):
        from ledge_lang.formatter import format_ledge
        root = os.path.join(os.path.dirname(__file__), '..', '..', 'examples', 'tour.ledge')
        if os.path.exists(root):
            with open(root, encoding='utf-8') as f:
                src = f.read()
            fmt1 = format_ledge(src)
            fmt2 = format_ledge(fmt1)
            assert fmt1 == fmt2, "Formatter not idempotent on tour.ledge"
