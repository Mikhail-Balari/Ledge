#!/usr/bin/env python3
"""Lightweight supply-chain visibility check for Ledge.

This is intentionally not a certification step. It reports the current package
metadata, declared dependencies, installed distribution inventory, and the
availability of optional audit/SBOM tools.
"""

from __future__ import annotations

import ast
import importlib.metadata as metadata
import importlib.util
import platform
import re
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PYPROJECT = ROOT / "pyproject.toml"


def log(message: str = "") -> None:
    print(message, flush=True)


def read_pyproject() -> str:
    if not PYPROJECT.exists():
        raise SystemExit(f"FAIL: missing {PYPROJECT}")
    return PYPROJECT.read_text(encoding="utf-8")


def scalar(text: str, key: str) -> str:
    match = re.search(rf'^{re.escape(key)}\s*=\s*"([^"]*)"', text, re.MULTILINE)
    if not match:
        raise SystemExit(f"FAIL: could not read {key!r} from pyproject.toml")
    return match.group(1)


def section(text: str, name: str) -> str:
    match = re.search(
        rf"^\[{re.escape(name)}\]\s*$(.*?)(?=^\[|\Z)",
        text,
        re.MULTILINE | re.DOTALL,
    )
    return match.group(1) if match else ""


def parse_array_literal(value: str) -> list[str]:
    try:
        parsed = ast.literal_eval(value.strip())
    except (SyntaxError, ValueError) as exc:
        raise SystemExit(f"FAIL: could not parse dependency array {value!r}: {exc}") from exc
    if not isinstance(parsed, list) or not all(isinstance(item, str) for item in parsed):
        raise SystemExit(f"FAIL: expected a string list, got {value!r}")
    return parsed


def array_in_project(text: str, key: str) -> list[str]:
    project = section(text, "project")
    match = re.search(rf"^{re.escape(key)}\s*=\s*(\[[^\]]*\])", project, re.MULTILINE)
    if not match:
        return []
    return parse_array_literal(match.group(1))


def optional_dependencies(text: str) -> dict[str, list[str]]:
    optional = section(text, "project.optional-dependencies")
    groups: dict[str, list[str]] = {}
    for match in re.finditer(r"^([A-Za-z0-9_.-]+)\s*=\s*(\[[^\]]*\])", optional, re.MULTILINE):
        groups[match.group(1)] = parse_array_literal(match.group(2))
    return groups


def license_summary(dist: metadata.Distribution) -> str:
    meta = dist.metadata
    license_value = (
        meta.get("License-Expression")
        or meta.get("License")
        or next(
            (
                classifier.removeprefix("License :: ").strip()
                for classifier in meta.get_all("Classifier", [])
                if classifier.startswith("License :: ")
            ),
            "",
        )
    )
    first_line = license_value.strip().splitlines()[0].strip() if license_value.strip() else ""
    if not first_line:
        return "UNKNOWN"
    if len(first_line) > 100:
        return first_line[:97] + "..."
    return first_line


def installed_inventory() -> list[tuple[str, str, str]]:
    rows: list[tuple[str, str, str]] = []
    for dist in metadata.distributions():
        name = dist.metadata.get("Name")
        version = dist.version
        if name:
            rows.append((name, version, license_summary(dist)))
    return sorted(rows, key=lambda row: row[0].lower())


def optional_tool_status() -> list[tuple[str, bool, str]]:
    checks = [
        ("pip-audit", bool(shutil.which("pip-audit") or importlib.util.find_spec("pip_audit")), "dependency vulnerability audit"),
        ("cyclonedx-py", bool(shutil.which("cyclonedx-py") or importlib.util.find_spec("cyclonedx_py")), "CycloneDX SBOM generation"),
    ]
    return checks


def pip_version() -> str:
    result = subprocess.run(
        [sys.executable, "-m", "pip", "--version"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return "unavailable"
    return result.stdout.strip()


def main() -> int:
    text = read_pyproject()
    name = scalar(text, "name")
    version = scalar(text, "version")
    direct_dependencies = array_in_project(text, "dependencies")
    optional = optional_dependencies(text)
    inventory = installed_inventory()

    log("Ledge supply-chain visibility check")
    log(f"Repository: {ROOT}")
    log(f"Package: {name} {version}")
    log(f"Python: {platform.python_version()} ({sys.executable})")
    log(f"Platform: {platform.platform()}")
    log(f"pip: {pip_version()}")

    log("\nDeclared runtime dependencies:")
    if direct_dependencies:
        for dep in direct_dependencies:
            log(f"- {dep}")
    else:
        log("- none")

    log("\nDeclared optional dependency groups:")
    if optional:
        for group, deps in sorted(optional.items()):
            joined = ", ".join(deps) if deps else "none"
            log(f"- {group}: {joined}")
    else:
        log("- none")

    log(f"\nInstalled distribution inventory ({len(inventory)} distributions):")
    for name, version, license_value in inventory:
        log(f"- {name}=={version} | license: {license_value}")

    log("\nOptional external supply-chain tools:")
    for tool, available, purpose in optional_tool_status():
        status = "available" if available else "not installed"
        log(f"- {tool}: {status} ({purpose})")

    log("\nPASS: supply-chain visibility check complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
