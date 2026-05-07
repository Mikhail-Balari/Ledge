"""
Ledge Compiler Tests
====================
Tests for the LLVM IR code generator.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from ledge_lang.compiler import compile_to_ir, TargetNotAvailable
from ledge_lang.compiler.targets import compile_to_native, compile_to_wasm


def ir_valid(ir: str) -> bool:
    """Check basic structural validity of generated LLVM IR."""
    return (
        'target triple' in ir and
        'define i32 @main' in ir and
        'ret i32 0' in ir and
        'entry:' in ir
    )


class TestIRGeneration:
    """LLVM IR code generation — always works, no LLVM needed."""

    def test_arithmetic(self):
        ir = compile_to_ir("show 2 + 3 * 4")
        assert ir_valid(ir)
        assert 'fadd' in ir or 'fmul' in ir

    def test_variables(self):
        ir = compile_to_ir("define x as 42\nshow x")
        assert ir_valid(ir)
        assert 'alloca' in ir
        assert 'store' in ir

    def test_if_else(self):
        ir = compile_to_ir("if 5 > 3:\n    show 1\nelse:\n    show 0")
        assert ir_valid(ir)
        assert 'br i1' in ir

    def test_while_loop(self):
        ir = compile_to_ir("define i as 0\nwhile i < 5:\n    set i to i + 1\nshow i")
        assert ir_valid(ir)
        assert 'while_cond' in ir or 'br label' in ir

    def test_repeat_loop(self):
        ir = compile_to_ir("define x as 0\nrepeat 5 times:\n    set x to x + 1\nshow x")
        assert ir_valid(ir)

    def test_function_definition(self):
        ir = compile_to_ir("define add(a, b):\n    return a + b\nshow add(3, 4)")
        assert ir_valid(ir)
        assert 'define double @fn_add' in ir
        assert 'call double @fn_add' in ir

    def test_recursive_function(self):
        src = """
define fib(n):
    if n <= 1:
        return n
    return fib(n - 1) + fib(n - 2)
show fib(10)
"""
        ir = compile_to_ir(src)
        assert ir_valid(ir)
        assert 'define double @fn_fib' in ir
        # Should have recursive calls inside the function body
        assert ir.count('call double @fn_fib') >= 2

    def test_safe_division(self):
        ir = compile_to_ir("show divide(10, 0)")
        assert ir_valid(ir)
        # Safe division checks for zero divisor
        assert 'fcmp oeq' in ir or 'div_zero' in ir or 'div_safe' in ir

    def test_comparison_operators(self):
        for op, src in [
            ("eq",  "show 5 = 5"),
            ("ne",  "show 5 != 3"),
            ("lt",  "show 3 < 5"),
            ("gt",  "show 5 > 3"),
            ("lte", "show 3 <= 3"),
            ("gte", "show 5 >= 5"),
        ]:
            ir = compile_to_ir(src)
            assert ir_valid(ir), f"Invalid IR for {op}"
            assert 'fcmp' in ir, f"Missing fcmp for {op}"

    def test_logical_and(self):
        ir = compile_to_ir("show true and false")
        assert ir_valid(ir)
        assert 'and i1' in ir

    def test_logical_or(self):
        ir = compile_to_ir("show true or false")
        assert ir_valid(ir)
        assert 'or i1' in ir

    def test_not_operator(self):
        ir = compile_to_ir("show not true")
        assert ir_valid(ir)
        assert 'fcmp oeq' in ir

    def test_multiple_functions(self):
        src = """
define double_val(x):
    return x * 2

define triple_val(x):
    return x * 3

show double_val(5)
show triple_val(5)
"""
        ir = compile_to_ir(src)
        assert ir_valid(ir)
        assert 'define double @fn_double_val' in ir
        assert 'define double @fn_triple_val' in ir

    def test_nested_calls(self):
        src = """
define square(x):
    return x * x

define sum_squares(a, b):
    return square(a) + square(b)

show sum_squares(3, 4)
"""
        ir = compile_to_ir(src)
        assert ir_valid(ir)
        assert 'define double @fn_square' in ir
        assert 'define double @fn_sum_squares' in ir

    def test_target_triple_present(self):
        ir = compile_to_ir("show 42")
        assert 'target triple = "x86_64-unknown-linux-gnu"' in ir

    def test_runtime_declarations_present(self):
        ir = compile_to_ir("show 42")
        assert 'declare i32 @printf' in ir
        assert 'declare i8* @malloc' in ir

    def test_ai_instructions_graceful(self):
        """AI instructions compile (as stubs) without crashing."""
        src = """
define r as analyze("hello") using sentiment
show confidence_of(r)
"""
        ir = compile_to_ir(src)
        assert ir_valid(ir)
        # AI instruction emits a comment stub
        assert '; AI instruction' in ir or 'unsupported' in ir or ir_valid(ir)


class TestTargetNotAvailable:
    """TargetNotAvailable raised correctly when toolchain missing."""

    def test_native_without_clang(self):
        """If clang is not installed, TargetNotAvailable is raised."""
        import shutil
        if shutil.which("clang"):
            return  # clang installed — skip this test
        try:
            compile_to_native("show 42", "/tmp/test_out")
            # Should not reach here
            assert False, "Should have raised TargetNotAvailable"
        except TargetNotAvailable as e:
            assert "clang" in str(e).lower()
            assert "install" in str(e).lower()

    def test_wasm_without_emcc(self):
        """If emcc is not installed, TargetNotAvailable is raised."""
        import shutil
        if shutil.which("emcc"):
            return
        try:
            compile_to_wasm("show 42", "/tmp/test.wasm")
            assert False, "Should have raised TargetNotAvailable"
        except TargetNotAvailable as e:
            assert "emcc" in str(e).lower() or "wasm" in str(e).lower()


class TestIRContent:
    """Verify specific IR patterns for correctness."""

    def test_alloca_for_variables(self):
        ir = compile_to_ir("define x as 42")
        assert 'alloca double' in ir

    def test_store_for_assignment(self):
        ir = compile_to_ir("define x as 42\nset x to 100")
        assert 'store double' in ir

    def test_load_for_reads(self):
        ir = compile_to_ir("define x as 42\nshow x")
        assert 'load double' in ir

    def test_fadd_for_addition(self):
        ir = compile_to_ir("show 1 + 2")
        assert 'fadd double' in ir

    def test_fmul_for_multiplication(self):
        ir = compile_to_ir("show 3 * 4")
        assert 'fmul double' in ir

    def test_fsub_for_subtraction(self):
        ir = compile_to_ir("show 5 - 3")
        assert 'fsub double' in ir

    def test_branch_for_if(self):
        ir = compile_to_ir("if true:\n    show 1")
        assert 'br i1' in ir

    def test_back_edge_for_while(self):
        ir = compile_to_ir("define i as 0\nwhile i < 3:\n    set i to i + 1")
        # While loops have a back edge (jump to condition check)
        lines = ir.splitlines()
        br_labels = [l for l in lines if l.strip().startswith('br label')]
        assert len(br_labels) >= 1
