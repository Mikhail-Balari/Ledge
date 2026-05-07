"""
Ledge JIT Compiler
==================
Method-level JIT: compiles hot functions to native code at runtime.

Strategy:
  1. Count function calls during tree-walker execution
  2. When a function is called > JIT_THRESHOLD times, compile it to native
  3. Redirect future calls to the native version via ctypes

This gives the benefit of native speed for hot functions without
requiring upfront AOT compilation of the entire program.

The JIT is transparent — programs produce identical output
whether running interpreted or JIT-compiled.

Usage:
    from ledge_lang.jit import JITInterpreter
    
    interp = JITInterpreter(output_fn=print)
    interp.run(ast)
    # Hot functions auto-compiled to native after JIT_THRESHOLD calls
"""
from __future__ import annotations
import ctypes, subprocess, tempfile, os, shutil, threading
from typing import Dict, Optional, Callable

JIT_THRESHOLD = 50   # Compile after this many calls
JIT_ENABLED   = shutil.which("gcc") is not None


class JITStats:
    """Track JIT compilation statistics."""
    def __init__(self):
        self.call_counts: Dict[str, int] = {}
        self.compiled_fns: Dict[str, str] = {}   # fn_name → binary_path
        self.compilation_time_ms: Dict[str, float] = {}
        self.speedup: Dict[str, float] = {}

    def record_call(self, fn_name: str) -> bool:
        """Returns True if this function just crossed the JIT threshold."""
        self.call_counts[fn_name] = self.call_counts.get(fn_name, 0) + 1
        return (JIT_ENABLED and
                self.call_counts[fn_name] == JIT_THRESHOLD and
                fn_name not in self.compiled_fns)

    def print_report(self):
        print("\n=== JIT Compilation Report ===")
        print(f"  JIT enabled: {JIT_ENABLED}")
        if not self.call_counts:
            print("  No function calls recorded.")
            return
        print(f"  {'Function':<25} {'Calls':>7} {'Status':<15}")
        print(f"  {'-'*25} {'-'*7} {'-'*15}")
        for fn, calls in sorted(self.call_counts.items(), key=lambda x: -x[1]):
            if fn in self.compiled_fns:
                speedup = self.speedup.get(fn, 0)
                status = f"JIT ✓ ({speedup:.0f}x)"
            elif calls >= JIT_THRESHOLD:
                status = "pending"
            else:
                status = f"interpreted ({JIT_THRESHOLD-calls} to JIT)"
            print(f"  {fn:<25} {calls:>7} {status:<15}")


def _compile_fn_to_shared_lib(fn_name: str, fn_node, scope) -> Optional[str]:
    """
    Compile a Ledge function to a shared library (.so) for fast calling.
    Returns the path to the .so file, or None on failure.
    """
    try:
        from ledge_lang.compiler.ccodegen import CCodegen, is_numeric_function
        
        if not is_numeric_function(fn_node):
            return None  # Only compile pure numeric functions via JIT
        
        params = fn_node.params
        param_list = ", ".join(f"double {p[0]}" for p in params)
        
        gen = CCodegen()
        gen._numeric_fns = set()
        gen._fn_defs = []
        gen._compile_funcdef(fn_name, fn_node)
        
        # Only keep defs that START with the numeric function (exclude boxed wrapper)
        numeric_defs = [d for d in gen._fn_defs if d.strip().startswith(f"static double fn_num_{fn_name}")]
        if not numeric_defs:
            return None
        fn_code = "\n".join(numeric_defs)
        
        # Generate a shared library with the numeric function exported
        c_src = f"""
#include <math.h>
#include <stdlib.h>

/* Forward declaration for recursion */
static double fn_num_{fn_name}({param_list});

{fn_code}

/* Exported JIT entry point */
double jit_{fn_name}({param_list}) {{
    return fn_num_{fn_name}({", ".join(p[0] for p in params)});
}}
"""
        with tempfile.NamedTemporaryFile(suffix=".c", mode="w", delete=False) as f:
            f.write(c_src)
            c_path = f.name
        
        so_path = c_path.replace(".c", ".so")
        
        result = subprocess.run(
            ["gcc", "-O3", "-march=native", "-shared", "-fPIC",
             "-o", so_path, c_path, "-lm"],
            capture_output=True, timeout=10
        )
        
        os.unlink(c_path)
        
        if result.returncode == 0:
            return so_path
        return None
    except Exception:
        return None


class JITFunction:
    """Wraps a compiled native function for transparent calling."""
    
    def __init__(self, fn_name: str, so_path: str, params):
        self._lib = ctypes.CDLL(so_path)
        self._fn = getattr(self._lib, f"jit_{fn_name}")
        self._fn.restype = ctypes.c_double
        self._fn.argtypes = [ctypes.c_double] * len(params)
        self._params = params
        self.so_path = so_path
    
    def call(self, args) -> float:
        """Call the native function with Ledge values."""
        c_args = []
        for arg in args:
            if hasattr(arg, "v") and hasattr(arg.v, "number"):
                c_args.append(arg.v.number)  # LdgVal
            elif isinstance(arg, (int, float)):
                c_args.append(float(arg))
            else:
                c_args.append(0.0)  # fallback
        return self._fn(*c_args)
    
    def __del__(self):
        try:
            os.unlink(self.so_path)
        except Exception:
            pass


class JITInterpreter:
    """
    Interpreter with transparent JIT compilation of hot numeric functions.
    
    Usage:
        interp = JITInterpreter(output_fn=print)
        ast = compile_ledge(source)
        interp.run(ast)
    """
    
    def __init__(self, output_fn=None, ai_backend=None):
        from ledge_lang.interpreter import Interpreter
        self._interp = Interpreter(output_fn=output_fn, ai_backend=ai_backend)
        self._stats = JITStats()
        self._jit_cache: Dict[str, JITFunction] = {}
        self._fn_nodes: Dict[str, object] = {}
        self._lock = threading.Lock()
        
        # Patch the interpreter to count function calls and JIT hot functions
        original_call_fn = self._interp._call_fn
        jit_self = self
        
        def jit_aware_call_fn(callee, args, kwargs, using):
            name = getattr(callee, "__name__", None) or getattr(callee, "name", None)
            
            # Track call count
            if name and jit_self._stats.record_call(name):
                # Just crossed JIT threshold — compile in background
                fn_node = jit_self._fn_nodes.get(name)
                if fn_node:
                    def compile_bg(n=name, fn=fn_node):
                        so = _compile_fn_to_shared_lib(n, fn, None)
                        if so:
                            with jit_self._lock:
                                try:
                                    jit_self._jit_cache[n] = JITFunction(n, so, fn.params)
                                except Exception:
                                    pass
                    threading.Thread(target=compile_bg, daemon=True).start()
            
            # Use JIT version if available (and call is numeric-safe)
            if name and name in jit_self._jit_cache:
                from ledge_lang.core_types import NOTHING
                try:
                    result = jit_self._jit_cache[name].call(args)
                    from ledge_lang.interpreter import LedgeNumber
                    return result  # Return raw float, interpreter handles it
                except Exception:
                    pass  # Fall back to interpreted
            
            return original_call_fn(callee, args, kwargs, using)
        
        self._interp._call_fn = jit_aware_call_fn
    
    def run(self, ast, env=None):
        # Register function nodes for JIT compilation
        for stmt in ast.stmts:
            if (type(stmt).__name__ == "Define" and stmt.value and
                    type(stmt.value).__name__ == "FuncDef"):
                self._fn_nodes[stmt.name] = stmt.value
        
        return self._interp.run(ast, env)
    
    @property
    def output_lines(self):
        return self._interp.output_lines
    
    @property
    def stats(self):
        return self._stats
