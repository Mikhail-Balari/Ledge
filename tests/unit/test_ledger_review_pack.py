import json

from ledge_lang.ledger import (
    DecisionEvent,
    DecisionLedger,
    LedgerAIReviewPack,
    build_ai_review_pack,
    build_manifest,
    write_ai_review_pack,
    write_manifest,
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


def write_ledger(path, events=None):
    ledger = DecisionLedger(path)
    if events is None:
        first = make_event()
        second = make_event(sequence=2, previous_event_hash=first.current_event_hash)
        events = [first, second]
    for event in events:
        ledger.append(event)
    return ledger, events


def test_build_review_pack_for_valid_ledger_without_manifest(tmp_path):
    ledger_path = tmp_path / "ledger.jsonl"
    write_ledger(ledger_path)

    pack = build_ai_review_pack(ledger_path)
    data = pack.to_dict()

    assert data["review_schema"] == "ledge.ai_review_pack.v1"
    assert data["ledger_status"] == "passed_with_warnings"
    assert data["manifest_used"] is None
    assert data["events_checked"] == 2
    assert data["events_in_scope"] == 2


def test_build_review_pack_for_valid_ledger_with_manifest(tmp_path):
    ledger_path = tmp_path / "ledger.jsonl"
    manifest_path = tmp_path / "manifest.json"
    ledger, _ = write_ledger(ledger_path)
    write_manifest(build_manifest(ledger), manifest_path)

    pack = build_ai_review_pack(ledger_path, manifest_path=manifest_path)
    data = pack.to_dict()

    assert data["ledger_status"] == "passed"
    assert data["manifest_used"] == str(manifest_path)
    assert data["integrity_summary"]["manifest_valid"] is True


def test_integrity_summary_reflects_full_ledger(tmp_path):
    ledger_path = tmp_path / "ledger.jsonl"
    _, events = write_ledger(ledger_path)

    data = build_ai_review_pack(ledger_path).to_dict()

    assert data["integrity_summary"]["first_event_hash"] == events[0].current_event_hash
    assert data["integrity_summary"]["last_event_hash"] == events[-1].current_event_hash
    assert data["integrity_summary"]["chain_valid"] is True


def test_event_summaries_include_safe_event_fields(tmp_path):
    ledger_path = tmp_path / "ledger.jsonl"
    event = make_event(trace_id="trace-1", request_id="request-1")
    write_ledger(ledger_path, [event])

    summary = build_ai_review_pack(ledger_path).to_dict()["event_summaries"][0]

    assert summary["event_id"] == event.event_id
    assert summary["sequence"] == event.sequence
    assert summary["policy_hash"] == event.policy_hash
    assert summary["evidence_hash"] == event.evidence_hash
    assert summary["input_hash"] == event.input_hash
    assert summary["output_hash"] == event.output_hash
    assert summary["warnings_count"] == 1
    assert summary["trace_id"] == "trace-1"
    assert summary["request_id"] == "request-1"


def test_event_summaries_do_not_include_raw_looking_fields(tmp_path):
    ledger_path = tmp_path / "ledger.jsonl"
    write_ledger(ledger_path)

    summary = build_ai_review_pack(ledger_path).to_dict()["event_summaries"][0]

    assert "input" not in summary
    assert "output" not in summary
    assert "raw_input" not in summary
    assert "raw_output" not in summary
    assert "prompt" not in summary
    assert "completion" not in summary
    assert "messages" not in summary
    assert "response" not in summary
    assert "payload" not in summary


def test_boundary_filter_includes_only_matching_boundary_events(tmp_path):
    ledger_path = tmp_path / "ledger.jsonl"
    first = make_event(boundary_id="refund_routing")
    second = make_event(
        sequence=2,
        previous_event_hash=first.current_event_hash,
        event_id="evt_shipping_0002",
        boundary_id="shipping_routing",
    )
    write_ledger(ledger_path, [first, second])

    data = build_ai_review_pack(ledger_path, boundary_id="refund_routing").to_dict()

    assert data["boundary_filter"] == "refund_routing"
    assert data["events_in_scope"] == 1
    assert [event["boundary_id"] for event in data["event_summaries"]] == ["refund_routing"]


def test_boundary_filter_does_not_alter_full_ledger_integrity_summary(tmp_path):
    ledger_path = tmp_path / "ledger.jsonl"
    first = make_event(boundary_id="refund_routing")
    second = make_event(
        sequence=2,
        previous_event_hash=first.current_event_hash,
        event_id="evt_shipping_0002",
        boundary_id="shipping_routing",
    )
    write_ledger(ledger_path, [first, second])

    data = build_ai_review_pack(ledger_path, boundary_id="refund_routing").to_dict()

    assert data["events_checked"] == 2
    assert data["integrity_summary"]["last_event_hash"] == second.current_event_hash


def test_policy_action_warning_and_critical_counts_are_correct(tmp_path):
    ledger_path = tmp_path / "ledger.jsonl"
    first = make_event(policy_result="block", action="block_refund", warnings=[])
    second = make_event(
        sequence=2,
        previous_event_hash=first.current_event_hash,
        policy_result="escalate",
        action="route_to_manual_review",
        warnings=["low_sample_size", "logprobs_unavailable"],
    )
    write_ledger(ledger_path, [first, second])

    data = build_ai_review_pack(ledger_path).to_dict()

    assert data["policy_results_count"] == {"block": 1, "escalate": 1}
    assert data["actions_count"] == {"block_refund": 1, "route_to_manual_review": 1}
    assert data["warnings_count"] == 2
    assert data["critical_findings_count"] == 0


def test_recommended_review_focus_includes_manifest_warning_when_missing(tmp_path):
    ledger_path = tmp_path / "ledger.jsonl"
    write_ledger(ledger_path)

    focus = build_ai_review_pack(ledger_path).to_dict()["recommended_review_focus"]

    assert any("manifest" in item for item in focus)


def test_recommended_review_focus_includes_blocked_and_escalated_events(tmp_path):
    ledger_path = tmp_path / "ledger.jsonl"
    first = make_event(policy_result="block", action="block_refund", warnings=[])
    second = make_event(
        sequence=2,
        previous_event_hash=first.current_event_hash,
        policy_result="escalate",
        action="route_to_manual_review",
    )
    write_ledger(ledger_path, [first, second])

    focus = build_ai_review_pack(ledger_path).to_dict()["recommended_review_focus"]

    assert any("blocked actions" in item for item in focus)
    assert any("escalated actions" in item for item in focus)


def test_generated_json_is_deterministic_for_same_pack(tmp_path):
    ledger_path = tmp_path / "ledger.jsonl"
    write_ledger(ledger_path)
    pack = build_ai_review_pack(ledger_path)

    assert pack.to_json() == pack.to_json()


def test_limitations_include_anti_claims(tmp_path):
    ledger_path = tmp_path / "ledger.jsonl"
    write_ledger(ledger_path)

    limitations = build_ai_review_pack(ledger_path).to_dict()["limitations"]

    assert "not compliance certification" in limitations
    assert "tamper-evident, not tamper-proof" in limitations
    assert "append-oriented local records, not immutable storage" in limitations
    assert "does not guarantee truth" in limitations
    assert "does not prevent hallucinations" in limitations
    assert "reviewing AI must not trust original AI output blindly" in limitations


def test_corrupted_ledger_generates_failed_review_pack_with_findings(tmp_path):
    ledger_path = tmp_path / "corrupt.jsonl"
    ledger_path.write_text("{bad-json}\n", encoding="utf-8")

    data = build_ai_review_pack(ledger_path).to_dict()

    assert data["ledger_status"] == "failed"
    assert data["event_summaries"] == []
    assert data["critical_findings_count"] == 1
    assert data["findings_summary"][0]["code"] == "LEDGER_INVALID_JSON"


def test_write_ai_review_pack_round_trips_json(tmp_path):
    ledger_path = tmp_path / "ledger.jsonl"
    out_path = tmp_path / "ai_review_pack.json"
    write_ledger(ledger_path)
    pack = build_ai_review_pack(ledger_path)

    write_ai_review_pack(pack, out_path)

    assert json.loads(out_path.read_text(encoding="utf-8"))["review_schema"] == "ledge.ai_review_pack.v1"


def test_public_exports_import_correctly():
    assert LedgerAIReviewPack is not None
    assert build_ai_review_pack is not None
    assert write_ai_review_pack is not None
