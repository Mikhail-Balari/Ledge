#!/usr/bin/env python3
"""CI helper for typechecking Ledge source files.

Usage:
    python scripts/ledge_check_ci.py ledge_lang/demos examples/python_integration

The script is intentionally small and subprocess-based so another repository
can copy the command into CI without importing private checker internals.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def log(message: str) -> None:
    print(message, flush=True)


def find_ledge_files(paths: list[Path]) -> list[Path]:
    files: list[Path] = []
    for path in paths:
        if not path.exists():
            raise SystemExit(f"ERROR: path does not exist: {path}")
        if path.is_file():
            if path.suffix == ".ledge":
                files.append(path)
            continue
        files.extend(sorted(path.rglob("*.ledge")))
    return sorted({path.resolve() for path in files})


def check_file(path: Path) -> tuple[bool, str]:
    env = os.environ.copy()
    env.setdefault("PYTHONIOENCODING", "utf-8")
    env.setdefault("PYTHONUTF8", "1")
    result = subprocess.run(
        [sys.executable, "-m", "ledge_lang.cli", "check", "--types", str(path)],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
    )
    output = (result.stdout + result.stderr).strip()
    return result.returncode == 0, output


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Recursively typecheck .ledge files for CI."
    )
    parser.add_argument("paths", nargs="+", help="Files or directories to check")
    args = parser.parse_args(argv)

    paths = [Path(p).resolve() for p in args.paths]
    files = find_ledge_files(paths)
    if not files:
        raise SystemExit("ERROR: no .ledge files found")

    log(f"Ledge CI typecheck: {len(files)} file(s)")
    failures = 0
    for path in files:
        rel = path.relative_to(ROOT) if path.is_relative_to(ROOT) else path
        ok, output = check_file(path)
        if ok:
            log(f"PASS: {rel}")
        else:
            failures += 1
            log(f"FAIL: {rel}")
            if output:
                for line in output.splitlines():
                    log(f"  {line}")

    if failures:
        log(f"\nFAIL: {failures} .ledge file(s) failed typecheck")
        return 1

    log("\nPASS: all .ledge files typecheck")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
