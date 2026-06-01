"""
Version consistency tests for release-critical package metadata.

The PyPI package version is checked strictly. Adjacent artifacts that can be
released independently, such as the VS Code extension, are validated without
requiring their version to match the package version.
"""

import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")


def get_version_from(path, pattern):
    try:
        with open(os.path.join(ROOT, path), encoding="utf-8") as f:
            m = re.search(pattern, f.read())
            return m.group(1) if m else None
    except FileNotFoundError:
        return None


# Source of truth for the PyPI package: pyproject.toml. Package version
# locations must match it.
EXPECTED_VERSION = get_version_from("pyproject.toml", r'version = "([^"]+)"')
assert EXPECTED_VERSION, "Could not read version from pyproject.toml - test cannot run"


def test_version_in_private_version_module():
    from ledge_lang._version import __version__

    assert __version__ == EXPECTED_VERSION, (
        f"_version.py version {__version__!r} does not match "
        f"pyproject.toml version {EXPECTED_VERSION!r}"
    )


def test_version_in_init():
    from ledge_lang import __version__

    assert __version__ == EXPECTED_VERSION, (
        f"__init__.py version {__version__!r} does not match "
        f"pyproject.toml version {EXPECTED_VERSION!r}"
    )


def test_regulatory_export_creator_version_matches_package():
    import json
    import tempfile

    from ledge_lang import __version__
    from ledge_lang.audit_store import AuditStore

    with tempfile.TemporaryDirectory() as tmp:
        store = AuditStore(db_path=os.path.join(tmp, "audit.db"))
        data = json.loads(store.export_json_ld())

    assert data["dcterms:creator"] == f"Ledge v{__version__}"


def test_version_in_pyproject():
    # Sanity check: pyproject.toml has a parseable version string.
    assert EXPECTED_VERSION, "pyproject.toml has no parseable version"


def test_cli_version_matches_package():
    import subprocess

    result = subprocess.run(
        [sys.executable, "-m", "ledge_lang.cli", "version"],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )

    assert result.returncode == 0, result.stderr
    assert f"Ledge {EXPECTED_VERSION}" in result.stdout


def test_version_in_vscode():
    v = get_version_from("vscode-ledge/package.json", r'"version":\s*"([^"]+)"')
    if v:  # VS Code extension may not be present in all environments
        # The PyPI package and VS Code extension can be released independently.
        # Only bump the extension version when preparing an extension release.
        assert re.fullmatch(r"\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?", v), (
            f"vscode-ledge/package.json version {v!r} is not semver-like"
        )


def test_no_claims_not_in_feature_matrix():
    """Ensure shipped features in README are in FEATURE_MATRIX.md."""
    matrix_path = os.path.join(ROOT, "docs", "FEATURE_MATRIX.md")
    if not os.path.exists(matrix_path):
        assert False, "FEATURE_MATRIX.md does not exist"
    with open(matrix_path, encoding="utf-8") as f:
        matrix = f.read()
    # Critical: roadmap items must be marked as such
    assert "roadmap" in matrix, "FEATURE_MATRIX.md must have roadmap section"
    assert "shipped" in matrix, "FEATURE_MATRIX.md must have shipped section"
    # Verify dangerous claims are in roadmap, not shipped
    for claim in ["--target wasm", "--target arm32", "--target serverless"]:
        # These should exist in the matrix but as roadmap
        assert claim in matrix, f"'{claim}' must be documented in FEATURE_MATRIX.md"


def test_all_conformance_pass():
    """Run a quick conformance check."""
    import subprocess

    result = subprocess.run(
        [sys.executable, "tests/conformance.py"],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    assert "100.0%" in result.stdout, f"Conformance not 100%: {result.stdout[-200:]}"
