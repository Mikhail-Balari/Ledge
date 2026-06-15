import json
import subprocess
import sys
from pathlib import Path


RAW_LEAK_TERMS = (
    "SECRET_SHOULD_NOT_LEAK",
    "raw_input",
    "raw_output",
    "prompt",
    "completion",
    "messages",
    "payload",
    "customer_data",
    "tier_2_support",
)


def run_command(*args):
    return subprocess.run(
        [sys.executable, "-m", "ledge_lang.cli", *args],
        capture_output=True,
        text=True,
        check=False,
    )


def read_texts(path: Path) -> str:
    if path.is_file():
        return path.read_text(encoding="utf-8")
    chunks: list[str] = []
    for child in sorted(path.rglob("*")):
        if child.is_file():
            chunks.append(child.read_text(encoding="utf-8"))
    return "\n".join(chunks)


def test_sdk_decision_result_to_ledger_example_end_to_end(tmp_path):
    out_dir = tmp_path / "ledger_example"
    script = Path("examples/ledger/sdk_decision_result_to_ledger.py")

    script_result = subprocess.run(
        [sys.executable, str(script), "--out", str(out_dir)],
        capture_output=True,
        text=True,
        check=False,
    )

    assert script_result.returncode == 0, script_result.stderr
    summary = json.loads(script_result.stdout)
    assert summary["status"] == "ok"
    assert summary["verification_status"] == "passed"

    ledger_path = out_dir / "support_ticket_ledger.jsonl"
    manifest_path = out_dir / "ledger_manifest.json"
    export_dir = out_dir / "audit_export"
    review_pack_path = out_dir / "ai_review_pack.json"

    assert ledger_path.exists()
    assert manifest_path.exists()
    assert export_dir.is_dir()
    assert review_pack_path.exists()

    verify = run_command(
        "ledger-verify",
        "--store",
        str(ledger_path),
        "--manifest",
        str(manifest_path),
        "--format",
        "json",
    )
    assert verify.returncode == 0, verify.stderr
    verify_json = json.loads(verify.stdout)
    assert verify_json["status"] == "passed"
    assert verify_json["chain_valid"] is True

    review_pack = json.loads(review_pack_path.read_text(encoding="utf-8"))
    assert review_pack["review_schema"] == "ledge.ai_review_pack.v1"
    assert review_pack["ledger_status"] == "passed"
    assert review_pack["integrity_summary"]["chain_valid"] is True
    assert review_pack["events_in_scope"] == 1

    expected_export_files = {
        "ledger_events.jsonl",
        "ledger_manifest.json",
        "verification_report.json",
        "verification_report.md",
        "decision_summary.json",
        "README.md",
    }
    assert expected_export_files.issubset({path.name for path in export_dir.iterdir()})

    export_report = json.loads((export_dir / "verification_report.json").read_text(encoding="utf-8"))
    assert export_report["status"] == "passed"

    exported_pack = tmp_path / "cli_ai_review_pack.json"
    cli_pack = run_command(
        "ledger-review-pack",
        "--store",
        str(ledger_path),
        "--manifest",
        str(manifest_path),
        "--out",
        str(exported_pack),
    )
    assert cli_pack.returncode == 0, cli_pack.stderr
    assert json.loads(exported_pack.read_text(encoding="utf-8"))["ledger_status"] == "passed"

    cli_export_dir = tmp_path / "cli_audit_export"
    cli_export = run_command(
        "ledger-export",
        "--store",
        str(ledger_path),
        "--manifest",
        str(manifest_path),
        "--out",
        str(cli_export_dir),
    )
    assert cli_export.returncode == 0, cli_export.stderr
    assert (cli_export_dir / "decision_summary.json").exists()

    generated_text = "\n".join(
        [
            read_texts(ledger_path),
            read_texts(manifest_path),
            read_texts(export_dir),
            read_texts(review_pack_path),
            read_texts(exported_pack),
            read_texts(cli_export_dir),
        ]
    )
    for term in RAW_LEAK_TERMS:
        assert term not in generated_text
