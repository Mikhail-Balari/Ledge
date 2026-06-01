import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "run_pilot_dry_run.py"
PILOT_DIR = ROOT / "pilot_templates" / "loan_approval"


def run_dry_run(*args):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *map(str, args)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=20,
    )


def run_cli_dry_run(*args):
    return subprocess.run(
        [sys.executable, "-m", "ledge_lang.cli", "pilot-dry-run", *map(str, args)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=20,
    )


def test_loan_approval_pilot_dry_run_runs_successfully():
    result = run_dry_run(PILOT_DIR)

    assert result.returncode == 0
    assert "SYNTHETIC DEMO ONLY" in result.stdout
    assert "NOT A CREDIT MODEL" in result.stdout
    assert "NOT A LENDING DECISION SYSTEM" in result.stdout
    assert "NOT PRODUCTION OR COMPLIANCE SOFTWARE" in result.stdout
    assert "high_confidence_approve" in result.stdout
    assert "low_confidence_review" in result.stdout
    assert "high_confidence_reject" in result.stdout
    assert "ambiguous_case" in result.stdout
    assert "missing_evidence_case" in result.stdout
    assert "APPROVE_ALLOWED" in result.stdout
    assert "ROUTE_TO_HUMAN_REVIEW" in result.stdout
    assert "REJECT_ALLOWED" in result.stdout
    assert "Human review/fallback: yes" in result.stdout
    assert "Total cases: 5" in result.stdout


def test_packaged_loan_approval_pilot_dry_run_runs_successfully():
    result = run_cli_dry_run("loan_approval")

    assert result.returncode == 0, result.stdout + result.stderr
    assert "SYNTHETIC DEMO ONLY" in result.stdout
    assert "NOT A CREDIT MODEL" in result.stdout
    assert "NOT A LENDING DECISION SYSTEM" in result.stdout
    assert "NOT PRODUCTION OR COMPLIANCE SOFTWARE" in result.stdout
    assert "packaged: loan_approval" in result.stdout
    assert "high_confidence_approve" in result.stdout
    assert "ROUTE_TO_HUMAN_REVIEW" in result.stdout
    assert "Total cases: 5" in result.stdout


def test_pilot_dry_run_missing_files_fail_clearly(tmp_path):
    result = run_dry_run(tmp_path)

    assert result.returncode != 0
    assert "ERROR: required file not found" in result.stderr or "ERROR: required file not found" in result.stdout
    assert "fixture.json" in (result.stderr + result.stdout)


def test_loan_approval_fixture_and_policy_are_valid_json():
    fixture = json.loads((PILOT_DIR / "fixture.json").read_text(encoding="utf-8"))
    policy = json.loads((PILOT_DIR / "policy.json").read_text(encoding="utf-8"))

    case_ids = {case["application_id"] for case in fixture["cases"]}
    assert case_ids == {
        "high_confidence_approve",
        "low_confidence_review",
        "high_confidence_reject",
        "ambiguous_case",
        "missing_evidence_case",
    }
    assert policy["possible_actions"] == [
        "APPROVE_ALLOWED",
        "ROUTE_TO_HUMAN_REVIEW",
        "REJECT_ALLOWED",
    ]
    assert policy["threshold_approve"] == 0.85
    assert policy["threshold_review_min"] == 0.65


def test_packaged_pilot_resources_match_source_checkout_templates():
    from importlib import resources

    package_root = resources.files("ledge_lang.pilot_templates.loan_approval")
    for name in [
        "fixture.json",
        "policy.json",
        "expected_results.md",
        "sample_final_report.md",
    ]:
        assert package_root.joinpath(name).read_text(encoding="utf-8") == (
            PILOT_DIR / name
        ).read_text(encoding="utf-8")
