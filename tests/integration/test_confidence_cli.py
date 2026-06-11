import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EXAMPLE_DIR = ROOT / "examples" / "confidence"


def run_cli(*args):
    return subprocess.run(
        [sys.executable, "-m", "ledge_lang.cli", *map(str, args)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=30,
    )


def test_confidence_eval_example_text_passes():
    result = run_cli("confidence-eval", EXAMPLE_DIR / "fixture.json")

    assert result.returncode == 0, result.stdout + result.stderr
    assert "Final score" in result.stdout
    assert "Sources:" in result.stdout
    assert "Warnings:" in result.stdout
    assert "No truth guarantee." in result.stdout


def test_confidence_eval_example_json_is_valid():
    result = run_cli("confidence-eval", EXAMPLE_DIR / "fixture.json", "--format", "json")

    assert result.returncode == 0, result.stdout + result.stderr
    data = json.loads(result.stdout)
    assert data["boundary_id"] == "refund_routing"
    assert data["final_score"] <= 0.86
    assert data["no_truth_guarantee"] is True
    assert data["sources"]
    rendered = result.stdout
    assert "refund reason requires review" not in rendered
    assert all("detail_keys" in source for source in data["sources"])
    assert all("details" not in source for source in data["sources"])


def test_confidence_eval_malformed_fixture_exits_2(tmp_path):
    fixture = tmp_path / "fixture.json"
    fixture.write_text("{not json", encoding="utf-8")

    result = run_cli("confidence-eval", fixture)

    assert result.returncode == 2
    assert "ledge confidence-eval" in result.stderr


def test_confidence_eval_schema_failure_exits_1(tmp_path):
    fixture = tmp_path / "fixture.json"
    fixture.write_text(
        json.dumps(
            {
                "boundary_id": "refund_routing",
                "base_score": 0.9,
                "raw_output": {"reason": "needs review"},
                "required_fields": ["route", "reason"],
                "critical_fields": ["route"],
                "expected_types": {"route": "str", "reason": "str"},
            }
        ),
        encoding="utf-8",
    )

    result = run_cli("confidence-eval", fixture)

    assert result.returncode == 1
    assert "critical_field_missing" in result.stdout
    assert "hard_evidence_failure" in result.stdout


def test_calibration_report_example_text_passes_with_low_sample_warning():
    result = run_cli("calibration-report", EXAMPLE_DIR / "outcomes.json")

    assert result.returncode == 0, result.stdout + result.stderr
    assert "Brier score" in result.stdout
    assert "ECE" in result.stdout
    assert "low_sample_size" in result.stdout


def test_calibration_report_example_json_is_valid():
    result = run_cli("calibration-report", EXAMPLE_DIR / "outcomes.json", "--format", "json")

    assert result.returncode == 0, result.stdout + result.stderr
    data = json.loads(result.stdout)
    assert data["boundary_id"] == "refund_routing"
    assert data["sample_count"] == 12
    assert "low_sample_size" in data["warnings"]


def test_calibration_report_malformed_file_exits_2(tmp_path):
    outcomes = tmp_path / "outcomes.json"
    outcomes.write_text("{not json", encoding="utf-8")

    result = run_cli("calibration-report", outcomes)

    assert result.returncode == 2
    assert "ledge calibration-report" in result.stderr


def test_calibration_report_malformed_metadata_exits_2_without_traceback(tmp_path):
    outcomes = tmp_path / "outcomes.json"
    outcomes.write_text(
        json.dumps(
            [
                {
                    "boundary_id": "refund_routing",
                    "prediction_id": "pred_bad",
                    "score": 0.8,
                    "outcome": True,
                    "metadata": "not-a-dict",
                }
            ]
        ),
        encoding="utf-8",
    )

    result = run_cli("calibration-report", outcomes)

    output = result.stdout + result.stderr
    assert result.returncode == 2
    assert "metadata must be a dictionary" in output
    assert "Traceback" not in output


def test_low_sample_size_warning_does_not_make_calibration_cli_fail():
    result = run_cli("calibration-report", EXAMPLE_DIR / "outcomes.json")

    assert result.returncode == 0
    assert "low_sample_size" in result.stdout


def test_existing_version_command_still_reports_1_5_0():
    result = run_cli("version")

    assert result.returncode == 0
    assert "Ledge 1.5.0" in result.stdout
