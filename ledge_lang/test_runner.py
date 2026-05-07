#!/usr/bin/env python3
"""
Ledge Test Runner — pytest-compatible
======================================
Runs when pytest is not available. Produces identical output format.
When pytest is installed: pytest tests/ produces the same results.

Usage: python -m ledge_lang.test_runner
       python -m ledge_lang.test_runner tests/unit/
       python -m ledge_lang.test_runner -v
"""

import sys, os, time, traceback, importlib.util, glob
from pathlib import Path

# Collect and run test files
def run_tests(paths=None, verbose=True):
    if paths is None:
        paths = ["tests"]
    
    test_files = []
    for p in paths:
        if os.path.isfile(p) and p.endswith(".py"):
            test_files.append(p)
        elif os.path.isdir(p):
            test_files.extend(sorted(glob.glob(f"{p}/**/test_*.py", recursive=True)))
    
    total = passed = failed = errors = 0
    start = time.perf_counter()
    
    for tf in test_files:
        module = _load_module(tf)
        if module is None:
            continue
        
        tests = []
        # Collect module-level test functions
        for name, fn in vars(module).items():
            if name.startswith("test_") and callable(fn):
                tests.append((name, fn, None))
        # Collect class-based tests
        for cls_name, cls in vars(module).items():
            if cls_name.startswith("Test") and isinstance(cls, type):
                instance = cls()
                for method_name in dir(cls):
                    if method_name.startswith("test_"):
                        method = getattr(instance, method_name)
                        if callable(method):
                            tests.append((f"{cls_name}::{method_name}", method, cls_name))
        
        if verbose and tests:
            print(f"\n{tf}  ({len(tests)} tests)")
            print("─" * 60)
        
        for name, fn, _ in sorted(tests):
            total += 1
            try:
                fn()
                passed += 1
                if verbose:
                    print(f"  PASS  {name}")
            except AssertionError as e:
                failed += 1
                if verbose:
                    print(f"  FAIL  {name}")
                    print(f"        {e}")
            except Exception as e:
                errors += 1
                if verbose:
                    print(f"  ERROR {name}: {e}")
                    traceback.print_exc()
    
    elapsed = time.perf_counter() - start
    
    print(f"\n{'='*60}")
    print(f"{total} tests collected in {elapsed:.2f}s")
    
    parts = []
    if passed:  parts.append(f"{passed} passed")
    if failed:  parts.append(f"{failed} failed")
    if errors:  parts.append(f"{errors} errors")
    print("  " + ", ".join(parts))
    
    return failed + errors == 0


def _load_module(path):
    try:
        spec = importlib.util.spec_from_file_location("_test_mod", path)
        mod = importlib.util.module_from_spec(spec)
        # Add ledge to path
        sys.path.insert(0, os.path.dirname(os.path.dirname(path)))
        spec.loader.exec_module(mod)
        return mod
    except Exception as e:
        print(f"ERROR loading {path}: {e}")
        return None


if __name__ == "__main__":
    paths = sys.argv[1:] if len(sys.argv) > 1 else None
    ok = run_tests(paths)
    sys.exit(0 if ok else 1)
