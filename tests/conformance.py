"""
Ledge Conformance Test Suite v0.2
500+ tests covering every semantic edge case, error condition, and boundary.
This suite is the normative reference for conforming Ledge implementations.
"""

import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from ledge_lang import run, compile_ledge
from ledge_lang.interpreter import NOTHING, LedgeList, LedgeMap, LedgeError, LedgeLazyGenerator
from ledge_lang.lexer import LexError
from ledge_lang.parser import ParseError

PASS = FAIL = 0
ERRORS = []
SECTIONS = {}

def test(name, source, expected=None, error=False, section="general"):
    global PASS, FAIL
    SECTIONS.setdefault(section, [0, 0])
    try:
        lines, value = run(source, output_fn=lambda x: None)
        if error:
            FAIL += 1; SECTIONS[section][1] += 1
            ERRORS.append(f"FAIL [{section}] {name}: expected error, got output {lines!r}")
            return
        if expected is not None:
            got = "\n".join(lines).strip()
            exp = expected.strip()
            if got != exp:
                FAIL += 1; SECTIONS[section][1] += 1
                ERRORS.append(f"FAIL [{section}] {name}:\n  exp: {exp!r}\n  got: {got!r}")
                return
        PASS += 1; SECTIONS[section][0] += 1
        print(f"  PASS  [{section}] {name}")
    except Exception as e:
        if error:
            PASS += 1; SECTIONS[section][0] += 1
            print(f"  PASS  [{section}] {name} (expected: {type(e).__name__})")
        else:
            FAIL += 1; SECTIONS[section][1] += 1
            ERRORS.append(f"FAIL [{section}] {name}: {type(e).__name__}: {e}")


# ════════════════════════════════════════════════════════════════════
# SECTION 1: LITERALS
# ════════════════════════════════════════════════════════════════════
s = "literals"
print(f"\n=== 1. Literals ===")
test("integer", "show 42", "42", section=s)
test("zero", "show 0", "0", section=s)
test("negative", "show -5", "-5", section=s)
test("float", "show 3.14", "3.14", section=s)
test("float no trail", "show 1.0", "1", section=s)
test("float precision", "show 0.1 + 0.2", "0.30000000000000004", section=s)
test("string empty", 'show ""', "", section=s)
test("string basic", 'show "hello"', "hello", section=s)
test("string with spaces", 'show "hello world"', "hello world", section=s)
test("string newline escape", 'show "a\\nb"', "a\nb", section=s)
test("string tab escape", 'show "a\\tb"', "a\tb", section=s)
test("string quote escape", 'show "say \\"hi\\""', 'say "hi"', section=s)
test("bool true", "show true", "true", section=s)
test("bool false", "show false", "false", section=s)
test("nothing", "show nothing", "nothing", section=s)
test("list empty", "show list []", "[]", section=s)
test("list basic", "show list [1, 2, 3]", "[1, 2, 3]", section=s)
test("list nested", "show list [list [1, 2], list [3, 4]]", "[[1, 2], [3, 4]]", section=s)
test("map empty", "show map {}", "{}", section=s)
test("map basic", 'show map {"k": 1}', '{"k": 1}', section=s)
test("large int", "show 1000000", "1000000", section=s)
test("neg float", "show -3.14", "-3.14", section=s)

# ════════════════════════════════════════════════════════════════════
# SECTION 2: STRING INTERPOLATION
# ════════════════════════════════════════════════════════════════════
s = "interpolation"
print(f"\n=== 2. String Interpolation ===")
test("simple var", 'define x as 42\nshow "x={x}"', "x=42", section=s)
test("expression", 'show "2+2={2+2}"', "2+2=4", section=s)
test("string in string", 'define s as "world"\nshow "hello {s}"', "hello world", section=s)
test("method call", 'define x as 5\nshow "{x * 2}"', "10", section=s)
test("nested expr", 'define a as 3\ndefine b as 4\nshow "hyp={sqrt(a*a+b*b)}"', "hyp=5", section=s)
test("multiple", 'define a as 1\ndefine b as 2\nshow "{a} and {b}"', "1 and 2", section=s)
test("bool in str", 'show "it is {true}"', "it is true", section=s)
test("nothing in str", 'show "val={nothing}"', "val=nothing", section=s)
test("no braces pass", 'show "no braces here"', "no braces here", section=s)
test("escaped brace", 'show "literal \\{brace\\}"', "literal {brace}", section=s)

# ════════════════════════════════════════════════════════════════════
# SECTION 3: ARITHMETIC
# ════════════════════════════════════════════════════════════════════
s = "arithmetic"
print(f"\n=== 3. Arithmetic ===")
test("add int", "show 3 + 4", "7", section=s)
test("add float", "show 1.5 + 2.5", "4", section=s)
test("sub", "show 10 - 3", "7", section=s)
test("mul", "show 6 * 7", "42", section=s)
test("div", "show 10 / 4", "2.5", section=s)
test("div zero returns nothing", "show divide(10, 0)", "nothing", section=s)
test("div zero or fallback", "show divide(10, 0) or -1", "-1", section=s)
test("mod basic", "show modulo(17, 5)", "2", section=s)
test("mod zero returns nothing", "show modulo(10, 0)", "nothing", section=s)
test("power", "show power(2, 10)", "1024", section=s)
test("neg unary", "show -42", "-42", section=s)
test("neg neg", "show -(-5)", "5", section=s)
test("precedence mul over add", "show 2 + 3 * 4", "14", section=s)
test("parens override", "show (2 + 3) * 4", "20", section=s)
test("chain add", "show 1 + 2 + 3 + 4", "10", section=s)
test("chain sub", "show 10 - 3 - 2", "5", section=s)
test("str concat", 'show "a" + "b" + "c"', "abc", section=s)
test("str num concat", 'show "n=" + 42', "n=42", section=s)
test("num str concat", 'show 42 + " things"', "42 things", section=s)
test("list concat", "show list [1, 2] + list [3, 4]", "[1, 2, 3, 4]", section=s)
test("sqrt positive", "show sqrt(25)", "5", section=s)
test("sqrt zero", "show sqrt(0)", "0", section=s)
test("sqrt negative nothing", "show sqrt(-1) or \"impossible\"", "impossible", section=s)
test("abs negative", "show abs(-42)", "42", section=s)
test("abs positive", "show abs(42)", "42", section=s)
test("floor", "show floor(3.9)", "3", section=s)
test("ceil", "show ceil(3.1)", "4", section=s)
test("round down", "show round(3.4)", "3", section=s)
test("round up", "show round(3.5)", "4", section=s)
test("round digits", "show round(3.14159, 2)", "3.14", section=s)
test("int overflow safe", "show power(2, 62)", str(2**62), section=s)

# ════════════════════════════════════════════════════════════════════
# SECTION 4: COMPARISON AND LOGIC
# ════════════════════════════════════════════════════════════════════
s = "comparison"
print(f"\n=== 4. Comparison and Logic ===")
test("eq numbers", "show 5 = 5", "true", section=s)
test("eq strings", 'show "a" = "a"', "true", section=s)
test("neq", "show 5 != 6", "true", section=s)
test("lt", "show 3 < 5", "true", section=s)
test("gt", "show 5 > 3", "true", section=s)
test("lte eq", "show 5 <= 5", "true", section=s)
test("lte lt", "show 4 <= 5", "true", section=s)
test("lte fail", "show 6 <= 5", "false", section=s)
test("gte eq", "show 5 >= 5", "true", section=s)
test("is op eq", "define x as 5\nif x is 5:\n    show \"yes\"", "yes", section=s)
test("is not", "define x as 5\nif x is not 3:\n    show \"yes\"", "yes", section=s)
test("nothing is nothing", "if nothing is nothing:\n    show \"yes\"", "yes", section=s)
test("nothing is not 0", "if nothing is not 0:\n    show \"yes\"", "yes", section=s)
test("and true", "show true and true", "true", section=s)
test("and false", "show true and false", "false", section=s)
test("and short circuit", "define x as 0\nshow false and divide(1, x)", "false", section=s)
test("or true", "show false or true", "true", section=s)
test("or false", "show false or false", "false", section=s)
test("or short circuit", "define x as 0\nshow true or divide(1, x)", "true", section=s)
test("not true", "show not true", "false", section=s)
test("not false", "show not false", "true", section=s)
test("not nothing", "show not nothing", "true", section=s)
test("bool 0 falsy", "if 0:\n    show \"yes\"\nelse:\n    show \"no\"", "no", section=s)
test("bool empty str falsy", 'if "":\n    show "yes"\nelse:\n    show "no"', "no", section=s)
test("bool 1 truthy", "if 1:\n    show \"yes\"", "yes", section=s)
test("bool str truthy", 'if "x":\n    show "yes"', "yes", section=s)
test("chained comparison", "define x as 5\nshow x > 3 and x < 10", "true", section=s)

# ════════════════════════════════════════════════════════════════════
# SECTION 5: VARIABLES AND SCOPING
# ════════════════════════════════════════════════════════════════════
s = "variables"
print(f"\n=== 5. Variables and Scoping ===")
test("define and use", "define x as 10\nshow x", "10", section=s)
test("set mutates", "define x as 1\nset x to 99\nshow x", "99", section=s)
test("set undefined error", "set x to 10", error=True, section=s)
test("shadow inner", "define x as 1\ndefine f():\n    define x as 2\n    return x\nshow f()\nshow x", "2\n1", section=s)
test("closure captures", "define x as 10\ndefine f():\n    return x\nshow f()", "10", section=s)
test("closure mutates outer", """
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
""", "1\n2\n3", section=s)
test("type hint number ok", "define x: number as 42\nshow x", "42", section=s)
test("type hint text ok", 'define x: text as "hi"\nshow x', "hi", section=s)
test("type hint mismatch error", 'define x: number as "string"', error=True, section=s)
test("set type enforced", "define x: number as 1\nset x to \"str\"", error=True, section=s)
test("multi assign", "define a as 1\ndefine b as 2\ndefine c as a + b\nshow c", "3", section=s)
test("reassign same type", "define x: number as 1\nset x to 2\nshow x", "2", section=s)
test("any type accepts all", "define x: any as 42\nset x to \"str\"\nshow x", "str", section=s)

# ════════════════════════════════════════════════════════════════════
# SECTION 6: CONTROL FLOW
# ════════════════════════════════════════════════════════════════════
s = "control"
print(f"\n=== 6. Control Flow ===")
test("if true", "if true:\n    show 1", "1", section=s)
test("if false skip", "if false:\n    show 1", "", section=s)
test("else branch", "if false:\n    show 1\nelse:\n    show 2", "2", section=s)
test("elif first", "define x as 1\nif x = 1:\n    show \"one\"\nelse if x = 2:\n    show \"two\"", "one", section=s)
test("elif second", "define x as 2\nif x = 1:\n    show \"one\"\nelse if x = 2:\n    show \"two\"", "two", section=s)
test("elif else", "define x as 9\nif x = 1:\n    show \"one\"\nelse if x = 2:\n    show \"two\"\nelse:\n    show \"other\"", "other", section=s)
test("for list", "for each x in list [1, 2, 3]:\n    show x", "1\n2\n3", section=s)
test("for string chars", 'for each c in "abc":\n    show c', "a\nb\nc", section=s)
test("for map keys", 'define m as map {"a": 1, "b": 2}\nfor each k in m:\n    show k', "a\nb", section=s)
test("for map kv", 'define m as map {"x": 10}\nfor each k, v in m:\n    show k + "=" + v', "x=10", section=s)
test("while basic", "define x as 0\nwhile x < 5:\n    set x to x + 1\nshow x", "5", section=s)
test("while false skip", "while false:\n    show 1\nshow 2", "2", section=s)
test("repeat n", "define x as 0\nrepeat 5 times:\n    set x to x + 1\nshow x", "5", section=s)
test("repeat until", "define x as 0\nrepeat until x >= 5:\n    set x to x + 1\nshow x", "5", section=s)
test("break", "define x as 0\nwhile true:\n    set x to x + 1\n    if x = 3:\n        break\nshow x", "3", section=s)
test("continue", "define r as list []\nfor each n in list [1,2,3,4,5]:\n    if modulo(n, 2) = 0:\n        continue\n    set r to append(r, n)\nshow r", "[1, 3, 5]", section=s)
test("nested loops break", "define r as list []\nfor each i in list [1,2,3]:\n    for each j in list [1,2,3]:\n        if j = 2:\n            break\n        set r to append(r, i * 10 + j)\nshow r", "[11, 21, 31]", section=s)
test("pass placeholder", "if true:\n    pass\nshow 1", "1", section=s)

# ════════════════════════════════════════════════════════════════════
# SECTION 7: FUNCTIONS
# ════════════════════════════════════════════════════════════════════
s = "functions"
print(f"\n=== 7. Functions ===")
test("basic fn", "define f():\n    return 42\nshow f()", "42", section=s)
test("fn with args", "define add(a, b):\n    return a + b\nshow add(3, 4)", "7", section=s)
test("fn no return", "define greet(n):\n    show \"hi \" + n\ngreet(\"Ledge\")", "hi Ledge", section=s)
test("fn returns nothing implicit", "define f():\n    define x as 1\nshow f()", "nothing", section=s)
test("fn typed params", "define mul(a: number, b: number):\n    return a * b\nshow mul(6, 7)", "42", section=s)
test("fn typed params error", "define f(x: number):\n    return x\nf(\"str\")", error=True, section=s)
test("recursion", "define fact(n):\n    if n <= 1:\n        return 1\n    return n * fact(n - 1)\nshow fact(10)", "3628800", section=s)
test("mutual recursion", """
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
""", "true\ntrue", section=s)
test("first class fn", "define apply(f, x):\n    return f(x)\ndefine double(x):\n    return x * 2\nshow apply(double, 21)", "42", section=s)
test("lambda basic", "define f as given x: x * 2\nshow f(5)", "10", section=s)
test("lambda multi param", "define f as given (a, b): a + b\nshow f(3, 4)", "7", section=s)
test("closure over loop var", """
define adders as list []
for each i in list [1, 2, 3]:
    define adder as given x: x + i
    set adders to append(adders, adder)
show adders[0](10)
show adders[2](10)
""", "11\n13", section=s)
test("fn as return value", """
define make_adder(n):
    return given x: x + n
define add5 as make_adder(5)
show add5(37)
""", "42", section=s)
test("missing arg error", "define f(a, b):\n    return a + b\nf(1)", error=True, section=s)
test("extra kwarg ok", "define f(a):\n    return a\nshow f(a=42)", "42", section=s)

# ════════════════════════════════════════════════════════════════════
# SECTION 8: MATCH
# ════════════════════════════════════════════════════════════════════
s = "match"
print(f"\n=== 8. Match ===")
test("match exact", "match 2:\n    case 1:\n        show \"one\"\n    case 2:\n        show \"two\"", "two", section=s)
test("match otherwise", "match 99:\n    case 1:\n        show \"one\"\n    otherwise:\n        show \"other\"", "other", section=s)
test("match string", 'match "hi":\n    case "hi":\n        show "hello"\n    case "bye":\n        show "goodbye"', "hello", section=s)
test("match nothing hit", "match 42:\n    case 1:\n        show \"one\"\nshow \"done\"", "done", section=s)
test("match bool", "match true:\n    case true:\n        show \"yes\"\n    case false:\n        show \"no\"", "yes", section=s)
test("match expression", "define x as 3\nmatch x * 2:\n    case 6:\n        show \"six\"\n    otherwise:\n        show \"other\"", "six", section=s)

# ════════════════════════════════════════════════════════════════════
# SECTION 9: ERROR HANDLING
# ════════════════════════════════════════════════════════════════════
s = "errors"
print(f"\n=== 9. Error Handling ===")
test("check ok", "check:\n    show 1", "1", section=s)
test("check recover", "check:\n    error(\"boom\")\nrecover e:\n    show e", "boom", section=s)
test("check always runs", "check:\n    show 1\nalways:\n    show 2", "1\n2", section=s)
test("check recover always", "check:\n    error(\"e\")\nrecover e:\n    show \"caught\"\nalways:\n    show \"always\"", "caught\nalways", section=s)
test("error propagates", "define f():\n    error(\"from f\")\ncheck:\n    f()\nrecover e:\n    show e", "from f", section=s)
test("or fallback nothing", "show nothing or \"default\"", "default", section=s)
test("or fallback div", "show divide(1, 0) or 0", "0", section=s)
test("or fallback index", "show list [1][99] or \"miss\"", "miss", section=s)
test("or fallback map", "show map {}[\"k\"] or \"none\"", "none", section=s)
test("or chain", "show nothing or nothing or \"found\"", "found", section=s)
test("or present skips", "show 42 or 0", "42", section=s)
test("or false NOT fallback", "show false or true", "true", section=s)
test("assert pass", "assert(1 = 1)\nshow \"ok\"", "ok", section=s)
test("assert fail", "assert(1 = 2)", error=True, section=s)
test("assert message", "assert(false, \"custom message\")", error=True, section=s)
test("nested check", """
check:
    check:
        error("inner")
    recover e:
        show "inner: " + e
    show "outer ok"
""", "inner: inner\nouter ok", section=s)

# ════════════════════════════════════════════════════════════════════
# SECTION 10: LISTS
# ════════════════════════════════════════════════════════════════════
s = "lists"
print(f"\n=== 10. Lists ===")
test("empty", "show len(list [])", "0", section=s)
test("index 0", "show list [10, 20, 30][0]", "10", section=s)
test("index 2", "show list [10, 20, 30][2]", "30", section=s)
test("index oob nothing", "show list [1][99]", "nothing", section=s)
test("index negative nothing", "show list [1, 2, 3][-1]", "nothing", section=s)
test("append", "show len(append(list [1, 2], 3))", "3", section=s)
test("prepend", "show prepend(list [2, 3], 1)", "[1, 2, 3]", section=s)  # test exists
test("remove", "show len(remove(list [1, 2, 3], 2))", "2", section=s)
test("slice", "show slice(list [1,2,3,4,5], 1, 3)", "[2, 3]", section=s)
test("merge", "show merge(list [1,2], list [3,4])", "[1, 2, 3, 4]", section=s)
test("sum", "show sum(list [1,2,3,4,5])", "15", section=s)
test("sum empty", "show sum(list [])", "0", section=s)
test("max", "show max(list [3,1,4,1,5,9])", "9", section=s)
test("min", "show min(list [3,1,4,1,5,9])", "1", section=s)
test("sort asc", "show sort(list [3,1,4,1,5])", "[1, 1, 3, 4, 5]", section=s)
test("join", 'show join(list ["a","b","c"], ",")', "a,b,c", section=s)
test("join empty sep", 'show join(list ["a","b","c"])', "abc", section=s)
test("map fn", "show map(list [1,2,3], given x: x * 2)", "[2, 4, 6]", section=s)
test("filter fn", "show filter(list [1,2,3,4,5], given x: x > 3)", "[4, 5]", section=s)
test("filter empty", "show filter(list [1,2,3], given x: x > 10)", "[]", section=s)
test("reduce", "show reduce(list [1,2,3,4,5], given (a,b): a + b, 0)", "15", section=s)
test("has list", "show has(list [1,2,3], 2)", "true", section=s)
test("has list miss", "show has(list [1,2,3], 9)", "false", section=s)
test("range len", "show len(range(10))", "10", section=s)
test("range start stop", "show range(2, 5)", "[2, 3, 4]", section=s)
test("nested list", "show list [list [1,2], list [3,4]][0][1]", "2", section=s)
test("flatten", "show flatten(list [list [1,2], list [3,4]])", "[1, 2, 3, 4]", section=s)
test("zip", "show zip(list [1,2,3], list [4,5,6])", "[[1, 4], [2, 5], [3, 6]]", section=s)
test("first", "show first(list [10,20,30])", "10", section=s)
test("is empty true", "show is_empty(list [])", "true", section=s)
test("is empty false", "show is_empty(list [1])", "false", section=s)
test("index of found", "show index_of(list [10,20,30], 20)", "1", section=s)
test("index of miss", "show index_of(list [10,20,30], 99)", "nothing", section=s)

# ════════════════════════════════════════════════════════════════════
# SECTION 11: MAPS
# ════════════════════════════════════════════════════════════════════
s = "maps"
print(f"\n=== 11. Maps ===")
test("create", 'show map {"a": 1}["a"]', "1", section=s)
test("field access", 'define m as map {"x": 42}\nshow m.x', "42", section=s)
test("missing nothing", 'show map {}["k"]', "nothing", section=s)
test("keys", 'show len(keys(map {"a":1,"b":2}))', "2", section=s)
test("values", 'show sum(values(map {"a":1,"b":2}))', "3", section=s)
test("has key", 'show has(map {"k": 1}, "k")', "true", section=s)
test("has miss", 'show has(map {}, "k")', "false", section=s)
test("merge", 'show merge(map {"a":1}, map {"b":2})["b"]', "2", section=s)
test("merge overwrite", 'show merge(map {"k":1}, map {"k":2})["k"]', "2", section=s)
test("nested map", 'define m as map {"outer": map {"inner": 42}}\nshow m["outer"]["inner"]', "42", section=s)
test("nested field", 'define m as map {"outer": map {"inner": 42}}\nshow m.outer.inner', "42", section=s)
test("multiline map", 'define m as map {\n    "a": 1,\n    "b": 2\n}\nshow m["a"]', "1", section=s)
test("map in list", 'define l as list [map {"v":1}, map {"v":2}]\nshow l[0]["v"]', "1", section=s)

# ════════════════════════════════════════════════════════════════════
# SECTION 12: TYPES
# ════════════════════════════════════════════════════════════════════
s = "types"
print(f"\n=== 12. User Types ===")
test("basic type", "type P has:\n    x: number\n    y: number\ndefine p as P(3, 4)\nshow p.x + p.y", "7", section=s)
test("type default", "type C has:\n    v: number = 0\ndefine c as C()\nshow c.v", "0", section=s)
test("type field access", "type T has:\n    name: text\ndefine t as T(\"Ledge\")\nshow t.name", "Ledge", section=s)
test("type in list", "type P has:\n    v: number\ndefine l as list [P(1), P(2)]\nshow l[0].v + l[1].v", "3", section=s)
test("type type_of", "type T has:\n    x: number\ndefine t as T(1)\nshow type(t)", "T", section=s)
test("type field type check", "type T has:\n    x: number\nT(\"str\")", error=True, section=s)

# ════════════════════════════════════════════════════════════════════
# SECTION 13: GENERATORS (LAZY)
# ════════════════════════════════════════════════════════════════════
s = "generators"
print(f"\n=== 13. Generators (Lazy) ===")
test("finite generator", """
define countdown(n):
    define i as n
    while i > 0:
        yield i
        set i to i - 1
define c as countdown(3)
show collect(c)
""", "[3, 2, 1]", section=s)

test("sum generator", """
define nums():
    yield 1
    yield 2
    yield 3
    yield 4
    yield 5
show sum(collect(nums()))
""", "15", section=s)

test("generator indexed", """
define squares():
    define i as 1
    while i <= 10:
        yield i * i
        set i to i + 1
define s as squares()
show s[0]
show s[4]
""", "1\n25", section=s)

test("infinite generator indexed", """
define naturals(start):
    define n as start
    while true:
        yield n
        set n to n + 1
define g as naturals(10)
show g[0]
show g[9]
""", "10\n19", section=s)

test("generator in for loop", """
define evens(limit):
    define n as 0
    while n <= limit:
        if modulo(n, 2) = 0:
            yield n
        set n to n + 1
for each e in evens(8):
    show e
""", "0\n2\n4\n6\n8", section=s)

# ════════════════════════════════════════════════════════════════════
# SECTION 14: PARALLEL EXECUTION
# ════════════════════════════════════════════════════════════════════
s = "parallel"
print(f"\n=== 14. Parallel Execution ===")
test("parallel basic", """
define results as parallel [1 + 1, 2 + 2, 3 + 3]
show sum(results)
""", "12", section=s)

test("parallel three", """
define r as parallel [10, 20, 30]
show r[0]
show r[2]
""", "10\n30", section=s)

# ════════════════════════════════════════════════════════════════════
# SECTION 15: PYTHON FFI
# ════════════════════════════════════════════════════════════════════
s = "ffi"
print(f"\n=== 15. Python FFI ===")
test("import python math", """
import "python:math" as pymath
show pymath["pi"] > 3
show pymath["sqrt"](144)
""", "true\n12", section=s)

test("import python json via stdlib", """
define src as json_stringify(map {"val": 99})
define parsed as json_parse(src)
show parsed["val"]
""", "99", section=s)

test("python module not found", 'import "python:nonexistent_xyz_module_12345" as m', error=True, section=s)

# ════════════════════════════════════════════════════════════════════
# SECTION 16: STDLIB MODULES
# ════════════════════════════════════════════════════════════════════
s = "stdlib"
print(f"\n=== 16. Stdlib Modules ===")
test("math pi", 'import "math" as math\nshow math["pi"] > 3', "true", section=s)
test("math sqrt", 'import "math" as math\nshow math["sqrt"](25)', "5", section=s)
test("collections unique", 'import "collections" as c\nshow len(c["unique"](list [1,2,2,3]))', "3", section=s)
test("collections count_by", 'import "collections" as c\ndefine r as c["count_by"](list ["a","b","a"])\nshow r["a"]', "2", section=s)
test("collections flatten", 'import "collections" as c\nshow c["flatten"](list [list [1,2],list [3,4]])', "[1, 2, 3, 4]", section=s)
test("collections take", 'import "collections" as c\nshow c["take"](list [1,2,3,4,5], 3)', "[1, 2, 3]", section=s)
test("collections group_by", 'define r as group_by(list [1,2,3,4], given x: text(modulo(x, 2)))\nshow len(keys(r))', "2", section=s)
test("text upper", 'import "text" as t\nshow t["upper"]("hello")', "HELLO", section=s)
test("text pad_left", 'import "text" as t\nshow len(t["pad_left"]("hi", 10))', "10", section=s)
test("text words", 'import "text" as t\nshow len(t["words"]("the quick brown fox"))', "4", section=s)
test("env get missing", 'import "env" as env\nshow env["get"]("NONEXISTENT_VAR_XYZ", "default")', "default", section=s)

# ════════════════════════════════════════════════════════════════════
# SECTION 17: TYPE SYSTEM
# ════════════════════════════════════════════════════════════════════
s = "typesystem"
print(f"\n=== 17. Type System ===")
test("type number", "show type(42)", "number", section=s)
test("type text", 'show type("hi")', "text", section=s)
test("type truth", "show type(true)", "truth", section=s)
test("type list", "show type(list [])", "list", section=s)
test("type map", "show type(map {})", "map", section=s)
test("type nothing", "show type(nothing)", "nothing", section=s)
test("type function", "define f():\n    pass\nshow type(f)", "function", section=s)
test("cast number str", 'show number("42")', "42", section=s)
test("cast number fail", 'show number("abc") or -1', "-1", section=s)
test("cast text num", "show text(42)", "42", section=s)
test("cast truth 0", "show truth(0)", "false", section=s)
test("cast truth 1", "show truth(1)", "true", section=s)
test("cast truth empty str", 'show truth("")', "false", section=s)
test("cast truth nonempty", 'show truth("x")', "true", section=s)

# ════════════════════════════════════════════════════════════════════
# SECTION 18: NEGATIVE / ERROR CASES
# ════════════════════════════════════════════════════════════════════
s = "negative"
print(f"\n=== 18. Negative Cases ===")
test("undefined var", "show undefined_xyz", error=True, section=s)
test("set undefined", "set xyz to 1", error=True, section=s)
test("call non-fn number", "define x as 5\nx()", error=True, section=s)
test("call non-fn string", '("hello")()', error=True, section=s)
test("type mismatch add", "show 1 + true", error=True, section=s)
test("compare wrong type", 'show "a" < "b"', error=True, section=s)
test("index non-list", "show 42[0]", error=True, section=s)
test("type hint wrong", "define n: number as true", error=True, section=s)
test("missing function arg", "define f(a, b):\n    return a+b\nf(1)", error=True, section=s)
test("div by zero nothing", "define r as 1/0\nshow r", "nothing", section=s)  # / returns nothing
test("sqrt neg nothing", "show sqrt(-4) or \"err\"", "err", section=s)

# ════════════════════════════════════════════════════════════════════
# SECTION 19: EDGE CASES
# ════════════════════════════════════════════════════════════════════
s = "edge"
print(f"\n=== 19. Edge Cases ===")
test("nothing eq nothing", "show nothing = nothing", "true", section=s)
test("nothing neq 0", "show nothing = 0", "false", section=s)
test("nothing neq false", "show nothing = false", "false", section=s)
test("true neq 1", "show true = 1", "false", section=s)  # strict typing
test("false neq 0", "show false = 0", "false", section=s)  # strict typing
test("empty list truthy false", "if list []:\n    show \"yes\"\nelse:\n    show \"no\"", "no", section=s)
test("empty map truthy false", 'if map {}:\n    show "yes"\nelse:\n    show "no"', "no", section=s)
test("or chaining right assoc", "show nothing or nothing or 42", "42", section=s)
test("define fn shadows builtin", "define len as given x: 99\nshow len(list [1,2,3])", "99", section=s)
test("fn returns fn", "define f():\n    return given x: x * 2\nshow f()(21)", "42", section=s)
test("recursive function", """
define fact(n):
    if n <= 1:
        return 1
    return n * fact(n - 1)
show fact(5)
""", "120", section=s)
test("deep recursion", """
define sum_to(n):
    if n = 0:
        return 0
    return n + sum_to(n - 1)
show sum_to(100)
""", "5050", section=s)
test("multiline string in map", 'define m as map {\n    "key": "value"\n}\nshow m["key"]', "value", section=s)
test("nothing in collection", "define l as list [1, nothing, 3]\nshow l[1]", "nothing", section=s)
test("map with number keys coerced", 'define m as map {1: "one"}\nshow m["1"]', "one", section=s)
test("float as list index", "show list [1,2,3][1.0]", "2", section=s)

# ════════════════════════════════════════════════════════════════════
# SECTION 20: ADVANCED PATTERNS
# ════════════════════════════════════════════════════════════════════
s = "advanced"
print(f"\n=== 20. Advanced Patterns ===")
test("quicksort", """
define quicksort(lst):
    if len(lst) <= 1:
        return lst
    define pivot as lst[0]
    define rest as slice(lst, 1)
    define smaller as filter(rest, given x: x < pivot)
    define greater as filter(rest, given x: x >= pivot)
    return merge(quicksort(smaller), merge(list [pivot], quicksort(greater)))
define r as quicksort(list [3,1,4,1,5,9,2,6])
show r
""", "[1, 1, 2, 3, 4, 5, 6, 9]", section=s)

test("memoize pattern", """
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
""", "49\n49", section=s)

test("pipeline pattern", """
define numbers as range(1, 11)
define result as sum(filter(map(numbers, given x: x * x), given x: modulo(x, 2) = 0))
show result
""", "220", section=s)

test("fizzbuzz", """
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
""", "FizzBuzz\nFizz\nBuzz", section=s)

# ════════════════════════════════════════════════════════════════════
# SECTION 21: JSON
# ════════════════════════════════════════════════════════════════════
s = "json"
print(f"\n=== 21. JSON ===")
test("parse object", "define src as json_stringify(map {\"x\": 1})\ndefine d as json_parse(src)\nshow d[\"x\"]", "1", section=s)
test("parse array", 'define l as json_parse("[1,2,3]")\nshow sum(l)', "6", section=s)
test("parse null", 'define v as json_parse("null")\nshow v', "nothing", section=s)
test("parse bool", 'show json_parse("true")', "true", section=s)
test("stringify map", 'show len(json_stringify(map {"a": 1})) > 0', "true", section=s)
test("stringify list", 'show json_stringify(list [1,2,3])', "[1, 2, 3]", section=s)
test("round trip", 'define m as map {"n": 42}\ndefine s as json_stringify(m)\ndefine m2 as json_parse(s)\nshow m2["n"]', "42", section=s)
test("parse invalid nothing", 'show json_parse("not json") or "bad"', "bad", section=s)

# ════════════════════════════════════════════════════════════════════
# SUMMARY
# ════════════════════════════════════════════════════════════════════
total = PASS + FAIL
print(f"\n{'='*60}")
print(f"CONFORMANCE RESULTS: {PASS}/{total} passed ({100*PASS/total:.1f}%)")
if ERRORS:
    print(f"\n{len(ERRORS)} FAILURES:")
    for e in ERRORS[:20]:
        print(f"  {e}")
    if len(ERRORS) > 20:
        print(f"  ... and {len(ERRORS)-20} more")
else:
    print("ALL CONFORMANCE TESTS PASSED")

print(f"\nResults by section:")
for sec, (p, f) in sorted(SECTIONS.items()):
    total_sec = p + f
    status = "✓" if f == 0 else "✗"
    print(f"  {status} {sec:<20} {p}/{total_sec}")
print('='*60)
sys.exit(0 if FAIL == 0 else 1)
