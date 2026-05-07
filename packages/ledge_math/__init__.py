"""
ledge_math — Math utilities for Ledge
======================================
Provides advanced mathematical operations beyond the stdlib.

Usage in Ledge:
    import "ledge:math" as m
    show m.matrix_mul([[1,2],[3,4]], [[5,6],[7,8]])
    show m.prime(97)
    show m.gcd(48, 18)
"""
from ledge_lang import run

LEDGE_PACKAGE = "ledge_math"
VERSION = "1.0.0"

# These functions are exposed as Ledge builtins when the package is imported
BUILTINS = {
    "prime": lambda n, *_: all(n % i != 0 for i in range(2, int(n**0.5)+1)) and n > 1,
    "gcd": lambda a, b, *_: a if b == 0 else BUILTINS["gcd"](b, a % b),
    "lcm": lambda a, b, *_: abs(a*b) // BUILTINS["gcd"](a, b) if a and b else 0,
    "is_even": lambda n, *_: int(n) % 2 == 0,
    "is_odd": lambda n, *_: int(n) % 2 != 0,
    "clamp": lambda val, lo, hi, *_: max(lo, min(hi, val)),
    "lerp": lambda a, b, t, *_: a + (b - a) * t,
}

EXAMPLES = """
# Check if a number is prime
import "python:ledge_math" as m
show m["prime"](97)   # true
show m["prime"](100)  # false
show m["gcd"](48, 18) # 6
"""


# Direct function exports (accessible as m["prime"])
def prime(n):
    """Check if n is prime."""
    n = int(n)
    if n < 2: return False
    return all(n % i != 0 for i in range(2, int(n**0.5)+1))

def gcd(a, b):
    """Greatest common divisor."""
    a, b = int(a), int(b)
    while b: a, b = b, a % b
    return a

def lcm(a, b):
    """Least common multiple."""
    return abs(int(a)*int(b)) // gcd(a, b) if a and b else 0

def is_even(n): return int(n) % 2 == 0
def is_odd(n): return int(n) % 2 != 0
def clamp(val, lo, hi): return max(lo, min(hi, val))
def lerp(a, b, t): return a + (b - a) * t
def factorial(n): return 1 if int(n) <= 1 else int(n) * factorial(int(n)-1)
def power(base, exp): return base ** exp
def log2(n): import math; return math.log2(n)
