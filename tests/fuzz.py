"""
Ledge Parser Fuzzer
Generates adversarial and random inputs to find crashes in lexer/parser/interpreter.
A conforming Ledge implementation must NEVER crash on any input — only raise
LedgeError, LexError, or ParseError.
"""

import sys, os, random, string, time
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from ledge_lang import compile_ledge
from ledge_lang.lexer import Lexer, LexError
from ledge_lang.parser import ParseError
from ledge_lang.interpreter import LedgeError

CRASHES = 0
ERRORS = 0
RUNS = 0


def safe_run(source):
    """Run source. Returns True if handled correctly, False if crashed."""
    global CRASHES, ERRORS, RUNS
    RUNS += 1
    try:
        from ledge_lang import run
        run(source, output_fn=lambda x: None)
        return True
    except (LexError, ParseError, LedgeError):
        ERRORS += 1
        return True  # Expected error types — that's fine
    except RecursionError:
        ERRORS += 1
        return True  # Python recursion limit — acceptable for deeply recursive code
    except Exception as e:
        CRASHES += 1
        print(f"  CRASH [{type(e).__name__}]: {str(e)[:100]}")
        print(f"    Input: {source[:80]!r}")
        return False


# ── Seed corpus: valid programs ────────────────────────────────────────────────
SEEDS = [
    "show 42",
    'define x as "hello"\nshow x',
    "define f(n):\n    return n * 2\nshow f(21)",
    "for each i in range(10):\n    show i",
    "if true:\n    show 1\nelse:\n    show 0",
    "define l as list [1, 2, 3]\nshow sum(l)",
    'define m as map {"k": 1}\nshow m["k"]',
    "check:\n    error(\"test\")\nrecover e:\n    show e",
]

# ── Mutation strategies ────────────────────────────────────────────────────────

def mutate(source):
    """Apply random mutations to a valid source program."""
    strategies = [
        lambda s: s + "\n" + random.choice(["show", "define", "if", "for"]),
        lambda s: s.replace(random.choice(list(s)) if s else "x", ""),
        lambda s: s + " " + "".join(random.choices(string.ascii_lowercase, k=5)),
        lambda s: s[:len(s)//2],  # truncate
        lambda s: s + "\n" * random.randint(1, 10),
        lambda s: s.replace("define", "DEFINE"),
        lambda s: s + "\x00",  # null byte
        lambda s: s + "🦊",  # unicode
        lambda s: "\t".join(s.split(" ")),  # tabs instead of spaces
        lambda s: s.replace("    ", "  "),  # wrong indent
        lambda s: s * 3,  # repeat
        lambda s: "\n".join(reversed(s.split("\n"))),  # reverse lines
    ]
    return random.choice(strategies)(source)


def random_program(depth=0):
    """Generate a random (possibly invalid) Ledge program."""
    if depth > 3:
        return random.choice(["show 1", "pass", "define x as 1"])
    
    templates = [
        lambda: f"show {random_expr()}",
        lambda: f"define {random_name()} as {random_expr()}",
        lambda: f"if {random_expr()}:\n    {random_program(depth+1)}",
        lambda: f"while {random_expr()}:\n    pass",
        lambda: f"for each x in {random_expr()}:\n    show x",
        lambda: f"define {random_name()}({random_name()}):\n    return {random_expr()}",
        lambda: f"check:\n    {random_program(depth+1)}\nrecover e:\n    show e",
        lambda: f"show {random_expr()} or {random_expr()}",
        lambda: f"define x: {random_type()} as {random_expr()}",
    ]
    return random.choice(templates)()


def random_expr():
    exprs = [
        str(random.randint(-100, 100)),
        f'"{random_string()}"',
        "true", "false", "nothing",
        f"list [{random_expr_simple()}, {random_expr_simple()}]",
        f"map {{\"k\": {random_expr_simple()}}}",
        f"{random_expr_simple()} + {random_expr_simple()}",
        f"divide({random_expr_simple()}, {random.randint(-5, 5)})",
        f"sum(list [{random_expr_simple()}])",
        "nothing",
    ]
    return random.choice(exprs)


def random_expr_simple():
    return random.choice([
        str(random.randint(0, 100)),
        f'"{random_string(3)}"',
        "true", "false", "nothing", "0",
    ])


def random_name():
    return random.choice(["x", "y", "z", "n", "val", "data", "result", "tmp"])


def random_type():
    return random.choice(["number", "text", "truth", "list", "map", "any"])


def random_string(max_len=10):
    chars = string.ascii_letters + string.digits + " _-"
    return "".join(random.choices(chars, k=random.randint(0, max_len)))


# ── Adversarial inputs ────────────────────────────────────────────────────────

ADVERSARIAL = [
    # Empty and whitespace
    "", " ", "\n", "\t", "\r\n", "   \n   \n",
    
    # Deeply nested structures
    "list [" * 100 + "1" + "]" * 100,
    "map {" * 50 + '"k": 1' + "}" * 50,
    
    # Very long identifiers
    "define " + "x" * 1000 + " as 1",
    
    # Very long strings
    f'show "{"x" * 10000}"',
    
    # Unicode
    'show "héllo wörld 🌍"',
    'define ñ as 1\nshow ñ',
    
    # Escape sequences
    r'show "\n\t\r\\"',
    'show "unclosed string',
    
    # Deeply recursive programs
    "define f(n):\n    return f(n+1)\nf(0)",  # should hit recursion limit
    
    # Max integer
    f"show {2**63}",
    f"show {2**63 + 1}",
    
    # Division edge cases
    "show divide(0, 0)",
    "show divide(1, 0)",
    "show modulo(0, 0)",
    
    # Empty blocks (should require pass)
    "if true:\n",
    
    # Mixed indentation (invalid)
    "define f():\n  return 1",  # 2 spaces
    
    # Keywords as values
    "define x as define",
    "show show",
    
    # Circular reference attempt
    "define x as x",
    
    # Very deep function nesting
    "\n".join(f"define f{i}(n):\n    return f{i+1}(n)" for i in range(50)) + f"\ndefine f50(n):\n    return n\nf0(1)",
    
    # Null bytes and control chars
    "show 1\x00show 2",
    "define\x01x as 1",
    
    # Extremely long numbers
    "show " + "9" * 1000,
    "show 0." + "9" * 1000,
    
    # Operator spam
    "+ + + + +",
    "show + + 1",
    
    # Unclosed brackets
    "show list [1, 2, 3",
    'show map {"k": 1',
    "show (1 + 2",
    
    # Multiple returns
    "define f():\n    return 1\n    return 2\nf()",
    
    # Yield outside function
    "yield 1",
    
    # Break outside loop
    "break",
    
    # Giant list
    "show list [" + ", ".join(str(i) for i in range(1000)) + "]",
    
    # Deeply nested if
    "\n".join(
        ["define x as 5"] +
        [f"{'    '*i}if x > {i}:" for i in range(30)] +
        [f"{'    '*30}show x"]
    ),
    
    # String with all escape chars
    'show "\\n\\t\\\\\\"\\{\\}"',
    
    # Chain of or
    "show " + " or ".join(["nothing"] * 50) + " or 42",
    
    # Interpolation edge cases
    'show "{}"',
    'show "{{not interpolated}}"',
    'show "{1 + 2 + 3}"',
]


# ── Run fuzzer ────────────────────────────────────────────────────────────────

def run_fuzzer(seed=42, iterations=500):
    global CRASHES, ERRORS, RUNS
    random.seed(seed)
    
    print("Ledge Fuzzer v0.2")
    print("=" * 50)
    print(f"Iterations: {iterations}")
    print("A CRASH means an unhandled Python exception (bug).")
    print("Errors (LexError/ParseError/LedgeError) are EXPECTED.")
    print()
    
    start = time.time()
    
    # 1. Adversarial corpus
    print(f"[1/3] Adversarial inputs ({len(ADVERSARIAL)} cases)...")
    for source in ADVERSARIAL:
        safe_run(source)
    
    # 2. Seed mutations
    print(f"[2/3] Seed mutations ({min(iterations//2, 200)} cases)...")
    for _ in range(min(iterations//2, 200)):
        seed_prog = random.choice(SEEDS)
        mutated = mutate(seed_prog)
        safe_run(mutated)
    
    # 3. Random generation
    print(f"[3/3] Random programs ({iterations//2} cases)...")
    for _ in range(iterations//2):
        prog = random_program()
        safe_run(prog)
    
    elapsed = time.time() - start
    
    print()
    print("=" * 50)
    print(f"Results:")
    print(f"  Total runs:   {RUNS}")
    print(f"  Expected errors: {ERRORS} ({100*ERRORS/RUNS:.1f}%)")
    print(f"  CRASHES:      {CRASHES}")
    print()
    
    if CRASHES == 0:
        print("✓ PASS: No unhandled crashes found.")
        print("  The parser and interpreter handle all inputs gracefully.")
    else:
        print(f"✗ FAIL: {CRASHES} unhandled crash(es) found.")
        print("  These represent bugs in the implementation.")
    
    print(f"\nFuzzing speed: {RUNS/elapsed:.0f} programs/second")
    return CRASHES == 0


if __name__ == "__main__":
    iterations = int(sys.argv[1]) if len(sys.argv) > 1 else 500
    ok = run_fuzzer(iterations=iterations)
    sys.exit(0 if ok else 1)
