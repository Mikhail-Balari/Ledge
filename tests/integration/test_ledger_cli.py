import json
import subprocess
import sys
from pathlib import Path

from ledge_lang.ledger import DecisionEvent, DecisionLedger


ROOT = Path(__file__).resolve().parents[2]


def run_cli(*args):
    return subprocess.run(
        [sys.executable, "-m", "ledge_lang.cli", *map(str, args)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=30,
    )


def make_event(sequence=1, previous_event_hash=None, **overrides):
    values = {
        "event_id": f"evt_refund_{sequence:04d}",
        "sequence": sequence,
        "timestamp_utc": f"2026-06-12T15:04:{sequence:02d}Z",
        "boundary_id": "refund_routing",
        "boundary_version": "refund_routing.v1",
        "policy_hash": "sha256:policy",
        "evidence_hash": "sha256:evidence",
        "input_hash": "sha256:input",
        "output_hash": "sha256:output",
        "confidence_score": 0.82,
        "action": "route_to_manual_review",
        "policy_result": "escalate",
        "warnings": ["low_sample_size"],
        "redaction_profile": "hash_only",
        "previous_event_hash": previous_event_hash,
    }
    values.update(overrides)
    return DecisionEvent.create(**values)


def write_valid_ledger(path):
    ledger = DecisionLedger(path)
    first = make_event()
    second = make_event(sequence=2, previous_event_hash=first.current_event_hash)
    ledger.append(first)
    ledger.append(second)
    return first, second


def test_ledger_verify_valid_without_manifest_text_passes_with_warning(tmp_path):
    ledger_path = tmp_path / "valid.jsonl"
    write_valid_ledger(ledger_path)

    result = run_cli("ledger-verify", "--store", ledger_path)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "Status: passed_with_warnings" in result.stdout
    assert "LEDGER_MANIFEST_NOT_PROVIDED" in result.stdout
    assert result.stderr == ""


def test_ledger_verify_valid_without_manifest_json_is_parseable(tmp_path):
    ledger_path = tmp_path / "valid.jsonl"
    write_valid_ledger(ledger_path)

    result = run_cli("ledger-verify", "--store", ledger_path, "--format", "json")

    assert result.returncode == 0, result.stdout + result.stderr
    data = json.loads(result.stdout)
    assert data["status"] == "passed_with_warnings"
    assert data["events_checked"] == 2
    assert data["chain_valid"] is True
    assert "findings" in data
    assert result.stderr == ""


def test_ledger_verify_json_output_does_not_include_raw_values(tmp_path):
    ledger_path = tmp_path / "corrupt.jsonl"
    payload = make_event().to_dict()
    payload["raw_input"] = "SECRET_SHOULD_NOT_LEAK"
    ledger_path.write_text(json.dumps(payload) + "\n", encoding="utf-8")

    result = run_cli("ledger-verify", "--store", ledger_path, "--format", "json")

    assert result.returncode != 0
    data = json.loads(result.stdout)
    rendered = result.stdout + result.stderr
    assert data["status"] == "failed"
    assert "SECRET_SHOULD_NOT_LEAK" not in rendered


def test_ledger_verify_matching_manifest_returns_passed(tmp_path):
    ledger_path = tmp_path / "valid.jsonl"
    manifest_path = tmp_path / "manifest.json"
    write_valid_ledger(ledger_path)
    manifest_result = run_cli("ledger-manifest", "--store", ledger_path, "--out", manifest_path)
    assert manifest_result.returncode == 0, manifest_result.stdout + manifest_result.stderr

    result = run_cli("ledger-verify", "--store", ledger_path, "--manifest", manifest_path)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "Status: passed" in result.stdout
    assert "Manifest valid: true" in result.stdout


def test_ledger_verify_corrupt_ledger_text_returns_nonzero(tmp_path):
    ledger_path = tmp_path / "corrupt.jsonl"
    ledger_path.write_text("{bad-json}\n", encoding="utf-8")

    result = run_cli("ledger-verify", "--store", ledger_path)

    assert result.returncode != 0
    assert "Status: failed" in result.stdout
    assert "LEDGER_INVALID_JSON" in result.stdout


def test_ledger_verify_corrupt_ledger_json_is_parseable(tmp_path):
    ledger_path = tmp_path / "corrupt.jsonl"
    ledger_path.write_text("{bad-json}\n", encoding="utf-8")

    result = run_cli("ledger-verify", "--store", ledger_path, "--format", "json")

    assert result.returncode != 0
    data = json.loads(result.stdout)
    assert data["status"] == "failed"
    assert data["findings"][0]["code"] == "LEDGER_INVALID_JSON"


def test_ledger_verify_strict_treats_manifest_warning_as_nonzero(tmp_path):
    ledger_path = tmp_path / "valid.jsonl"
    write_valid_ledger(ledger_path)

    result = run_cli("ledger-verify", "--store", ledger_path, "--strict")

    assert result.returncode != 0
    assert "Status: passed_with_warnings" in result.stdout


def test_ledger_manifest_writes_manifest(tmp_path):
    ledger_path = tmp_path / "valid.jsonl"
    manifest_path = tmp_path / "nested" / "ledger_manifest.json"
    first, second = write_valid_ledger(ledger_path)

    result = run_cli("ledger-manifest", "--store", ledger_path, "--out", manifest_path)

    assert result.returncode == 0, result.stdout + result.stderr
    assert manifest_path.exists()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["event_count"] == 2
    assert manifest["first_event_hash"] == first.current_event_hash
    assert manifest["last_event_hash"] == second.current_event_hash
    assert str(manifest_path) in result.stdout
    assert second.current_event_hash in result.stdout


def test_generated_manifest_can_be_used_by_ledger_verify(tmp_path):
    ledger_path = tmp_path / "valid.jsonl"
    manifest_path = tmp_path / "manifest.json"
    write_valid_ledger(ledger_path)
    manifest_result = run_cli("ledger-manifest", "--store", ledger_path, "--out", manifest_path)
    assert manifest_result.returncode == 0, manifest_result.stdout + manifest_result.stderr

    result = run_cli(
        "ledger-verify",
        "--store",
        ledger_path,
        "--manifest",
        manifest_path,
        "--format",
        "json",
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(result.stdout)["status"] == "passed"


def test_ledger_manifest_refuses_overwrite_without_force(tmp_path):
    ledger_path = tmp_path / "valid.jsonl"
    manifest_path = tmp_path / "manifest.json"
    write_valid_ledger(ledger_path)
    first_result = run_cli("ledger-manifest", "--store", ledger_path, "--out", manifest_path)
    assert first_result.returncode == 0, first_result.stdout + first_result.stderr

    result = run_cli("ledger-manifest", "--store", ledger_path, "--out", manifest_path)

    assert result.returncode != 0
    assert "refusing to overwrite" in result.stderr


def test_ledger_manifest_force_overwrites(tmp_path):
    ledger_path = tmp_path / "valid.jsonl"
    manifest_path = tmp_path / "manifest.json"
    write_valid_ledger(ledger_path)
    first_result = run_cli("ledger-manifest", "--store", ledger_path, "--out", manifest_path)
    assert first_result.returncode == 0, first_result.stdout + first_result.stderr
    manifest_path.write_text('{"stale": true}\n', encoding="utf-8")

    result = run_cli("ledger-manifest", "--store", ledger_path, "--out", manifest_path, "--force")

    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(manifest_path.read_text(encoding="utf-8"))["event_count"] == 2


def test_ledger_manifest_missing_store_returns_nonzero(tmp_path):
    result = run_cli(
        "ledger-manifest",
        "--store",
        tmp_path / "missing.jsonl",
        "--out",
        tmp_path / "manifest.json",
    )

    assert result.returncode != 0
    assert "ledger store not found" in result.stderr


def test_ledger_verify_invalid_format_is_rejected(tmp_path):
    ledger_path = tmp_path / "valid.jsonl"
    write_valid_ledger(ledger_path)

    result = run_cli("ledger-verify", "--store", ledger_path, "--format", "xml")

    assert result.returncode == 2
    assert "invalid choice" in result.stderr


def test_public_help_lists_ledger_commands():
    result = run_cli("help")

    assert result.returncode == 0
    assert "ledger-verify" in result.stdout
    assert "ledger-manifest" in result.stdout
