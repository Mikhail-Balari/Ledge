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


def test_python_integration_source_uses_checked_run():
    source = APP.read_text(encoding="utf-8")

    assert "from ledge_lang import LedgeError, checked_run" in source
    assert "checked_run(source, ai_backend=backend)" in source
