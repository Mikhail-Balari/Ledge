import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
APP = ROOT / "examples" / "python_integration" / "app.py"


def test_python_integration_app_runs_checked_boundary():
    result = subprocess.run(
        [sys.executable, str(APP)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=20,
    )

    assert result.returncode == 0, result.stderr
    assert "SYNTHETIC DEMO ONLY" in result.stdout
    assert "NOT A CREDIT MODEL" in result.stdout
    assert "NOT A LENDING DECISION SYSTEM" in result.stdout
    assert "Checked execution: ledge_lang.checked_run(...)" in result.stdout
    assert "APPROVE_ALLOWED" in result.stdout
    assert "ROUTE_TO_HUMAN_REVIEW" in result.stdout
    assert "REJECT_ALLOWED" in result.stdout


def test_installed_python_integration_demo_command_runs_successfully():
    result = subprocess.run(
        [sys.executable, "-m", "ledge_lang.cli", "python-integration-demo"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=20,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "SYNTHETIC DEMO ONLY" in result.stdout
    assert "NOT A CREDIT MODEL" in result.stdout
    assert "NOT A LENDING DECISION SYSTEM" in result.stdout
    assert "NOT PRODUCTION OR COMPLIANCE SOFTWARE" in result.stdout
    assert "checked_run(...)" in result.stdout
    assert "APPROVE_ALLOWED" in result.stdout
    assert "ROUTE_TO_HUMAN_REVIEW" in result.stdout
    assert "REJECT_ALLOWED" in result.stdout


def test_python_integration_source_uses_checked_run():
    source = (ROOT / "ledge_lang" / "python_integration_demo.py").read_text(encoding="utf-8")

    assert "from ledge_lang import LedgeError, checked_run" in source
    assert "checked_run(source, ai_backend=backend)" in source


def test_packaged_python_integration_resources_match_source_checkout_example():
    from importlib import resources

    package_root = resources.files("ledge_lang.python_integration")
    source_root = ROOT / "examples" / "python_integration"
    for name in ["decision_boundary.ledge", "fixture.json"]:
        assert package_root.joinpath(name).read_text(encoding="utf-8") == (
            source_root / name
        ).read_text(encoding="utf-8")
