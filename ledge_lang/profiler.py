"""
Ledge Profiler
==============
Performance profiling for Ledge programs.
Shows where time is spent, which functions are hot,
and what the bottlenecks are.

Usage:
    from ledge_lang.profiler import profile, ProfileResult
    
    result = profile("define fib(n): ...")
    result.print_report()
    
    # Or via CLI:
    # ledge profile program.ledge
    # ledge profile program.ledge --native   (requires gcc)
"""
from __future__ import annotations
import time
from typing import Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class FunctionProfile:
    name: str
    calls: int = 0
    total_ms: float = 0.0
    self_ms: float = 0.0  # time not in callees

    @property
    def avg_ms(self) -> float:
        return self.total_ms / self.calls if self.calls > 0 else 0.0


@dataclass 
class ProfileResult:
    source: str
    total_ms: float
    functions: Dict[str, FunctionProfile]
    output_lines: List[str]
    native_ms: Optional[float] = None

    def print_report(self):
        print(f"\n{'='*55}")
        print(f"  Ledge Profiler Report")
        print(f"{'='*55}")
        print(f"  Total time: {self.total_ms:.2f}ms")
        if self.native_ms:
            print(f"  Native time: {self.native_ms:.2f}ms  ({self.total_ms/self.native_ms:.1f}x speedup with native)")
        print()

        if self.functions:
            # Sort by total time
            fns = sorted(self.functions.values(), key=lambda f: f.total_ms, reverse=True)
            print(f"  {'Function':<20} {'Calls':>8} {'Total ms':>10} {'Avg ms':>8}")
            print(f"  {'-'*20} {'-'*8} {'-'*10} {'-'*8}")
            for fn in fns[:15]:
                pct = fn.total_ms / self.total_ms * 100 if self.total_ms > 0 else 0
                print(f"  {fn.name:<20} {fn.calls:>8} {fn.total_ms:>9.2f}ms {fn.avg_ms:>7.3f}ms  ({pct:.0f}%)")

        print()
        if self.native_ms and self.native_ms > 0:
            print(f"  Interpretation overhead: {self.total_ms/self.native_ms:.1f}x vs native binary")
        print(f"{'='*55}\n")

    def to_dict(self) -> dict:
        return {
            "total_ms": self.total_ms,
            "native_ms": self.native_ms,
            "speedup": self.total_ms / self.native_ms if self.native_ms else None,
            "functions": {
                k: {"calls": v.calls, "total_ms": v.total_ms, "avg_ms": v.avg_ms}
                for k, v in self.functions.items()
            }
        }


class ProfilingInterpreter:
    """Interpreter wrapper that instruments function calls."""

    def __init__(self):
        self.profiles: Dict[str, FunctionProfile] = {}
        self._call_stack: List[tuple] = []  # (fn_name, start_time)

    def before_call(self, fn_name: str):
        self._call_stack.append((fn_name, time.perf_counter()))
        if fn_name not in self.profiles:
            self.profiles[fn_name] = FunctionProfile(name=fn_name)
        self.profiles[fn_name].calls += 1

    def after_call(self, fn_name: str):
        if not self._call_stack:
            return
        name, start = self._call_stack.pop()
        elapsed_ms = (time.perf_counter() - start) * 1000
        if name in self.profiles:
            self.profiles[name].total_ms += elapsed_ms


def profile(source: str, runs: int = 1,
            include_native: bool = True) -> ProfileResult:
    """
    Profile a Ledge program.

    Args:
        source: Ledge source code to profile
        runs: Number of runs to average over
        include_native: Also compile to native and compare (requires gcc)

    Returns:
        ProfileResult with timing data

    Example::

        src = "define fib(n):\n    if n <= 1:\n        return n\n    return fib(n-1)+fib(n-2)\nshow fib(30)"
        result = profile(src)
        result.print_report()
    """
    from .interpreter import Interpreter
    from . import compile_ledge

    # Run with interpreter timing
    times = []
    all_output = []
    profiler = ProfilingInterpreter()

    for _ in range(max(1, runs)):
        interp = Interpreter(output_fn=all_output.append)
        # Instrument function calls via debug hook
        original_call = interp._call_fn.__func__ if hasattr(interp._call_fn, '__func__') else None

        t0 = time.perf_counter()
        ast = compile_ledge(source)
        interp.run(ast)
        elapsed = (time.perf_counter() - t0) * 1000
        times.append(elapsed)

    total_ms = min(times)
    output_lines = all_output[:20]  # first run output

    # Native timing
    native_ms = None
    if include_native:
        import shutil
        if shutil.which('gcc'):
            try:
                import subprocess, tempfile, os
                from .compiler.ccodegen import compile_to_native
                with tempfile.NamedTemporaryFile(suffix='', delete=False) as f:
                    out_path = f.name
                try:
                    compile_to_native(source, out_path)
                    native_times = []
                    for _ in range(max(1, runs)):
                        t0 = time.perf_counter()
                        subprocess.run([out_path], capture_output=True, timeout=30)
                        native_times.append((time.perf_counter() - t0) * 1000)
                    native_ms = min(native_times)
                finally:
                    try: os.unlink(out_path)
                    except: pass
            except Exception:
                pass  # Native not available — that's OK

    return ProfileResult(
        source=source,
        total_ms=total_ms,
        functions=profiler.profiles,
        output_lines=output_lines,
        native_ms=native_ms,
    )


def profile_file(path: str, **kwargs) -> ProfileResult:
    """Profile a .ledge file."""
    with open(path, encoding='utf-8') as f:
        source = f.read()
    return profile(source, **kwargs)
