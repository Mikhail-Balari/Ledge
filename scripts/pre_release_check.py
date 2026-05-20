#!/usr/bin/env python3
"""Pre-release verification for Ledge.

This script is intentionally release-oriented rather than publication-channel
specific. It runs the checks that should be green before building and
publishing a distribution artifact.
"""

from __future__ import annotations

import importlib.util
import os
import re
import subprocess
import sys
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEMO_IN_WHEEL = "ledge_lang/demos/medical_triage.ledge"


def log(message: str) -> None:
    print(message, flush=True)


def run_step(name: str, args: list[str]) -> None:
    log(f"\n==> {name}")
    log("+ " + " ".join(args))
    env = os.environ.copy()
    env.setdefault("PYTHONIOENCODING", "utf-8")
    env.setdefault("PYTHONUTF8", "1")
    result = subprocess.run(args, cwd=ROOT, env=env)
    if result.returncode != 0:
        raise SystemExit(f"\nFAIL: {name} exited with code {result.returncode}")
    log(f"PASS: {name}")


def project_version() -> str:
    pyproject = ROOT / "pyproject.toml"
    text = pyproject.read_text(encoding="utf-8")
    match = re.search(r'^version\s*=\s*"([^"]+)"', text, re.MULTILINE)
    if not match:
        raise SystemExit("FAIL: could not read version from pyproject.toml")
    return match.group(1)


def package_version() -> str:
    sys.path.insert(0, str(ROOT))
    import ledge_lang

    return ledge_lang.__version__


def official_ledge_files() -> list[Path]:
    roots = [ROOT / "ledge_lang" / "demos", ROOT / "examples", ROOT / "examples" / "showcase"]
    files: set[Path] = set()
    for root in roots:
        if root.exists():
            files.update(path.resolve() for path in root.rglob("*.ledge"))
    return sorted(files)


def typecheck_examples() -> None:
    files = official_ledge_files()
    if not files:
        raise SystemExit("FAIL: no official .ledge examples found")

    log(f"\n==> Typecheck official .ledge examples ({len(files)} files)")
    for path in files:
        rel = path.relative_to(ROOT)
        log(f"check --types {rel}")
        run_step(
            f"typecheck {rel}",
            [sys.executable, "-m", "ledge_lang.cli", "check", "--types", str(path)],
        )
    log("PASS: all official .ledge examples typecheck")


def ensure_build_available() -> None:
    if importlib.util.find_spec("build") is None:
        raise SystemExit(
            "FAIL: package build module is not installed. "
            "Install it with: python -m pip install --user build"
        )


def newest_wheel(version: str) -> Path:
    dist = ROOT / "dist"
    wheels = sorted(dist.glob("*.whl"), key=lambda path: path.stat().st_mtime, reverse=True)
    if not wheels:
        raise SystemExit("FAIL: build completed but no wheel was found in dist/")

    normalized_version = version.replace("-", "_")
    matching = [wheel for wheel in wheels if normalized_version in wheel.name]
    if not matching:
        names = ", ".join(wheel.name for wheel in wheels)
        raise SystemExit(f"FAIL: no built wheel filename contains version {version!r}; found: {names}")
    return matching[0]


def verify_wheel(wheel: Path, version: str) -> None:
    log(f"\n==> Verify wheel {wheel.name}")
    if version not in wheel.name.replace("-", "_"):
        raise SystemExit(f"FAIL: wheel filename does not contain version {version}: {wheel.name}")

    with zipfile.ZipFile(wheel) as zf:
        names = set(zf.namelist())
    if DEMO_IN_WHEEL not in names:
        raise SystemExit(f"FAIL: wheel missing {DEMO_IN_WHEEL}")
    log(f"PASS: wheel contains {DEMO_IN_WHEEL}")


def main() -> int:
    log("Ledge pre-release verification")
    log(f"Repository: {ROOT}")

    pyproject_version = project_version()
    init_version = package_version()
    if pyproject_version != init_version:
        raise SystemExit(
            "FAIL: version mismatch: "
            f"pyproject.toml={pyproject_version}, ledge_lang.__version__={init_version}"
        )
    log(f"PASS: version consistency pyproject/import = {pyproject_version}")

    run_step("unit tests", [sys.executable, "-m", "pytest", "tests/unit/"])
    run_step("conformance tests", [sys.executable, "tests/conformance.py"])
    typecheck_examples()
    run_step("bundled demo", [sys.executable, "-m", "ledge_lang.cli", "demo", "medical_triage"])

    ensure_build_available()
    run_step("package build", [sys.executable, "-m", "build"])
    verify_wheel(newest_wheel(pyproject_version), pyproject_version)

    log("\nPASS: pre-release verification complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
