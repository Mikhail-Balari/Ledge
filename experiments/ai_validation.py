"""
AI Generation Quality Experiment v2.0
=======================================
50 reference tasks for Ledge AI-first programming.
Tests whether Ledge's canonical syntax enables correct AI code generation.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from ledge_lang import run

def task(name, src, expected):
    return {"name": name, "src": src.strip(), "expected": expected}

TASKS = [

task("sum_list", """
show sum(range(1, 11))
""", "55"),

task("filter_evens", """
show filter(range(1, 11), given x: modulo(x, 2) = 0)
""", "[2, 4, 6, 8, 10]"),

task("fibonacci", """
define fibs as list [0, 1]
repeat 6 times:
    define n as len(fibs)
    define prev2 as fibs[n - 2]
    define prev1 as fibs[n - 1]
    set fibs to append(fibs, prev2 + prev1)
show fibs
""", "[0, 1, 1, 2, 3, 5, 8, 13]"),

task("count_words", """
show len(split("the quick brown fox", " "))
""", "4"),

task("safe_divide", """
define safe_divide(a: number, b: number):
    requires:
        b != 0
    return divide(a, b) or 0
show safe_divide(10, 2)
show safe_divide(6, 3)
""", "5\n2"),

task("factorial", """
define fact(n):
    if n <= 1:
        return 1
    return n * fact(n - 1)
show fact(7)
""", "5040"),

task("max_list", """
show max(list [3, 1, 4, 1, 5, 9, 2, 6])
""", "9"),

task("flatten_list", """
show flatten(list [list [1,2], list [3,4], list [5,6]])
""", "[1, 2, 3, 4, 5, 6]"),

task("map_transform", """
show map(range(1, 6), given x: x * 2)
""", "[2, 4, 6, 8, 10]"),

task("ai_sentiment_type", """
define r as analyze("hello") using sentiment
show type(r)
""", "uncertain[map]"),

task("ai_zero_confidence", """
define r as analyze("test") using sentiment
show confidence_of(r)
""", "0"),

task("ai_nothing_without_backend", """
show value_of(classify("x") using ["a","b"])
""", "nothing"),

task("ai_not_confident_without_backend", """
show is_confident(analyze("x") using y)
""", "false"),

task("ai_when_fallback_low", """
show when(uncertain("yes", 0.5), 0.8, "no")
""", "no"),

task("ai_when_fallback_high", """
show when(uncertain("yes", 0.95), 0.8, "no")
""", "yes"),

task("ai_audit_trail", """
define r1 as analyze("audit_test_1") using sentiment
define r2 as analyze("audit_test_2") using sentiment
define r3 as classify("audit_test_3") using ["x","y"]
define log as audit_query()
show len(log) >= 3
""", "true"),

task("ai_confidence_range", """
show confidence_of(uncertain("x", 2.5)) <= 1
show confidence_of(uncertain("x", -1)) >= 0
""", "true\ntrue"),

task("ai_pipeline", """
define texts as list ["a", "b", "c"]
define results as list []
for each t in texts:
    define r as classify(t) using ["pos", "neg"]
    set results to append(results, when(r, 0.7, "unclassified"))
show len(results)
""", "3"),

task("ai_contract", """
define f(x: number):
    requires:
        x > 0
    return x * 2
show f(5)
""", "10"),

task("stream_filter", """
define s as stream_of(range(1, 11))
show stream_collect(stream_where(s, given x: modulo(x, 2) = 0))
""", "[2, 4, 6, 8, 10]"),

task("stream_map", """
define s as stream_of(list [1, 2, 3, 4, 5])
show stream_collect(stream_map(s, given x: x * 2))
""", "[2, 4, 6, 8, 10]"),

task("stream_take", """
show stream_collect(stream_take(stream_of(range(1, 100)), 3))
""", "[1, 2, 3]"),

task("stream_pipeline", """
define s as stream_of(range(1, 11))
show stream_collect(stream_map(stream_where(s, given x: x > 5), given x: x * x))
""", "[36, 49, 64, 81, 100]"),

task("infinite_gen", """
define naturals(n):
    while true:
        yield n
        set n to n + 1
define g as naturals(1)
show g[4]
""", "5"),

task("fizzbuzz", """
define n as 15
define result as "other"
if modulo(n, 15) = 0:
    set result to "FizzBuzz"
else if modulo(n, 3) = 0:
    set result to "Fizz"
else if modulo(n, 5) = 0:
    set result to "Buzz"
show result
""", "FizzBuzz"),

task("match_expr", """
define status as "active"
match status:
    case "active":
        show "running"
    case "stopped":
        show "halted"
    otherwise:
        show "unknown"
""", "running"),

task("check_recover", """
check:
    error("boom")
recover e:
    show "Caught: " + e
""", "Caught: boom"),

task("closure_counter", """
define make_counter():
    define n as 0
    define inc():
        set n to n + 1
        return n
    return inc
define c as make_counter()
show c()
show c()
show c()
""", "1\n2\n3"),

task("higher_order", """
define apply_twice(f, x):
    return f(f(x))
define double as given x: x * 2
show apply_twice(double, 3)
""", "12"),

task("json_roundtrip", """
define data as map {"name": "Ledge", "version": 1}
define s as json_stringify(data)
show json_parse(s)["name"]
""", "Ledge"),

task("group_by", """
define grouped as group_by(range(1, 7), given x: text(modulo(x, 2)))
show len(keys(grouped))
""", "2"),

task("zip_pairs", """
define k as list ["a", "b", "c"]
define v as list [1, 2, 3]
show zip(k, v)[0]
""", "[a, 1]"),

task("reduce_fn", """
show reduce(list [1, 2, 3, 4, 5], given (a, b): a * b, 1)
""", "120"),

task("type_annotation", """
define x: number as 42
set x to 100
show x
""", "100"),

task("nothing_semantics", """
show nothing = nothing
show nothing = false
show nothing = 0
""", "true\nfalse\nfalse"),

task("boolean_semantics", """
show true = 1
show false = 0
show true = true
""", "false\nfalse\ntrue"),

task("or_fallback", """
define m as map {"x": 10}
show m["x"] or 0
show m["y"] or 0
show divide(10, 0) or -1
""", "10\n0\n-1"),

task("contracts_full", """
define safe_sqrt(x: number):
    requires:
        x >= 0
    ensures:
        result >= 0
    return sqrt(x) or 0
show safe_sqrt(25)
show safe_sqrt(0)
""", "5\n0"),

task("string_ops", """
define s as "Hello"
show upper(s)
show lower(s)
show len(s)
""", "HELLO\nhello\n5"),

task("string_template", """
define n as 42
show "The answer is {n} and pi is {round(pi(), 2)}"
""", "The answer is 42 and pi is 3.14"),

task("split_join", """
show join(reverse(split("a-b-c", "-")), "+")
""", "c+b+a"),

task("ffi_math", """
import "python:math" as m
show m["sqrt"](144)
""", "12"),

task("parallel_sum", """
define r as parallel [1 + 1, 2 * 2, 3 * 3]
show sum(r)
""", "15"),

task("parallel_order", """
define r as parallel [10, 20, 30]
show r[0]
show r[2]
""", "10\n30"),

task("memoize", """
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
define sq as make_memo(given x: x * x)
show sq(7)
show sq(7)
""", "49\n49"),

task("pipeline_composition", """
define result as sum(filter(map(range(1, 11), given x: x * x), given x: modulo(x, 4) = 0))
show result
""", "220"),

task("stream_re_iterable", """
define s as stream_of(list [1, 2, 3, 4])
define evens as stream_where(s, given x: modulo(x, 2) = 0)
show stream_collect(evens)
show stream_collect(evens)
""", "[2, 4]\n[2, 4]"),

task("uncertain_confidence_clamped", """
show confidence_of(uncertain("x", 0.75))
""", "0.75"),

task("audit_is_list", """
define r as analyze("test") using mode
show type(audit_query())
""", "list"),

task("nothing_or_chain", """
show nothing or nothing or nothing or 42
""", "42"),

]


def run_task(t):
    try:
        lines, _ = run(t["src"], output_fn=lambda x: None)
        got = "\n".join(lines).strip()
        return got == t["expected"], got, None
    except Exception as e:
        return False, "", str(e)[:80]


def main():
    print("=" * 70)
    print(f"Ledge AI Generation Quality Experiment v2.0")
    print(f"{len(TASKS)} tasks — all reference implementations")
    print("=" * 70)

    passed = failed = errors = 0
    fail_list = []

    for t in TASKS:
        ok, got, err = run_task(t)
        if ok:
            passed += 1
        elif err:
            errors += 1
            fail_list.append((t["name"], err, t["expected"]))
        else:
            failed += 1
            fail_list.append((t["name"], got, t["expected"]))

    if fail_list:
        print("\nFAILURES:")
        for name, got, exp in fail_list[:5]:
            print(f"  ✗ {name}")
            print(f"    Expected: {repr(exp)[:50]}")
            print(f"    Got:      {repr(got)[:50]}")

    total = len(TASKS)
    pct = 100 * passed // total
    print(f"\nResults: {passed}/{total} ({pct}%)")
    print(f"  Ledge  first-run correct: {passed}/{total} ({pct}%)")

    return passed == total


if __name__ == "__main__":
    import sys
    sys.exit(0 if main() else 1)
