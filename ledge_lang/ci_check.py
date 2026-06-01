"""Installed CI helper for typechecking Ledge source files."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


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


def display_path(path: Path, base: Path) -> str:
    try:
        return str(path.relative_to(base))
    except ValueError:
        return str(path)


def check_file(path: Path, cwd: Path | None = None) -> tuple[bool, str]:
    env = os.environ.copy()
    env.setdefault("PYTHONIOENCODING", "utf-8")
    env.setdefault("PYTHONUTF8", "1")
    result = subprocess.run(
        [sys.executable, "-m", "ledge_lang.cli", "check", "--types", str(path)],
        cwd=cwd or Path.cwd(),
        env=env,
        capture_output=True,
        text=True,
    )
    output = (result.stdout + result.stderr).strip()
    return result.returncode == 0, output


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Recursively typecheck .ledge files for CI.")
    parser.add_argument("paths", nargs="+", help="Files or directories to check")
    args = parser.parse_args(argv)

    base = Path.cwd().resolve()
    paths = [Path(p).resolve() for p in args.paths]
    files = find_ledge_files(paths)
    if not files:
        raise SystemExit("ERROR: no .ledge files found")

    log(f"Ledge CI typecheck: {len(files)} file(s)")
    failures = 0
    for path in files:
        ok, output = check_file(path, cwd=base)
        rel = display_path(path, base)
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
