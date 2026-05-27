import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "ledge_check_ci.py"


def run_ci_check(*paths):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *map(str, paths)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=30,
    )


def test_ledge_check_ci_passes_required_paths():
    result = run_ci_check(
        ROOT / "ledge_lang" / "demos",
        ROOT / "examples" / "python_integration",
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "Ledge CI typecheck:" in result.stdout
    assert "loan_approval.ledge" in result.stdout
    assert "decision_boundary.ledge" in result.stdout
    assert "PASS: all .ledge files typecheck" in result.stdout


def test_ledge_check_ci_fails_invalid_ledge_file(tmp_path):
    bad = tmp_path / "unsafe.ledge"
    bad.write_text(
        "\n".join(
            [
                'define r as classify("invoice") using ["release_payment", "hold_payment"]',
                'show "AI decision: {value_of(r)}"',
                'show "PAYMENT_RELEASED"',
            ]
        ),
        encoding="utf-8",
    )

    result = run_ci_check(bad)

    assert result.returncode != 0
    output = result.stdout + result.stderr
    assert "FAIL:" in output
    assert "value_of" in output
    assert "PAYMENT_RELEASED" not in output
