"""
Ledge Conformance Test Suite — pytest format
=============================================
284 tests covering every language construct.
This suite is the normative reference for conforming implementations.
A Ledge implementation is conforming if and only if all tests here pass.

Sections:
  1. Literals
  2. String Interpolation
  3. Arithmetic
  4. Comparison & Logic
  5. Variables & Scoping
  6. Control Flow
  7. Functions
  8. Match
  9. Error Handling
 10. Lists
 11. Maps
 12. Types
 13. Generators (Lazy)
 14. Parallel
 15. Python FFI
 16. Stdlib Modules
 17. Type System
 18. Negative / Error Cases
 19. Edge Cases
 20. Advanced Patterns
 21. JSON
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from ledge_lang import run
from ledge_lang.interpreter import LedgeError
from ledge_lang.lexer import LexError
from ledge_lang.parser import ParseError


def ok(src, expected):
    lines, _ = run(src.strip(), output_fn=lambda x: None)
    got = "\n".join(lines).strip()
    assert got == expected.strip(), f"\n  Expected: {expected!r}\n  Got:      {got!r}"

def err(src):
    try:
        run(src.strip(), output_fn=lambda x: None)
        assert False, f"Expected error, got no error"
    except (LexError, ParseError, LedgeError, RecursionError):
        pass


class TestLiterals:
    def test_int(self):              ok("show 42", "42")
    def test_zero(self):             ok("show 0", "0")
    def test_neg(self):              ok("show -5", "-5")
    def test_float(self):            ok("show 3.14", "3.14")
    def test_float_whole(self):      ok("show 1.0", "1")
    def test_str_empty(self):        ok('show ""', "")
    def test_str_basic(self):        ok('show "hello"', "hello")
    def test_str_spaces(self):       ok('show "hello world"', "hello world")
    def test_str_newline_esc(self):  ok('show "a\\nb"', "a\nb")
    def test_str_tab_esc(self):      ok('show "a\\tb"', "a\tb")
    def test_bool_true(self):        ok("show true", "true")
    def test_bool_false(self):       ok("show false", "false")
    def test_nothing(self):          ok("show nothing", "nothing")
    def test_list_empty(self):       ok("show list []", "[]")
    def test_list_basic(self):       ok("show list [1, 2, 3]", "[1, 2, 3]")
    def test_list_nested(self):      ok("show list [list [1, 2], list [3, 4]]", "[[1, 2], [3, 4]]")
    def test_map_empty(self):        ok("show map {}", "{}")
    def test_map_basic(self):        ok('show map {"k": 1}', '{"k": 1}')
    def test_large_int(self):        ok("show 1000000", "1000000")


class TestInterpolation:
    def test_simple_var(self):  ok('define x as 42\nshow "x={x}"', "x=42")
    def test_expression(self):  ok('show "2+2={2+2}"', "2+2=4")
    def test_nested(self):      ok('define a as 3\ndefine b as 4\nshow "h={sqrt(a*a+b*b)}"', "h=5")
    def test_multiple(self):    ok('define a as 1\ndefine b as 2\nshow "{a} and {b}"', "1 and 2")
    def test_bool_in_str(self): ok('show "it is {true}"', "it is true")
    def test_nothing_in_str(self): ok('show "val={nothing}"', "val=nothing")


class TestArithmetic:
    def test_add_int(self):       ok("show 3 + 4", "7")
    def test_add_float(self):     ok("show 1.5 + 2.5", "4")
    def test_sub(self):           ok("show 10 - 3", "7")
    def test_mul(self):           ok("show 6 * 7", "42")
    def test_div(self):           ok("show 10 / 4", "2.5")
    def test_div_zero_nothing(self): ok("show divide(10, 0)", "nothing")
    def test_div_zero_fallback(self): ok("show divide(10, 0) or -1", "-1")
    def test_mod(self):           ok("show modulo(17, 5)", "2")
    def test_mod_zero(self):      ok("show modulo(10, 0)", "nothing")
    def test_power(self):         ok("show power(2, 10)", "1024")
    def test_neg_unary(self):     ok("show -42", "-42")
    def test_prec_mul_over_add(self): ok("show 2 + 3 * 4", "14")
    def test_parens(self):        ok("show (2 + 3) * 4", "20")
    def test_str_concat(self):    ok('show "a" + "b" + "c"', "abc")
    def test_str_num_concat(self): ok('show "n=" + 42', "n=42")
    def test_num_str_concat(self): ok('show 42 + " things"', "42 things")
    def test_list_concat(self):   ok("show list [1, 2] + list [3, 4]", "[1, 2, 3, 4]")
    def test_sqrt_pos(self):      ok("show sqrt(25)", "5")
    def test_sqrt_zero(self):     ok("show sqrt(0)", "0")
    def test_sqrt_neg_nothing(self): ok("show sqrt(-1) or \"err\"", "err")
    def test_abs_neg(self):       ok("show abs(-42)", "42")
    def test_floor(self):         ok("show floor(3.9)", "3")
    def test_ceil(self):          ok("show ceil(3.1)", "4")
    def test_round_down(self):    ok("show round(3.4)", "3")
    def test_round_up(self):      ok("show round(3.5)", "4")
    def test_round_digits(self):  ok("show round(3.14159, 2)", "3.14")
    def test_int_power(self):     ok("show power(2, 62)", str(2**62))


class TestComparisonLogic:
    def test_eq_numbers(self):    ok("show 5 = 5", "true")
    def test_eq_strings(self):    ok('show "a" = "a"', "true")
    def test_neq(self):           ok("show 5 != 6", "true")
    def test_lt(self):            ok("show 3 < 5", "true")
    def test_gt(self):            ok("show 5 > 3", "true")
    def test_lte_eq(self):        ok("show 5 <= 5", "true")
    def test_gte_eq(self):        ok("show 5 >= 5", "true")
    # Critical invariants
    def test_true_neq_1(self):    ok("show true = 1", "false")
    def test_false_neq_0(self):   ok("show false = 0", "false")
    def test_nothing_eq_nothing(self): ok("show nothing = nothing", "true")
    def test_nothing_neq_0(self): ok("show nothing = 0", "false")
    def test_nothing_neq_false(self): ok("show nothing = false", "false")
    def test_and_true(self):      ok("show true and true", "true")
    def test_and_false(self):     ok("show true and false", "false")
    def test_and_sc(self):        ok("show false and divide(1, 0)", "false")
    def test_or_true(self):       ok("show false or true", "true")
    def test_or_false(self):      ok("show false or false", "false")
    def test_or_sc(self):         ok("show true or divide(1, 0)", "true")
    def test_not_true(self):      ok("show not true", "false")
    def test_not_false(self):     ok("show not false", "true")
    def test_not_nothing(self):   ok("show not nothing", "true")
    def test_zero_falsy(self):    ok("if 0:\n    show \"y\"\nelse:\n    show \"n\"", "n")
    def test_empty_str_falsy(self): ok('if "":\n    show "y"\nelse:\n    show "n"', "n")


class TestVariables:
    def test_define(self):        ok("define x as 10\nshow x", "10")
    def test_set(self):           ok("define x as 1\nset x to 99\nshow x", "99")
    def test_set_undef_err(self): err("set x to 10")
    def test_shadow(self):
        ok("define x as 1\ndefine f():\n    define x as 2\n    return x\nshow f()\nshow x", "2\n1")
    def test_closure_captures(self): ok("define x as 10\ndefine f():\n    return x\nshow f()", "10")
    def test_counter_closure(self):
        ok("""
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
    def test_type_hint_ok(self):  ok("define x: number as 42\nshow x", "42")
    def test_type_mismatch_err(self): err('define x: number as "bad"')
    def test_set_type_enforced(self): err("define x: number as 1\nset x to \"s\"")
    def test_any_accepts_all(self): ok("define x: any as 42\nset x to \"str\"\nshow x", "str")


class TestControlFlow:
    def test_if_true(self):   ok("if true:\n    show 1", "1")
    def test_if_false(self):  ok("if false:\n    show 1", "")
    def test_else(self):      ok("if false:\n    show 1\nelse:\n    show 2", "2")
    def test_elif(self):
        ok("define x as 2\nif x=1:\n    show \"one\"\nelse if x=2:\n    show \"two\"\nelse:\n    show \"other\"", "two")
    def test_for_list(self):  ok("for each x in list [1, 2, 3]:\n    show x", "1\n2\n3")
    def test_for_string(self): ok('for each c in "abc":\n    show c', "a\nb\nc")
    def test_for_map_kv(self): ok('define m as map {"x": 10}\nfor each k, v in m:\n    show k + "=" + v', "x=10")
    def test_while(self):     ok("define x as 0\nwhile x < 5:\n    set x to x + 1\nshow x", "5")
    def test_repeat_n(self):  ok("define x as 0\nrepeat 5 times:\n    set x to x + 1\nshow x", "5")
    def test_repeat_until(self): ok("define x as 0\nrepeat until x >= 5:\n    set x to x + 1\nshow x", "5")
    def test_break(self):
        ok("define x as 0\nwhile true:\n    set x to x + 1\n    if x = 3:\n        break\nshow x", "3")
    def test_continue(self):
        ok("""
define r as list []
for each n in list [1,2,3,4,5]:
    if modulo(n, 2) = 0:
        continue
    set r to append(r, n)
show r
""", "[1, 3, 5]")
    def test_pass(self): ok("if true:\n    pass\nshow 1", "1")


class TestFunctions:
    def test_basic(self):   ok("define f():\n    return 42\nshow f()", "42")
    def test_args(self):    ok("define add(a, b):\n    return a + b\nshow add(3, 4)", "7")
    def test_no_return(self): ok("define f():\n    define x as 1\nshow f()", "nothing")
    def test_recursion(self):
        ok("define fact(n):\n    if n <= 1:\n        return 1\n    return n * fact(n - 1)\nshow fact(10)", "3628800")
    def test_mutual_recursion(self):
        ok("""
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
    def test_first_class(self):
        ok("define apply(f, x):\n    return f(x)\ndefine double(x):\n    return x * 2\nshow apply(double, 21)", "42")
    def test_lambda(self):    ok("define f as given x: x * 2\nshow f(5)", "10")
    def test_lambda_multi(self): ok("define f as given (a, b): a + b\nshow f(3, 4)", "7")
    def test_returns_fn(self):
        ok("define make_adder(n):\n    return given x: x + n\ndefine add5 as make_adder(5)\nshow add5(37)", "42")
    def test_missing_arg_err(self): err("define f(a, b):\n    return a + b\nf(1)")
    def test_typed_params_ok(self): ok("define mul(a: number, b: number):\n    return a * b\nshow mul(6, 7)", "42")
    def test_typed_params_err(self): err("define f(x: number):\n    return x\nf(\"str\")")


class TestMatch:
    def test_hit(self):   ok("match 2:\n    case 1:\n        show \"one\"\n    case 2:\n        show \"two\"", "two")
    def test_otherwise(self): ok("match 99:\n    case 1:\n        show \"one\"\n    otherwise:\n        show \"other\"", "other")
    def test_string(self): ok('match "hi":\n    case "hi":\n        show "hello"\n    case "bye":\n        show "bye"', "hello")
    def test_no_match(self): ok("match 42:\n    case 1:\n        show \"one\"\nshow \"done\"", "done")
    def test_bool(self):  ok("match true:\n    case true:\n        show \"yes\"\n    case false:\n        show \"no\"", "yes")


class TestErrorHandling:
    def test_check_ok(self):  ok("check:\n    show 1", "1")
    def test_recover(self):   ok("check:\n    error(\"boom\")\nrecover e:\n    show e", "boom")
    def test_always(self):    ok("check:\n    show 1\nalways:\n    show 2", "1\n2")
    def test_recover_always(self):
        ok("check:\n    error(\"e\")\nrecover e:\n    show \"caught\"\nalways:\n    show \"always\"", "caught\nalways")
    def test_propagate(self):
        ok("define f():\n    error(\"from f\")\ncheck:\n    f()\nrecover e:\n    show e", "from f")
    def test_or_nothing(self): ok("show nothing or \"default\"", "default")
    def test_or_div(self):     ok("show divide(1, 0) or 0", "0")
    def test_or_index(self):   ok("show list [1][99] or \"miss\"", "miss")
    def test_or_map(self):     ok("show map {}[\"k\"] or \"none\"", "none")
    def test_or_chain(self):   ok("show nothing or nothing or \"found\"", "found")
    def test_or_present(self): ok("show 42 or 0", "42")
    def test_assert_pass(self): ok("assert(1 = 1)\nshow \"ok\"", "ok")
    def test_assert_fail(self): err("assert(1 = 2)")
    def test_nested_check(self):
        ok("""
check:
    check:
        error("inner")
    recover e:
        show "inner: " + e
    show "outer ok"
""", "inner: inner\nouter ok")
    def test_yield_outside_err(self): err("yield 1")
    def test_break_outside_err(self): err("break")
    def test_continue_outside_err(self): err("continue")


class TestLists:
    def test_index_0(self):   ok("show list [10, 20, 30][0]", "10")
    def test_index_2(self):   ok("show list [10, 20, 30][2]", "30")
    def test_oob_nothing(self): ok("show list [1][99]", "nothing")
    def test_neg_nothing(self): ok("show list [1, 2, 3][-1]", "nothing")
    def test_append(self):    ok("show len(append(list [1, 2], 3))", "3")
    def test_remove(self):    ok("show len(remove(list [1, 2, 3], 2))", "2")
    def test_slice(self):     ok("show slice(list [1,2,3,4,5], 1, 3)", "[2, 3]")
    def test_merge(self):     ok("show merge(list [1,2], list [3,4])", "[1, 2, 3, 4]")
    def test_sum(self):       ok("show sum(list [1,2,3,4,5])", "15")
    def test_sum_empty(self): ok("show sum(list [])", "0")
    def test_max(self):       ok("show max(list [3,1,4,1,5,9])", "9")
    def test_min(self):       ok("show min(list [3,1,4,1,5,9])", "1")
    def test_sort(self):      ok("show sort(list [3,1,4,1,5])", "[1, 1, 3, 4, 5]")
    def test_join(self):      ok('show join(list ["a","b","c"], ",")', "a,b,c")
    def test_map_fn(self):    ok("show map(list [1,2,3], given x: x * 2)", "[2, 4, 6]")
    def test_filter_fn(self): ok("show filter(list [1,2,3,4,5], given x: x > 3)", "[4, 5]")
    def test_filter_empty(self): ok("show filter(list [1,2,3], given x: x > 10)", "[]")
    def test_reduce(self):    ok("show reduce(list [1,2,3,4,5], given (a,b): a + b, 0)", "15")
    def test_has_true(self):  ok("show has(list [1,2,3], 2)", "true")
    def test_has_false(self): ok("show has(list [1,2,3], 9)", "false")
    def test_range(self):     ok("show len(range(10))", "10")
    def test_range_2(self):   ok("show range(2, 5)", "[2, 3, 4]")
    def test_nested(self):    ok("show list [list [1,2], list [3,4]][0][1]", "2")
    def test_flatten(self):   ok("show flatten(list [list [1,2], list [3,4]])", "[1, 2, 3, 4]")
    def test_zip_fn(self):    ok("show zip(list [1,2,3], list [4,5,6])", "[[1, 4], [2, 5], [3, 6]]")
    def test_first(self):     ok("show first(list [10,20,30])", "10")
    def test_is_empty_t(self): ok("show is_empty(list [])", "true")
    def test_is_empty_f(self): ok("show is_empty(list [1])", "false")
    def test_index_of(self):  ok("show index_of(list [10,20,30], 20)", "1")
    def test_index_of_miss(self): ok("show index_of(list [10,20,30], 99)", "nothing")


class TestMaps:
    def test_create(self):    ok('show map {"a": 1}["a"]', "1")
    def test_field_dot(self): ok('define m as map {"x": 42}\nshow m.x', "42")
    def test_missing(self):   ok('show map {}["k"]', "nothing")
    def test_keys(self):      ok('show len(keys(map {"a":1,"b":2}))', "2")
    def test_values(self):    ok('show sum(values(map {"a":1,"b":2}))', "3")
    def test_has_key(self):   ok('show has(map {"k": 1}, "k")', "true")
    def test_merge(self):     ok('show merge(map {"a":1}, map {"b":2})["b"]', "2")
    def test_merge_overwrite(self): ok('show merge(map {"k":1}, map {"k":2})["k"]', "2")
    def test_nested(self):    ok('define m as map {"o": map {"i": 42}}\nshow m["o"]["i"]', "42")
    def test_nested_field(self): ok('define m as map {"o": map {"i": 42}}\nshow m.o.i', "42")
    def test_map_in_list(self): ok('define l as list [map {"v":1}, map {"v":2}]\nshow l[0]["v"]', "1")


class TestTypes:
    def test_basic(self):
        ok("type P has:\n    x: number\n    y: number\ndefine p as P(3, 4)\nshow p.x + p.y", "7")
    def test_default(self):
        ok("type C has:\n    v: number = 0\ndefine c as C()\nshow c.v", "0")
    def test_field_access(self):
        ok("type T has:\n    name: text\ndefine t as T(\"Ledge\")\nshow t.name", "Ledge")
    def test_type_of(self):
        ok("type T has:\n    x: number\ndefine t as T(1)\nshow type(t)", "T")
    def test_field_type_check(self): err("type T has:\n    x: number\nT(\"str\")")


class TestGenerators:
    def test_finite(self):
        ok("""
define countdown(n):
    define i as n
    while i > 0:
        yield i
        set i to i - 1
define c as countdown(3)
show collect(c)
""", "[3, 2, 1]")

    def test_sum_gen(self):
        ok("""
define nums():
    yield 1
    yield 2
    yield 3
    yield 4
    yield 5
show sum(collect(nums()))
""", "15")

    def test_indexed(self):
        ok("""
define squares():
    define i as 1
    while i <= 10:
        yield i * i
        set i to i + 1
define s as squares()
show s[0]
show s[4]
""", "1\n25")

    def test_infinite(self):
        ok("""
define naturals(start):
    define n as start
    while true:
        yield n
        set n to n + 1
define g as naturals(10)
show g[0]
show g[9]
""", "10\n19")

    def test_for_loop(self):
        ok("""
define evens(limit):
    define n as 0
    while n <= limit:
        if modulo(n, 2) = 0:
            yield n
        set n to n + 1
for each e in evens(8):
    show e
""", "0\n2\n4\n6\n8")


class TestParallel:
    def test_basic(self):
        ok("define results as parallel [1 + 1, 2 + 2, 3 + 3]\nshow sum(results)", "12")
    def test_order_preserved(self):
        ok("define r as parallel [10, 20, 30]\nshow r[0]\nshow r[2]", "10\n30")


class TestPythonFFI:
    def test_math(self):
        ok('import "python:math" as m\nshow m["pi"] > 3\nshow m["sqrt"](144)', "true\n12")
    def test_json(self):
        ok('import "python:json" as j\ndefine d as j["loads"]("{}")\nshow type(d)', "map")
    def test_not_found_err(self):
        err('import "python:nonexistent_xyz_00000" as m')


class TestStdlib:
    def test_math_pi(self):   ok('import "math" as m\nshow m["pi"] > 3', "true")
    def test_math_sqrt(self): ok('import "math" as m\nshow m["sqrt"](25)', "5")
    def test_col_unique(self): ok('import "collections" as c\nshow len(c["unique"](list [1,2,2,3]))', "3")
    def test_col_count_by(self): ok('import "collections" as c\ndefine r as c["count_by"](list ["a","b","a"])\nshow r["a"]', "2")
    def test_col_flatten(self): ok('import "collections" as c\nshow c["flatten"](list [list [1,2],list [3,4]])', "[1, 2, 3, 4]")
    def test_col_take(self):  ok('import "collections" as c\nshow c["take"](list [1,2,3,4,5], 3)', "[1, 2, 3]")
    def test_text_upper(self): ok('import "text" as t\nshow t["upper"]("hello")', "HELLO")
    def test_text_words(self): ok('import "text" as t\nshow len(t["words"]("the quick brown fox"))', "4")
    def test_env_miss(self):  ok('import "env" as e\nshow e["get"]("__NONEXISTENT_XYZ__", "default")', "default")


class TestTypeSystem:
    def test_type_number(self): ok("show type(42)", "number")
    def test_type_text(self):   ok('show type("hi")', "text")
    def test_type_truth(self):  ok("show type(true)", "truth")
    def test_type_list(self):   ok("show type(list [])", "list")
    def test_type_map(self):    ok("show type(map {})", "map")
    def test_type_nothing(self): ok("show type(nothing)", "nothing")
    def test_type_fn(self):     ok("define f():\n    pass\nshow type(f)", "function")
    def test_cast_num_str(self): ok('show number("42")', "42")
    def test_cast_num_fail(self): ok('show number("abc") or -1', "-1")
    def test_cast_text_num(self): ok("show text(42)", "42")
    def test_cast_truth_0(self): ok("show truth(0)", "false")
    def test_cast_truth_1(self): ok("show truth(1)", "true")
    def test_cast_truth_str(self): ok('show truth("")', "false")
    def test_cast_truth_nonstr(self): ok('show truth("x")', "true")


class TestNegativeCases:
    def test_undef_var(self):      err("show undefined_xyz_var")
    def test_set_undef(self):      err("set xyz to 1")
    def test_call_non_fn_num(self): err("define x as 5\nx()")
    def test_call_non_fn_str(self): err('("hello")()')
    def test_type_mismatch_add(self): err("show 1 + true")
    def test_index_non_list(self): err("show 42[0]")
    def test_type_hint_bool(self): err("define n: number as true")
    def test_missing_arg(self):    err("define f(a, b):\n    return a+b\nf(1)")
    def test_div_zero_nothing(self): ok("define r as 1/0\nshow r", "nothing")
    def test_sqrt_neg_nothing(self): ok("show sqrt(-4) or \"err\"", "err")


class TestEdgeCases:
    def test_nothing_eq_nothing(self): ok("show nothing = nothing", "true")
    def test_nothing_neq_0(self):      ok("show nothing = 0", "false")
    def test_nothing_neq_false(self):  ok("show nothing = false", "false")
    def test_true_neq_1(self):         ok("show true = 1", "false")
    def test_false_neq_0(self):        ok("show false = 0", "false")
    def test_empty_list_falsy(self):   ok("if list []:\n    show \"y\"\nelse:\n    show \"n\"", "n")
    def test_empty_map_falsy(self):    ok('if map {}:\n    show "y"\nelse:\n    show "n"', "n")
    def test_or_chain(self):           ok("show nothing or nothing or 42", "42")
    def test_fn_returns_fn(self):      ok("define f():\n    return given x: x * 2\nshow f()(21)", "42")
    def test_deep_recursion(self):
        ok("define sum_to(n):\n    if n = 0:\n        return 0\n    return n + sum_to(n - 1)\nshow sum_to(100)", "5050")
    def test_nothing_in_list(self):    ok("define l as list [1, nothing, 3]\nshow l[1]", "nothing")
    def test_float_list_index(self):   ok("show list [1,2,3][1.0]", "2")
    def test_closure_mutual_recursion(self):
        ok("""
define is_even(n):
    if n = 0:
        return true
    return is_odd(n - 1)
define is_odd(n):
    if n = 0:
        return false
    return is_even(n - 1)
show is_even(4)
show is_odd(3)
""", "true\ntrue")


class TestAdvancedPatterns:
    def test_quicksort(self):
        ok("""
define quicksort(lst):
    if len(lst) <= 1:
        return lst
    define pivot as lst[0]
    define rest as slice(lst, 1)
    define smaller as filter(rest, given x: x < pivot)
    define greater as filter(rest, given x: x >= pivot)
    return merge(quicksort(smaller), merge(list [pivot], quicksort(greater)))
define r as quicksort(list [64, 34, 25, 12, 22, 11, 90, 42, 7, 55])
show r
""", "[7, 11, 12, 22, 25, 34, 42, 55, 64, 90]")

    def test_memoize(self):
        ok("""
define make_memo(f):
    define cache as map {}
    define memoized(n):
        define key as text(n)
        if has(cache, key):
            return cache[key]
        define result as f(n)
        set cache to merge(cache, map {key: result})
        return result
    return memoized
define slow_square(n):
    return n * n
define fast_square as make_memo(slow_square)
show fast_square(7)
show fast_square(7)
""", "49\n49")

    def test_fizzbuzz(self):
        ok("""
define fb as list []
for each n in range(1, 16):
    if modulo(n, 15) = 0:
        set fb to append(fb, "FizzBuzz")
    else if modulo(n, 3) = 0:
        set fb to append(fb, "Fizz")
    else if modulo(n, 5) = 0:
        set fb to append(fb, "Buzz")
    else:
        set fb to append(fb, text(n))
show fb[14]
show fb[2]
show fb[4]
""", "FizzBuzz\nFizz\nBuzz")

    def test_pipeline(self):
        ok("""
define numbers as range(1, 11)
define result as sum(filter(map(numbers, given x: x * x), given x: modulo(x, 2) = 0))
show result
""", "220")


class TestJSON:
    def test_parse_null(self):    ok('show json_parse("null")', "nothing")
    def test_parse_bool(self):    ok('show json_parse("true")', "true")
    def test_parse_array(self):   ok('define l as json_parse("[1,2,3]")\nshow sum(l)', "6")
    def test_stringify(self):     ok('show len(json_stringify(map {"a": 1})) > 0', "true")
    def test_stringify_list(self): ok('show json_stringify(list [1,2,3])', "[1, 2, 3]")
    def test_roundtrip(self):
        ok('define m as map {"n": 42}\ndefine s as json_stringify(m)\ndefine m2 as json_parse(s)\nshow m2["n"]', "42")
    def test_invalid_nothing(self): ok('show json_parse("not json") or "bad"', "bad")
