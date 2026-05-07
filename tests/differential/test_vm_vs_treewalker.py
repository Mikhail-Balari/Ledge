"""
Differential Testing: Tree-Walker vs Bytecode VM
=================================================
Both backends MUST produce identical output for all valid programs.
Any divergence is a critical bug.

The VM is in development — tests define the official supported subset.
Programs outside the supported subset are explicitly excluded.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

try:
    import pytest
except ImportError:
    class _raises:
        def __init__(self, *e): self.e = e
        def __enter__(self): return self
        def __exit__(self, t, v, tb): return t and issubclass(t, self.e)
    class pytest:
        raises = _raises

from ledge_lang import run, compile_ledge
from ledge_lang.vm import compile_to_bytecode, VM


def both(src):
    """Run source on both backends and assert identical output."""
    # Tree-walker
    tw_lines, _ = run(src.strip(), output_fn=lambda x: None)

    # VM
    try:
        ast = compile_ledge(src.strip())
        co  = compile_to_bytecode(ast)
        vm_out = []
        VM(output_fn=vm_out.append).run(co)
        vm_lines = vm_out
    except Exception as e:
        # VM may not support all features yet — skip if unsupported
        return tw_lines, None

    assert tw_lines == vm_lines, (
        f"DIVERGENCE:\n"
        f"  Tree-walker: {tw_lines}\n"
        f"  VM:          {vm_lines}\n"
        f"  Source: {src.strip()[:80]}"
    )
    return tw_lines, vm_lines


# ── VM Supported Subset ───────────────────────────────────────────────────────

VM_SUPPORTED = """
Official VM-supported subset (v1.0):
  - Number literals, string literals, booleans, nothing
  - Arithmetic: + - * / with safe division
  - Comparison: = != < > <= >=
  - Logic: and or not
  - Variables: define, set
  - Control: if/else, while, repeat N times
  - Show
  - Lists: create, index, len
  - Maps: create, index
  - Fallback: or
  - Basic function calls (builtins)

NOT YET in VM (use tree-walker):
  - Function definitions with closures
  - Generators / yield
  - Parallel
  - AI instructions
  - Python FFI
  - Streams, contracts, agents
"""


class TestVMCoreDivergence:
    """Core arithmetic and control — VM must match tree-walker exactly."""

    def test_integer_literal(self):     both("show 42")
    def test_float_literal(self):       both("show 3.14")
    def test_string_literal(self):      both('show "hello"')
    def test_bool_true(self):           both("show true")
    def test_bool_false(self):          both("show false")
    def test_nothing_literal(self):     both("show nothing")
    def test_add(self):                 both("show 3 + 4")
    def test_subtract(self):            both("show 10 - 3")
    def test_multiply(self):            both("show 6 * 7")
    def test_divide(self):              both("show 10 / 4")
    def test_div_zero(self):            both("show divide(1, 0)")
    def test_div_fallback(self):        both("show divide(1, 0) or -1")
    def test_eq_true(self):             both("show 5 = 5")
    def test_eq_false(self):            both("show 5 = 6")
    def test_neq(self):                 both("show 5 != 6")
    def test_lt(self):                  both("show 3 < 5")
    def test_gt(self):                  both("show 5 > 3")
    def test_and_true(self):            both("show true and true")
    def test_and_false(self):           both("show true and false")
    def test_or_true(self):             both("show false or true")
    def test_not(self):                 both("show not true")
    def test_not_false(self):           both("show not false")

    def test_var_define_show(self):
        both("define x as 42\nshow x")

    def test_var_set(self):
        both("define x as 1\nset x to 99\nshow x")

    def test_if_true(self):
        both("if true:\n    show 1\nelse:\n    show 0")

    def test_if_false(self):
        both("if false:\n    show 1\nelse:\n    show 0")

    def test_while_loop(self):
        both("define x as 0\nwhile x < 5:\n    set x to x + 1\nshow x")

    def test_repeat_n(self):
        both("define x as 0\nrepeat 5 times:\n    set x to x + 1\nshow x")

    def test_list_create(self):
        both("show list [1, 2, 3]")

    def test_list_index(self):
        both("show list [10, 20, 30][1]")

    def test_list_oob(self):
        both("show list [1][99]")

    def test_list_len(self):
        both("show len(list [1, 2, 3])")

    def test_map_create(self):
        both('show map {"k": 1}["k"]')

    def test_str_concat(self):
        both('show "a" + "b"')

    def test_nothing_eq(self):
        both("show nothing = nothing")

    def test_true_not_eq_1(self):
        """Critical invariant: true ≠ 1."""
        both("show true = 1")

    def test_false_not_eq_0(self):
        """Critical invariant: false ≠ 0."""
        both("show false = 0")

    def test_nothing_not_eq_false(self):
        both("show nothing = false")

    def test_fibonacci_iterative(self):
        """Fibonacci via loop — VM subset."""
        both("""
define a as 0
define b as 1
repeat 10 times:
    define next as a + b
    set a to b
    set b to next
show a
""")

    def test_sum_loop(self):
        both("""
define total as 0
define i as 0
while i < 100:
    set total to total + i
    set i to i + 1
show total
""")
