import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EXAMPLE_DIR = ROOT / "examples" / "python_linter"
CONFIG = EXAMPLE_DIR / "ledge.toml"


def run_lint(*args):
    return subprocess.run(
        [sys.executable, "-m", "ledge_lang.cli", "lint-python", *map(str, args)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=30,
    )


def test_lint_python_safe_example_passes():
    result = run_lint(EXAMPLE_DIR / "safe_usage.py", "--config", CONFIG)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "PASS: no Python lint violations" in result.stdout


def test_lint_python_unsafe_example_fails_with_expected_rules():
    result = run_lint(EXAMPLE_DIR / "unsafe_usage.py", "--config", CONFIG)

    assert result.returncode != 0
    output = result.stdout + result.stderr
    assert "LPY001" in output
    assert "LPY002" in output
    assert "LPY003" in output
    assert "LPY004" in output
    assert "unsafe_usage.py" in output


def test_lint_python_json_output_is_valid_json():
    result = run_lint(EXAMPLE_DIR / "unsafe_usage.py", "--config", CONFIG, "--format", "json")

    assert result.returncode != 0
    data = json.loads(result.stdout)
    assert {item["rule_id"] for item in data} >= {"LPY001", "LPY002", "LPY003", "LPY004"}


def test_lint_python_invalid_config_fails_clearly(tmp_path):
    config = tmp_path / "ledge.toml"
    config.write_text("[ledge.actions]\ncritical = 123\n", encoding="utf-8")

    result = run_lint(EXAMPLE_DIR / "safe_usage.py", "--config", config)

    assert result.returncode == 2
    assert "critical" in (result.stdout + result.stderr)


def test_lint_python_existing_cli_commands_still_work():
    result = subprocess.run(
        [sys.executable, "-m", "ledge_lang.cli", "version"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=20,
    )

    assert result.returncode == 0
    assert "Ledge 1.5.0" in result.stdout
