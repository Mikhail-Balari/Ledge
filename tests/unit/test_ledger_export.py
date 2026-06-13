import json

import pytest

from ledge_lang.ledger import (
    DecisionEvent,
    DecisionLedger,
    LedgerExportError,
    build_manifest,
    export_ledger_review_package,
    write_manifest,
)


EXPORT_FILES = {
    "ledger_events.jsonl",
    "ledger_manifest.json",
    "verification_report.json",
    "verification_report.md",
    "decision_summary.json",
    "README.md",
}


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


def write_ledger(path, events=None):
    ledger = DecisionLedger(path)
    if events is None:
        first = make_event()
        second = make_event(sequence=2, previous_event_hash=first.current_event_hash)
        events = [first, second]
    for event in events:
        ledger.append(event)
    return ledger, events


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_export_valid_ledger_without_manifest_creates_output_directory(tmp_path):
    ledger_path = tmp_path / "ledger.jsonl"
    out_dir = tmp_path / "audit_export"
    _, events = write_ledger(ledger_path)

    result = export_ledger_review_package(ledger_path, out_dir)

    assert result.events_exported == len(events)
    assert result.verification_status == "passed_with_warnings"
    assert out_dir.exists()
    assert {path.name for path in out_dir.iterdir()} == EXPORT_FILES


def test_export_valid_ledger_with_manifest_creates_output_directory(tmp_path):
    ledger_path = tmp_path / "ledger.jsonl"
    manifest_path = tmp_path / "manifest.json"
    out_dir = tmp_path / "audit_export"
    ledger, events = write_ledger(ledger_path)
    write_manifest(build_manifest(ledger), manifest_path)

    result = export_ledger_review_package(ledger_path, out_dir, manifest_path=manifest_path)

    assert result.events_exported == len(events)
    assert result.verification_status == "passed"
    assert {path.name for path in out_dir.iterdir()} == EXPORT_FILES


def test_export_writes_expected_files(tmp_path):
    ledger_path = tmp_path / "ledger.jsonl"
    out_dir = tmp_path / "audit_export"
    write_ledger(ledger_path)

    export_ledger_review_package(ledger_path, out_dir)

    for name in EXPORT_FILES:
        assert (out_dir / name).exists()


def test_verification_report_json_is_parseable(tmp_path):
    ledger_path = tmp_path / "ledger.jsonl"
    out_dir = tmp_path / "audit_export"
    write_ledger(ledger_path)

    export_ledger_review_package(ledger_path, out_dir)
    report = read_json(out_dir / "verification_report.json")

    assert report["verification_schema"] == "ledge.ledger_verification.v1"
    assert report["status"] == "passed_with_warnings"


def test_decision_summary_json_is_parseable(tmp_path):
    ledger_path = tmp_path / "ledger.jsonl"
    out_dir = tmp_path / "audit_export"
    write_ledger(ledger_path)

    export_ledger_review_package(ledger_path, out_dir)
    summary = read_json(out_dir / "decision_summary.json")

    assert summary["schema_version"] == "ledge.ledger_review_export.v1"
    assert summary["events_exported"] == 2
    assert summary["total_events_checked"] == 2
    assert summary["verification_status"] == "passed_with_warnings"
    assert summary["policy_results_count"] == {"escalate": 2}
    assert summary["actions_count"] == {"route_to_manual_review": 2}
    assert summary["warnings_count"] == 2
    assert summary["critical_findings_count"] == 0


def test_readme_includes_anti_claims(tmp_path):
    ledger_path = tmp_path / "ledger.jsonl"
    out_dir = tmp_path / "audit_export"
    write_ledger(ledger_path)

    export_ledger_review_package(ledger_path, out_dir)
    readme = (out_dir / "README.md").read_text(encoding="utf-8")

    assert "not compliance certification" in readme
    assert "not tamper-proof" in readme
    assert "not immutable storage" in readme


def test_export_refuses_existing_non_empty_output_without_force(tmp_path):
    ledger_path = tmp_path / "ledger.jsonl"
    out_dir = tmp_path / "audit_export"
    write_ledger(ledger_path)
    out_dir.mkdir()
    (out_dir / "stale.txt").write_text("stale", encoding="utf-8")

    with pytest.raises(LedgerExportError):
        export_ledger_review_package(ledger_path, out_dir)


def test_export_force_overwrites_safely(tmp_path):
    ledger_path = tmp_path / "ledger.jsonl"
    out_dir = tmp_path / "audit_export"
    write_ledger(ledger_path)
    out_dir.mkdir()
    (out_dir / "stale.txt").write_text("stale", encoding="utf-8")

    export_ledger_review_package(ledger_path, out_dir, force=True)

    assert "stale.txt" not in {path.name for path in out_dir.iterdir()}
    assert {path.name for path in out_dir.iterdir()} == EXPORT_FILES


def test_export_fails_for_corrupt_ledger(tmp_path):
    ledger_path = tmp_path / "ledger.jsonl"
    out_dir = tmp_path / "audit_export"
    ledger_path.write_text("{bad-json}\n", encoding="utf-8")

    with pytest.raises(LedgerExportError):
        export_ledger_review_package(ledger_path, out_dir)

    assert not out_dir.exists()


def test_export_fails_for_missing_store(tmp_path):
    with pytest.raises(LedgerExportError):
        export_ledger_review_package(tmp_path / "missing.jsonl", tmp_path / "audit_export")


def test_boundary_filtered_export_includes_only_matching_events(tmp_path):
    ledger_path = tmp_path / "ledger.jsonl"
    first = make_event(boundary_id="refund_routing")
    second = make_event(
        sequence=2,
        previous_event_hash=first.current_event_hash,
        event_id="evt_shipping_0002",
        boundary_id="shipping_routing",
    )
    third = make_event(
        sequence=3,
        previous_event_hash=second.current_event_hash,
        event_id="evt_refund_0003",
        boundary_id="refund_routing",
    )
    write_ledger(ledger_path, [first, second, third])
    out_dir = tmp_path / "audit_export"

    export_ledger_review_package(ledger_path, out_dir, boundary_id="refund_routing")
    lines = (out_dir / "ledger_events.jsonl").read_text(encoding="utf-8").splitlines()
    payloads = [json.loads(line) for line in lines]

    assert [payload["event_id"] for payload in payloads] == [first.event_id, third.event_id]
    assert {payload["boundary_id"] for payload in payloads} == {"refund_routing"}


def test_boundary_filtered_export_summary_records_filter_and_full_verification(tmp_path):
    ledger_path = tmp_path / "ledger.jsonl"
    first = make_event(boundary_id="refund_routing")
    second = make_event(
        sequence=2,
        previous_event_hash=first.current_event_hash,
        event_id="evt_shipping_0002",
        boundary_id="shipping_routing",
    )
    write_ledger(ledger_path, [first, second])
    out_dir = tmp_path / "audit_export"

    export_ledger_review_package(ledger_path, out_dir, boundary_id="refund_routing")
    summary = read_json(out_dir / "decision_summary.json")
    report = read_json(out_dir / "verification_report.json")

    assert summary["boundary_filter"] == "refund_routing"
    assert summary["events_exported"] == 1
    assert summary["total_events_checked"] == 2
    assert report["events_checked"] == 2


def test_export_output_contains_no_raw_payload_fields_or_values(tmp_path):
    ledger_path = tmp_path / "ledger.jsonl"
    out_dir = tmp_path / "audit_export"
    write_ledger(ledger_path)

    export_ledger_review_package(ledger_path, out_dir)
    rendered = "\n".join(path.read_text(encoding="utf-8") for path in out_dir.iterdir())

    assert "raw_input" not in rendered
    assert "raw_output" not in rendered
    assert "prompt" not in rendered
    assert "completion" not in rendered
    assert "messages" not in rendered
    assert "SECRET_SHOULD_NOT_LEAK" not in rendered
