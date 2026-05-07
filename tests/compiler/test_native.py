"""
Ledge Native Compiler Tests (GCC backend)
==========================================
Verifies: Ledge → C99 → gcc → binary produces correct output.
These tests PROVE the "faster than Python" claim with reproducible evidence.
"""
import sys, os, subprocess, tempfile, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from ledge_lang.compiler.ccodegen import compile_to_native, compile_to_c
from ledge_lang import run


def run_native(source: str, timeout: int = 5) -> list:
    """Compile and run Ledge source natively, return output lines."""
    with tempfile.NamedTemporaryFile(suffix='', delete=False) as f:
        out_path = f.name
    try:
        compile_to_native(source, out_path)
        r = subprocess.run([out_path], capture_output=True, text=True, timeout=timeout)
        return [l for l in r.stdout.strip().split('\n') if l]
    finally:
        try: os.unlink(out_path)
        except: pass


def tw_out(source: str) -> list:
    """Get tree-walker output for comparison."""
    lines, _ = run(source, output_fn=lambda x: None)
    return lines


class TestNativeCorrectness:
    """Native output must match tree-walker on all programs."""

    def test_show_number(self):
        assert run_native("show 42") == ["42"]

    def test_show_float(self):
        assert run_native("show 3.14") == ["3.14"]

    def test_float_that_is_integer(self):
        assert run_native("show 5.0") == ["5"]  # displays as "5" not "5.0"

    def test_arithmetic(self):
        assert run_native("show 2 + 3 * 4") == ["14"]
        assert run_native("show 10 - 3") == ["7"]
        assert run_native("show 6 * 7") == ["42"]
        assert run_native("show 10 / 4") == ["2.5"]

    def test_safe_division(self):
        assert run_native("show divide(1, 0)") == ["nothing"]

    def test_comparison_true(self):
        assert run_native("show 5 > 3") == ["true"]
        assert run_native("show 3 < 5") == ["true"]
        assert run_native("show 5 = 5") == ["true"]

    def test_comparison_false(self):
        assert run_native("show 3 > 5") == ["false"]

    def test_critical_semantic_invariants(self):
        """These MUST hold in native mode — critical correctness."""
        assert run_native("show true = 1") == ["false"]   # true ≠ 1
        assert run_native("show false = 0") == ["false"]  # false ≠ 0
        assert run_native("show nothing = false") == ["false"]

    def test_variable_define(self):
        assert run_native("define x as 42\nshow x") == ["42"]

    def test_variable_assign(self):
        assert run_native("define x as 1\nset x to 99\nshow x") == ["99"]

    def test_if_true(self):
        assert run_native("if 5 > 3:\n    show 1\nelse:\n    show 0") == ["1"]

    def test_if_false(self):
        assert run_native("if 1 > 5:\n    show 1\nelse:\n    show 0") == ["0"]

    def test_while_loop(self):
        src = "define i as 0\nwhile i < 5:\n    set i to i + 1\nshow i"
        assert run_native(src) == ["5"]

    def test_repeat_loop(self):
        src = "define x as 0\nrepeat 10 times:\n    set x to x + 1\nshow x"
        assert run_native(src) == ["10"]

    def test_function_add(self):
        src = "define add(a, b):\n    return a + b\nshow add(3, 4)"
        assert run_native(src) == ["7"]

    def test_function_no_args(self):
        src = "define answer():\n    return 42\nshow answer()"
        assert run_native(src) == ["42"]

    def test_fibonacci_correctness(self):
        src = "define fib(n):\n    if n <= 1:\n        return n\n    return fib(n - 1) + fib(n - 2)\nshow fib(10)"
        native = run_native(src)
        tw = tw_out(src)
        assert native == ["55"], f"fib(10) must be 55, got {native}"
        assert native == tw, f"Native must match TW: {native} vs {tw}"

    def test_factorial_correctness(self):
        src = "define fact(n):\n    if n <= 1:\n        return 1\n    return n * fact(n - 1)\nshow fact(10)"
        assert run_native(src) == ["3628800"]

    def test_multiple_shows(self):
        src = "show 1\nshow 2\nshow 3"
        assert run_native(src) == ["1", "2", "3"]

    def test_negative_numbers(self):
        src = "define x as -5\nshow x"
        assert run_native(src) == ["-5"]

    def test_sqrt(self):
        assert run_native("show sqrt(25)") == ["5"]

    def test_abs(self):
        assert run_native("show abs(-7)") == ["7"]

    def test_string_output(self):
        assert run_native('show "hello"') == ["hello"]

    def test_string_concat(self):
        assert run_native('show "hello" + " world"') == ["hello world"]

    def test_string_num_concat(self):
        assert run_native('show "n=" + 42') == ["n=42"]

    def test_nothing_or_fallback(self):
        assert run_native("show divide(1, 0) or -1") == ["-1"]


class TestNativeVsTreeWalker:
    """Native output must match TW on the full differential test suite."""

    PROGRAMS = [
        "show 1 + 2 + 3 + 4 + 5",
        "define x as 10\nshow x * x",
        "show 100 / 4",
        "define acc as 0\nrepeat 100 times:\n    set acc to acc + 1\nshow acc",
        "define fib(n):\n    if n <= 1:\n        return n\n    return fib(n-1) + fib(n-2)\nshow fib(12)",
        "if 1 = 1:\n    show true\nelse:\n    show false",
        "show true = 1",   # false
        "show false = 0",  # false
        "show divide(10, 2)",
        "show divide(5, 0)",
    ]

    def test_differential_all(self):
        divergences = []
        for src in self.PROGRAMS:
            try:
                native = run_native(src)
                tw = tw_out(src)
                if native != tw:
                    divergences.append(f"{src[:40]!r}: native={native} TW={tw}")
            except Exception as e:
                divergences.append(f"{src[:40]!r}: {e}")

        assert not divergences, f"Divergences: {divergences}"


class TestNativePerformance:
    """Verify native is faster than CPython — the core performance claim."""

    def test_fib30_faster_than_python(self):
        """Native fib(30) must be faster than CPython."""
        import time

        src = "define fib(n):\n    if n <= 1:\n        return n\n    return fib(n-1) + fib(n-2)\nshow fib(30)"

        # Native
        native_ms = None
        with tempfile.NamedTemporaryFile(suffix='', delete=False) as f:
            out_path = f.name
        try:
            compile_to_native(src, out_path)
            t0 = time.perf_counter()
            subprocess.run([out_path], capture_output=True, timeout=10)
            native_ms = (time.perf_counter() - t0) * 1000
        finally:
            try: os.unlink(out_path)
            except: pass

        # CPython
        def pyfib(n):
            if n <= 1: return n
            return pyfib(n-1) + pyfib(n-2)

        t0 = time.perf_counter()
        pyfib(30)
        py_ms = (time.perf_counter() - t0) * 1000

        speedup = py_ms / native_ms if native_ms and native_ms > 0 else 0
        assert speedup > 5.0, (
            f"Native must be at least 5x faster than CPython for fib(30).\n"
            f"Native: {native_ms:.1f}ms, Python: {py_ms:.1f}ms, speedup: {speedup:.1f}x"
        )
        # Record for benchmark artifact
        print(f"\n  fib(30): native={native_ms:.1f}ms, python={py_ms:.1f}ms, speedup={speedup:.1f}x")
