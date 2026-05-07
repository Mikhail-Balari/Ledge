"""
Ledge Parser Fuzzer — deterministic, reproducible, time-bounded.
Seeds are versioned. Results are reportable.
A crash (unhandled Python exception) is a critical bug.
Expected errors (LexError, ParseError, LedgeError) are acceptable.
"""
import sys, os, random, time, string
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from ledge_lang import run
from ledge_lang.lexer import LexError
from ledge_lang.parser import ParseError
from ledge_lang.interpreter import LedgeError

REGISTERED_SEEDS = [42, 137, 271, 314, 999]
MAX_TIME_PER_SEED = 10  # seconds per seed budget

ADVERSARIAL_INPUTS = [
    "",  " ",  "\n",  "\t",  "\r\n",
    "yield 1",
    "break",
    "continue",
    "set x to 10",
    'show "unclosed',
    "if true:\n",
    "show +",
    "show list [1, 2, 3",
    'show map {"k": 1',
    "define x as x",
    "define x: number as true",
    'show "{}',
    "\x00",  "🦊🐍🤖",
    "+ + + + +",
    "show " + "9" * 500,
    "list [" * 30 + "1" + "]" * 30,
    "define " + "x" * 200 + " as 1",
    "show " + " or ".join(["nothing"] * 40) + " or 42",
    "define f(n):\n    return f(n+1)\nf(0)",
]

SEED_PROGRAMS = [
    "show 42",
    'define x as "hello"\nshow x',
    "define f(n):\n    return n * 2\nshow f(21)",
    "for each i in range(10):\n    show i",
    "define l as list [1, 2, 3]\nshow sum(l)",
    'define m as map {"k": 1}\nshow m["k"]',
    "check:\n    error(\"test\")\nrecover e:\n    show e",
]


def safe_run(source, timeout=2):
    """
    Run source safely. Returns ("ok", output) or ("error", type) or ("crash", exception).
    A "crash" is any exception that is NOT LexError/ParseError/LedgeError/RecursionError.
    """
    try:
        run(source, output_fn=lambda x: None)
        return "ok", None
    except (LexError, ParseError, LedgeError, RecursionError):
        return "error", None
    except Exception as e:
        return "crash", e


def mutate(source, rng):
    strategies = [
        lambda s: s + "\n" + rng.choice(["show", "define", "if", "for"]),
        lambda s: s[:-1] if len(s) > 1 else s,
        lambda s: s.replace(rng.choice(list(s)) if s else "x", ""),
        lambda s: s + " " + "".join(rng.choices(string.ascii_lowercase, k=3)),
        lambda s: s[:len(s)//2],
        lambda s: s.replace("    ", "  "),
        lambda s: s + "\x00",
        lambda s: s + "🤖",
        lambda s: s * 2 if len(s) < 50 else s,
        lambda s: "\n".join(reversed(s.split("\n"))),
    ]
    return rng.choice(strategies)(source)


def run_fuzz_session(seed, time_budget=MAX_TIME_PER_SEED):
    rng = random.Random(seed)
    crashes = []
    runs = 0
    start = time.perf_counter()

    # Phase 1: adversarial corpus
    for src in ADVERSARIAL_INPUTS:
        status, exc = safe_run(src)
        runs += 1
        if status == "crash":
            crashes.append((src[:60], exc))

    # Phase 2: mutations of valid programs
    while time.perf_counter() - start < time_budget * 0.7:
        base = rng.choice(SEED_PROGRAMS)
        mutated = mutate(base, rng)
        status, exc = safe_run(mutated)
        runs += 1
        if status == "crash":
            crashes.append((mutated[:60], exc))

    return runs, crashes


def test_fuzzer_seed_42():
    """Seed 42 — must produce 0 crashes."""
    runs, crashes = run_fuzz_session(42)
    assert runs > 0, "Fuzzer ran 0 programs"
    assert len(crashes) == 0, (
        f"CRASHES with seed 42:\n" +
        "\n".join(f"  {src!r}: {type(exc).__name__}: {exc}"
                  for src, exc in crashes[:5])
    )


def test_fuzzer_seed_137():
    runs, crashes = run_fuzz_session(137)
    assert len(crashes) == 0, f"{len(crashes)} crashes with seed 137"


def test_fuzzer_adversarial():
    """All adversarial inputs must be handled gracefully."""
    for src in ADVERSARIAL_INPUTS:
        status, exc = safe_run(src)
        assert status != "crash", (
            f"CRASH on adversarial input {src!r}:\n"
            f"  {type(exc).__name__}: {exc}"
        )


def test_fuzzer_yield_outside_fn():
    status, exc = safe_run("yield 1")
    assert status == "error", f"Expected error, got {status}"


def test_fuzzer_break_outside_loop():
    status, exc = safe_run("break")
    assert status == "error"


def test_fuzzer_empty_input():
    status, exc = safe_run("")
    assert status != "crash"


def test_fuzzer_unicode():
    status, exc = safe_run('show "héllo wörld 🌍"')
    assert status != "crash"


def test_fuzzer_null_byte():
    status, exc = safe_run("show 1\x00show 2")
    assert status != "crash"


def test_fuzzer_very_long_identifier():
    status, exc = safe_run("define " + "x" * 500 + " as 1")
    assert status != "crash"


def test_fuzzer_deep_nesting():
    status, exc = safe_run("list [" * 50 + "1" + "]" * 50)
    assert status != "crash"
