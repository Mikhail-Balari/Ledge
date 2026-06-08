import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_sdk_decision_boundary_example_runs_and_prints_markers():
    result = subprocess.run(
        [sys.executable, "examples/sdk_decision_boundary/app.py"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    output = result.stdout
    assert "SYNTHETIC DEMO ONLY" in output
    assert "ALLOW_REFUND_ROUTE" in output
    assert "ROUTE_TO_HUMAN_REVIEW" in output
    assert "BLOCK_MISSING_VALUE" in output
    assert "UNSAFE_UNWRAP_REJECTED" in output
    assert "EVIDENCE_RECORDED" in output
