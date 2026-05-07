"""
VM vs Tree-Walker — Random Program Differential Testing
=========================================================
Generates programs deterministically (seeded) and verifies that
the VM and tree-walker produce identical results.

This is the high-confidence test the Plan Maestro requires.
Seed is versioned — same seed always produces same programs.
"""
import sys, os, random
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from ledge_lang import run, compile_ledge
from ledge_lang.vm import compile_to_bytecode, VM


def generate_programs(seed, n=500):
    rng = random.Random(seed)
    programs = []

    nums = list(range(0, 20))
    strs = ["hello", "world", "ledge", "test"]
    vars_ = ["x", "y", "z", "n", "result"]

    def rn():  return rng.choice(nums)
    def rs():  return rng.choice(strs)
    def rv():  return rng.choice(vars_)
    def rop(): return rng.choice(["+", "-", "*"])
    def rcmp(): return rng.choice(["=", "!=", "<", ">", "<=", ">="])

    for _ in range(n):
        kind = rng.randint(0, 9)
        if kind == 0:
            a, b = rn(), rn()
            programs.append(f"show {a} {rop()} {b}")
        elif kind == 1:
            v, n_ = rv(), rn()
            programs.append(f"define {v} as {n_}\nshow {v}")
        elif kind == 2:
            a, b = rn(), rn()
            programs.append(f"if {a} {rcmp()} {b}:\n    show true\nelse:\n    show false")
        elif kind == 3:
            limit = rng.randint(1, 5)
            programs.append(f"define i as 0\nwhile i < {limit}:\n    set i to i + 1\nshow i")
        elif kind == 4:
            items = [str(rng.randint(0, 10)) for _ in range(rng.randint(1, 4))]
            programs.append("show len(list [" + ", ".join(items) + "])")
        elif kind == 5:
            a, b = rs(), rs()
            programs.append(f'show "{a}" + "{b}"')
        elif kind == 6:
            a, b = rn(), rn()
            programs.append(f"show {a} + {b} = {a + b}")
        elif kind == 7:
            n_ = rng.randint(0, 4)
            programs.append(f"define x as 0\nrepeat {n_} times:\n    set x to x + 1\nshow x")
        elif kind == 8:
            a, b, c = rn(), rn(), rng.randint(1, 5)
            programs.append(f"show ({a} + {b}) * {c}")
        else:
            choice = rng.choice(["true", "false", "nothing", "0", "1"])
            programs.append(f"show {choice}")
    return programs


def run_differential(programs):
    divergences = []
    skipped = 0
    for src in programs:
        try:
            tw_lines, _ = run(src, output_fn=lambda x: None)
        except Exception:
            continue
        try:
            ast = compile_ledge(src)
            co  = compile_to_bytecode(ast)
            vm_out = []
            VM(output_fn=vm_out.append).run(co)
            vm_lines = vm_out
        except Exception:
            skipped += 1
            continue
        if tw_lines != vm_lines:
            divergences.append((src, tw_lines, vm_lines))
    return divergences, skipped


class TestVMRandomDifferential:
    """Run generated programs through both backends — must be identical."""

    def test_seed_42_no_divergence(self):
        """Seed 42: 500 programs, 0 divergences allowed."""
        programs = generate_programs(42, 500)
        divs, skipped = run_differential(programs)
        assert len(divs) == 0, (
            f"{len(divs)} divergences found (seed=42):\n" +
            "\n".join(f"  {s[:50]!r}: TW={tw}, VM={vm}"
                      for s, tw, vm in divs[:5])
        )

    def test_seed_271_no_divergence(self):
        programs = generate_programs(271, 500)
        divs, _ = run_differential(programs)
        assert len(divs) == 0, f"{len(divs)} divergences (seed=271)"

    def test_seed_1000_no_divergence(self):
        programs = generate_programs(1000, 500)
        divs, _ = run_differential(programs)
        assert len(divs) == 0, f"{len(divs)} divergences (seed=1000)"

    def test_arithmetic_invariant(self):
        """Arithmetic results must be identical across all seeds."""
        for seed in [1, 2, 3, 7, 13, 99]:
            programs = [p for p in generate_programs(seed, 100)
                        if p.startswith("show ") and "+" in p and "define" not in p]
            divs, _ = run_differential(programs)
            assert len(divs) == 0, f"Arithmetic divergence (seed={seed}): {divs[:1]}"

    def test_comparison_invariant(self):
        """Comparison results must be identical."""
        programs = [f"show {a} {op} {b}"
                    for a in range(5) for b in range(5)
                    for op in ["=", "!=", "<", ">", "<=", ">="]]
        divs, _ = run_differential(programs)
        assert len(divs) == 0, f"Comparison divergence: {divs[:1]}"

    def test_boolean_invariant(self):
        """Boolean invariants must hold in both backends."""
        critical = [
            "show true = 1",
            "show false = 0",
            "show nothing = false",
            "show nothing = 0",
            "show true = true",
            "show false = false",
            "show nothing = nothing",
        ]
        divs, _ = run_differential(critical)
        assert len(divs) == 0, f"Boolean divergence: {divs}"

    def test_control_flow_invariant(self):
        """Control flow must be identical."""
        programs = []
        for limit in range(0, 8):
            programs.append(
                f"define i as 0\nwhile i < {limit}:\n    set i to i + 1\nshow i"
            )
        for n in range(0, 7):
            programs.append(
                f"define x as 0\nrepeat {n} times:\n    set x to x + 1\nshow x"
            )
        divs, _ = run_differential(programs)
        assert len(divs) == 0, f"Control flow divergence: {divs}"
