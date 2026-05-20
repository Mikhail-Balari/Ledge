#!/usr/bin/env python3
"""Installed-wheel smoke test for CI.

This script builds the project wheel, installs it into a fresh virtual
environment, and runs a small set of commands from outside the repository so
imports come from the installed package rather than the editable checkout.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile
import textwrap
import venv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def log(message: str) -> None:
    print(message, flush=True)


def run(
    name: str,
    args: list[str],
    *,
    cwd: Path,
    expect: int = 0,
) -> subprocess.CompletedProcess[str]:
    log(f"\n==> {name}")
    log("+ " + " ".join(str(arg) for arg in args))
    env = os.environ.copy()
    env.setdefault("PYTHONIOENCODING", "utf-8")
    env.setdefault("PYTHONUTF8", "1")
    result = subprocess.run(args, cwd=cwd, env=env, text=True, capture_output=True)
    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="", file=sys.stderr)
    if result.returncode != expect:
        raise SystemExit(f"FAIL: {name} exited {result.returncode}, expected {expect}")
    log(f"PASS: {name}")
    return result


def project_version() -> str:
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    match = re.search(r'^version\s*=\s*"([^"]+)"', text, re.MULTILINE)
    if not match:
        raise SystemExit("FAIL: could not read version from pyproject.toml")
    return match.group(1)


def venv_paths(venv_dir: Path) -> tuple[Path, Path]:
    if os.name == "nt":
        return venv_dir / "Scripts" / "python.exe", venv_dir / "Scripts" / "ledge.exe"
    return venv_dir / "bin" / "python", venv_dir / "bin" / "ledge"


def assert_installed_import(venv_python: Path, work_dir: Path) -> None:
    code = textwrap.dedent(
        f"""
        from pathlib import Path
        import ledge_lang

        repo = Path({str(ROOT)!r}).resolve()
        package_path = Path(ledge_lang.__file__).resolve()
        print(package_path)
        try:
            package_path.relative_to(repo)
        except ValueError:
            pass
        else:
            raise SystemExit(f"import came from repo checkout: {{package_path}}")
        """
    )
    run("import path comes from installed wheel", [str(venv_python), "-c", code], cwd=work_dir)


def write_unsafe_program(path: Path, direct_uncertain: bool = False) -> None:
    interpolation = "{r}" if direct_uncertain else "{value_of(r)}"
    path.write_text(
        textwrap.dedent(
            f"""
            define r as classify("invoice") using ["release_payment", "hold_payment"]
            show "AI decision: {interpolation}"
            show "PAYMENT_RELEASED"
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )


def main() -> int:
    version = project_version()
    log("Ledge installed-wheel smoke test")
    log(f"Repository: {ROOT}")
    log(f"Version: {version}")

    with tempfile.TemporaryDirectory(prefix="ledge-wheel-smoke-") as tmp:
        tmp_dir = Path(tmp)
        dist_dir = tmp_dir / "dist"
        venv_dir = tmp_dir / "venv"
        work_dir = tmp_dir / "work"
        dist_dir.mkdir()
        work_dir.mkdir()

        run(
            "build wheel",
            [sys.executable, "-m", "build", "--wheel", "--outdir", str(dist_dir)],
            cwd=ROOT,
        )
        wheels = sorted(dist_dir.glob("*.whl"))
        if len(wheels) != 1:
            raise SystemExit(f"FAIL: expected one wheel in {dist_dir}, found {len(wheels)}")
        wheel = wheels[0]
        if version not in wheel.name.replace("-", "_"):
            raise SystemExit(f"FAIL: wheel name does not contain {version}: {wheel.name}")
        log(f"PASS: built {wheel.name}")

        log("\n==> create clean virtual environment")
        venv.EnvBuilder(with_pip=True, clear=True).create(venv_dir)
        venv_python, ledge = venv_paths(venv_dir)
        if not venv_python.exists():
            raise SystemExit(f"FAIL: venv python not found: {venv_python}")
        log(f"PASS: created {venv_dir}")

        run(
            "install built wheel",
            [str(venv_python), "-m", "pip", "install", "--no-index", str(wheel)],
            cwd=work_dir,
        )
        if not ledge.exists():
            raise SystemExit(f"FAIL: ledge console script not found: {ledge}")

        assert_installed_import(venv_python, work_dir)

        version_result = run("ledge version", [str(ledge), "version"], cwd=work_dir)
        if f"Ledge {version}" not in version_result.stdout:
            raise SystemExit(f"FAIL: ledge version did not report {version}")

        run("ledge demo medical_triage", [str(ledge), "demo", "medical_triage"], cwd=work_dir)

        checked_code = (
            "from ledge_lang import checked_run; "
            "print(checked_run('show \"ok\"')[0])"
        )
        checked = run(
            "minimal checked_run program",
            [str(venv_python), "-c", checked_code],
            cwd=work_dir,
        )
        if "['ok']" not in checked.stdout:
            raise SystemExit("FAIL: checked_run did not return ['ok']")

        unsafe = work_dir / "unsafe_interpolation.ledge"
        write_unsafe_program(unsafe)
        blocked = run(
            "unsafe interpolation rejected",
            [str(ledge), "run", str(unsafe)],
            cwd=work_dir,
            expect=1,
        )
        combined = blocked.stdout + blocked.stderr
        if "static typecheck failed" not in combined:
            raise SystemExit("FAIL: unsafe interpolation did not report static typecheck failure")
        if "PAYMENT_RELEASED" in blocked.stdout:
            raise SystemExit("FAIL: unsafe interpolation executed sentinel under checked run")

        bypass = run(
            "unsafe interpolation --unsafe executes",
            [str(ledge), "run", str(unsafe), "--unsafe"],
            cwd=work_dir,
        )
        if "PAYMENT_RELEASED" not in bypass.stdout:
            raise SystemExit("FAIL: --unsafe bypass did not execute sentinel")

    log("\nPASS: installed-wheel smoke test complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
