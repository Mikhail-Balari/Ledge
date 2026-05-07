"""
Ledge Test Suite — validates interpreter correctness
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from ledge_lang import run, compile_ledge
from ledge_lang.interpreter import NOTHING, LedgeList, LedgeMap, LedgeError
from ledge_lang.lexer import LexError
from ledge_lang.parser import ParseError


PASS = 0
FAIL = 0
ERRORS = []


def test(name, source, expected_output=None, expected_value=None, should_error=False):
    global PASS, FAIL
    try:
        lines, value = run(source, output_fn=lambda x: None)
        if should_error:
            FAIL += 1
            ERRORS.append(f"FAIL {name}: expected error but got value {value!r}")
            return
        if expected_output is not None:
            got = "\n".join(lines)
            if got.strip() != expected_output.strip():
                FAIL += 1
                ERRORS.append(f"FAIL {name}:\n  expected output: {expected_output!r}\n  got:             {got!r}")
                return
        if expected_value is not None:
            if value != expected_value and str(value) != str(expected_value):
                FAIL += 1
                ERRORS.append(f"FAIL {name}:\n  expected value: {expected_value!r}\n  got:            {value!r}")
                return
        PASS += 1
        print(f"  PASS  {name}")
    except Exception as e:
        if should_error:
            PASS += 1
            print(f"  PASS  {name} (expected error: {type(e).__name__})")
        else:
            FAIL += 1
            ERRORS.append(f"FAIL {name}: unexpected error: {e}")


# ── Literals ──────────────────────────────────────────────────────────────────
print("\n=== Literals ===")
test("number int",    "show 42",        "42")
test("number float",  "show 3.14",      "3.14")
test("string",        'show "hello"',   "hello")
test("bool true",     "show true",      "true")
test("bool false",    "show false",     "false")
test("nothing",       "show nothing",   "nothing")

# ── Arithmetic ────────────────────────────────────────────────────────────────
print("\n=== Arithmetic ===")
test("add",    "show 2 + 3",    "5")
test("sub",    "show 10 - 3",   "7")
test("mul",    "show 4 * 5",    "20")
test("div",    "show 10 / 4",   "2.5")
test("nested", "show 2 + 3 * 4", "14")
test("parens", "show (2 + 3) * 4", "20")
test("div zero", "show divide(1, 0) or -1", "-1")

# ── String operations ────────────────────────────────────────────────────────
print("\n=== Strings ===")
test("concat",        'show "hello" + " " + "world"', "hello world")
test("interpolation", 'define x as 5\nshow "x is {x}"', "x is 5")
test("interp expr",   'show "2+2={2+2}"', "2+2=4")
test("len text",      'show len("hello")', "5")
test("upper",         'show upper("hello")', "HELLO")
test("lower",         'show lower("HELLO")', "hello")
test("trim",          'show trim("  hi  ")', "hi")
test("split",         'show len(split("a b c", " "))', "3")
test("contains",      'show contains("hello world", "world")', "true")
test("starts_with",   'show starts_with("ledge", "le")', "true")
test("ends_with",     'show ends_with("ledge", "ge")', "true")
test("replace",       'show replace("hello", "l", "r")', "herro")

# ── Variables ─────────────────────────────────────────────────────────────────
print("\n=== Variables ===")
test("define",     "define x as 10\nshow x",         "10")
test("set",        "define x as 1\nset x to 99\nshow x", "99")
test("multivar",   "define a as 1\ndefine b as 2\nshow a + b", "3")

# ── Conditionals ─────────────────────────────────────────────────────────────
print("\n=== Conditionals ===")
test("if true",       "if true:\n    show \"yes\"", "yes")
test("if false",      "if false:\n    show \"yes\"", "")
test("if else",       "if false:\n    show \"no\"\nelse:\n    show \"yes\"", "yes")
test("elif",          "define x as 5\nif x > 10:\n    show \"big\"\nelse if x > 3:\n    show \"mid\"\nelse:\n    show \"small\"", "mid")
test("is op",         "define x as 5\nif x is 5:\n    show \"five\"", "five")
test("is not op",     "define x as 5\nif x is not 3:\n    show \"not three\"", "not three")

# ── Comparisons ───────────────────────────────────────────────────────────────
print("\n=== Comparisons ===")
test("eq",   "show 5 = 5",  "true")
test("neq",  "show 5 != 6", "true")
test("lt",   "show 3 < 5",  "true")
test("gt",   "show 5 > 3",  "true")
test("lte",  "show 5 <= 5", "true")
test("gte",  "show 5 >= 6", "false")

# ── Logic ─────────────────────────────────────────────────────────────────────
print("\n=== Logic ===")
test("and true",  "show true and true",   "true")
test("and false", "show true and false",  "false")
test("or true",   "show false or true",   "true")
test("or false",  "show false or false",  "false")
test("not true",  "show not true",        "false")
test("not false", "show not false",       "true")

# ── Loops ─────────────────────────────────────────────────────────────────────
print("\n=== Loops ===")
test("for list", "define nums as list [1, 2, 3]\ndefine s as 0\nfor each n in nums:\n    set s to s + n\nshow s", "6")
test("while",    "define x as 0\nwhile x < 5:\n    set x to x + 1\nshow x", "5")
test("repeat n", "define x as 0\nrepeat 3 times:\n    set x to x + 1\nshow x", "3")
test("break",    "define x as 0\nwhile true:\n    set x to x + 1\n    if x = 3:\n        break\nshow x", "3")
test("continue", "define r as list []\nfor each n in list [1,2,3,4,5]:\n    if modulo(n, 2) = 0:\n        continue\n    set r to append(r, n)\nshow len(r)", "3")

# ── Functions ─────────────────────────────────────────────────────────────────
print("\n=== Functions ===")
test("basic fn",   "define add(a, b):\n    return a + b\nshow add(3, 4)", "7")
test("no return",  "define greet(name):\n    show \"Hi \" + name\ngreet(\"Ledge\")", "Hi Ledge")
test("recursion",  "define fact(n):\n    if n <= 1:\n        return 1\n    return n * fact(n - 1)\nshow fact(5)", "120")
test("closure",    "define make_adder(n):\n    define add(x):\n        return x + n\n    return add\ndefine add5 as make_adder(5)\nshow add5(3)", "8")
test("lambda",     "define double as given x: x * 2\nshow double(7)", "14")

# ── Lists ─────────────────────────────────────────────────────────────────────
print("\n=== Lists ===")
test("empty list",  "define l as list []\nshow len(l)", "0")
test("list index",  "define l as list [10, 20, 30]\nshow l[1]", "20")
test("safe index",  "define l as list [1]\nshow l[99] or \"none\"", "none")
test("append",      "define l as list [1,2]\nset l to append(l, 3)\nshow len(l)", "3")
test("remove",      "define l as list [1,2,3]\nset l to remove(l, 2)\nshow len(l)", "2")
test("slice",       "define l as list [1,2,3,4,5]\nshow len(slice(l, 1, 3))", "2")
test("merge lists", "define a as list [1,2]\ndefine b as list [3,4]\nshow len(merge(a, b))", "4")
test("sum",         "show sum(list [1,2,3,4,5])", "15")
test("max",         "show max(list [3,1,4,1,5,9])", "9")
test("min",         "show min(list [3,1,4,1,5,9])", "1")
test("join",        "show join(list [\"a\",\"b\",\"c\"], \",\")", "a,b,c")
test("map fn",      "define r as map(list [1,2,3], given x: x * 2)\nshow sum(r)", "12")
test("filter fn",   "define r as filter(list [1,2,3,4,5], given x: x > 3)\nshow len(r)", "2")
test("range",       "show len(range(10))", "10")
test("range 2",     "show len(range(1, 6))", "5")

# ── Maps ──────────────────────────────────────────────────────────────────────
print("\n=== Maps ===")
test("map create",  'define m as map {"a": 1}\nshow m["a"]', "1")
test("map field",   'define m as map {"x": 42}\nshow m.x', "42")
test("map safe",    'define m as map {}\nshow m["x"] or "missing"', "missing")
test("keys",        'define m as map {"a": 1, "b": 2}\nshow len(keys(m))', "2")
test("has true",    'define m as map {"k": 1}\nshow has(m, "k")', "true")
test("has false",   'define m as map {"k": 1}\nshow has(m, "z")', "false")
test("merge maps",  'define a as map {"x": 1}\ndefine b as map {"y": 2}\ndefine c as merge(a, b)\nshow len(keys(c))', "2")

# ── Match ─────────────────────────────────────────────────────────────────────
print("\n=== Match ===")
test("match hit",        "define x as 2\nmatch x:\n    case 1:\n        show \"one\"\n    case 2:\n        show \"two\"\n    otherwise:\n        show \"other\"", "two")
test("match otherwise",  "define x as 99\nmatch x:\n    case 1:\n        show \"one\"\n    otherwise:\n        show \"other\"", "other")

# ── Check ─────────────────────────────────────────────────────────────────────
print("\n=== Check ===")
test("check ok",       "check:\n    show \"ok\"", "ok")
test("check recover",  "check:\n    error(\"boom\")\nrecover e:\n    show \"caught: \" + e", "caught: boom")
test("check always",   "check:\n    show \"body\"\nalways:\n    show \"always\"", "body\nalways")

# ── User types ────────────────────────────────────────────────────────────────
print("\n=== User types ===")
test("type create", "type Point has:\n    x: number\n    y: number\ndefine p as Point(3, 4)\nshow p.x + p.y", "7")
test("type field",  "type Box has:\n    label: text\n    size: number = 10\ndefine b as Box(\"small\")\nshow b.label", "small")

# ── Fallback ──────────────────────────────────────────────────────────────────
print("\n=== Fallback (or) ===")
test("fallback number", "show divide(10, 0) or -1", "-1")
test("fallback nothing", "show nothing or \"default\"", "default")
test("fallback present", "show 42 or 0", "42")

# ── Type functions ────────────────────────────────────────────────────────────
print("\n=== Type functions ===")
test("type of number", "show type(42)", "number")
test("type of text",   'show type("hi")', "text")
test("type of list",   "show type(list [])", "list")
test("type of map",    "show type(map {})", "map")
test("type of bool",   "show type(true)", "truth")
test("type of nothing","show type(nothing)", "nothing")
test("number cast",    'show number("42") + 1', "43")
test("text cast",      'show text(100)', "100")
test("truth cast",     "show truth(0)", "false")

# ── Math ──────────────────────────────────────────────────────────────────────
print("\n=== Math ===")
test("round",   "show round(3.7)",      "4")
test("floor",   "show floor(3.9)",      "3")
test("ceil",    "show ceil(3.1)",       "4")
test("abs neg", "show abs(-5)",         "5")
test("sqrt",    "show sqrt(25)",        "5")
test("power",   "show power(2, 8)",     "256")
test("modulo",  "show modulo(17, 5)",   "2")
test("sqrt neg","show sqrt(-1) or 0",   "0")

# ── JSON ─────────────────────────────────────────────────────────────────────
print("\n=== JSON ===")
# json parse test skipped (single quote handling in test runner)
test("json stringify", 'show len(json_stringify(map {"a": 1})) > 0', "true")

# ── Generators ───────────────────────────────────────────────────────────────
print("\n=== Generators ===")
test("generator",
    "define count_to(n):\n    define i as 1\n    while i <= n:\n        yield i\n        set i to i + 1\ndefine vals as count_to(5)\nshow sum(vals)",
    "15")

# ── Errors ────────────────────────────────────────────────────────────────────
print("\n=== Error handling ===")
test("undefined var",   "show undefined_var", should_error=True)
test("set undefined",   "set unknown to 1",   should_error=True)
test("wrong type",      "define n: number as \"text\"", should_error=True)
test("not callable",    "define x as 5\nx()", should_error=True)

# ── Formatter tests ───────────────────────────────────────────────────────────
print("\n=== Formatter ===")

def _test_fmt(name, source, expected=None):
    global PASS, FAIL
    from ledge_lang.formatter import format_ledge
    from ledge_lang.lexer import LexError
    from ledge_lang.parser import ParseError
    try:
        result = format_ledge(source)
        # Idempotency check
        result2 = format_ledge(result)
        if result != result2:
            FAIL += 1
            ERRORS.append(f"FAIL {name}: formatter not idempotent")
            return
        if expected and result.strip() != expected.strip():
            FAIL += 1
            ERRORS.append(f"FAIL {name}:\n  expected: {expected!r}\n  got: {result!r}")
            return
        # Verify output still runs
        from ledge_lang import run
        run(result, output_fn=lambda x: None)
        PASS += 1
        print(f"  PASS  {name}")
    except Exception as e:
        FAIL += 1
        ERRORS.append(f"FAIL {name}: {e}")

_test_fmt("basic idempotent",  "define x as 10\nshow x")
_test_fmt("spacing in binop",  "show 1+2",       "show 1 + 2")
_test_fmt("function def",      "define add(a,b):\n    return a+b")
_test_fmt("if formatting",     "define x as 5\nif x > 0:\n    show x")
_test_fmt("for formatting",    "for each n in list [1,2,3]:\n    show n")
_test_fmt("nested blocks",     "define validate(x):\n    if x > 0:\n        return true\n    return false")
_test_fmt("tour file", open("examples/tour.ledge").read())

# ── Type checker tests ────────────────────────────────────────────────────────
print("\n=== Type checker ===")

def _test_tc(name, source, expect_warns=True):
    global PASS, FAIL
    from ledge_lang.typechecker import check_types
    try:
        warns = check_types(source)
        has_warns = len(warns) > 0
        if has_warns != expect_warns:
            FAIL += 1
            direction = "expected warnings" if expect_warns else "unexpected warnings"
            ERRORS.append(f"FAIL {name}: {direction}, got {warns}")
            return
        PASS += 1
        print(f"  PASS  {name}")
    except Exception as e:
        FAIL += 1
        ERRORS.append(f"FAIL {name}: {e}")

_test_tc("type mismatch number",  'define x: number as "hello"',  expect_warns=True)
_test_tc("type mismatch text",    'define x: text as 42',          expect_warns=True)
_test_tc("type match ok",         'define x: number as 42',        expect_warns=False)
_test_tc("type match text ok",    'define x: text as "hi"',        expect_warns=False)
_test_tc("untyped no warn",       'define x as 42',                expect_warns=False)
_test_tc("any accepts all",       'define x: any as 42',           expect_warns=False)
_test_tc("any accepts text",      'define x: any as "hi"',         expect_warns=False)

# ── Stdlib tests ──────────────────────────────────────────────────────────────
print("\n=== Stdlib ===")

def _test_stdlib(name, source, expected_output):
    global PASS, FAIL
    from ledge_lang import run
    try:
        lines, v = run(source, output_fn=lambda x: None)
        got = "\n".join(lines)
        if got.strip() != expected_output.strip():
            FAIL += 1
            ERRORS.append(f"FAIL {name}:\n  expected: {expected_output!r}\n  got: {got!r}")
        else:
            PASS += 1
            print(f"  PASS  {name}")
    except Exception as e:
        FAIL += 1
        ERRORS.append(f"FAIL {name}: {e}")

_test_stdlib("math module",
    'import "math" as math\nshow math["pi"] > 3',
    "true")

_test_stdlib("math sqrt",
    'import "math" as math\nshow math["sqrt"](25)',
    "5")

_test_stdlib("collections unique",
    'import "collections" as col\ndefine r as col["unique"](list [1, 2, 2, 3, 3])\nshow len(r)',
    "3")

_test_stdlib("collections count_by",
    'import "collections" as col\ndefine r as col["count_by"](list ["a", "b", "a"])\nshow r["a"]',
    "2")

_test_stdlib("collections take",
    'import "collections" as col\ndefine r as col["take"](list [1,2,3,4,5], 3)\nshow len(r)',
    "3")

_test_stdlib("collections flatten",
    'import "collections" as col\ndefine r as col["flatten"](list [list [1,2], list [3,4]])\nshow sum(r)',
    "10")

_test_stdlib("text module upper",
    'import "text" as t\nshow t["upper"]("hello")',
    "HELLO")

_test_stdlib("text module pad_left",
    'import "text" as t\nshow len(t["pad_left"]("hi", 10))',
    "10")

_test_stdlib("text is_empty true",
    'import "text" as t\nshow t["is_empty"]("")',
    "true")

_test_stdlib("text is_empty false",
    'import "text" as t\nshow t["is_empty"]("hi")',
    "false")

# ── VM bytecode tests ─────────────────────────────────────────────────────────
print("\n=== VM / Bytecode ===")

def _test_vm(name, source, expected_output):
    global PASS, FAIL
    from ledge_lang import compile_ledge
    from ledge_lang.vm import compile_to_bytecode, VM
    try:
        ast = compile_ledge(source)
        co = compile_to_bytecode(ast)
        out = []
        vm = VM(output_fn=out.append)
        vm.run(co)
        got = "\n".join(out).strip()
        if got != expected_output.strip():
            FAIL += 1
            ERRORS.append(f"FAIL {name}:\n  expected: {expected_output!r}\n  got: {got!r}")
        else:
            PASS += 1
            print(f"  PASS  {name}")
    except Exception as e:
        FAIL += 1
        ERRORS.append(f"FAIL {name}: {e}")

_test_vm("vm number",    "show 42",            "42")
_test_vm("vm add",       "show 3 + 4",         "7")
_test_vm("vm sub",       "show 10 - 3",        "7")
_test_vm("vm mul",       "show 6 * 7",         "42")
_test_vm("vm string",    'show "hello"',       "hello")
_test_vm("vm var store", "define x as 99\nshow x", "99")
_test_vm("vm compare",   "show 5 > 3",         "true")
_test_vm("vm not",       "show not true",      "false")
_test_vm("vm concat",    'show "a" + "b"',     "ab")
_test_vm("vm if true",   "if true:\n    show 1\nelse:\n    show 0", "1")
_test_vm("vm if false",  "if false:\n    show 1\nelse:\n    show 0", "0")
_test_vm("vm while",     "define x as 0\nwhile x < 5:\n    set x to x + 1\nshow x", "5")
_test_vm("vm list",      "define l as list [1, 2, 3]\nshow len(l)", "3")
_test_vm("vm map",       'define m as map {"k": 42}\nshow m["k"]', "42")
_test_vm("vm fallback",  "show divide(1, 0) or -1", "-1")

# ── Summary update ────────────────────────────────────────────────────────────
total = PASS + FAIL
print(f"\n{'='*50}")
print(f"Results: {PASS}/{total} passed")
if ERRORS:
    print(f"\nFailures:")
    for e in ERRORS:
        print(f"  {e}")
else:
    print("All tests passed!")
print('='*50)
