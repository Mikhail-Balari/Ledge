import json

from ledge_lang.ledger import (
    DecisionEvent,
    DecisionLedger,
    LedgerFinding,
    LedgerVerificationResult,
    LedgerVerifier,
    build_manifest,
    compute_event_hash,
    verify_ledger,
    write_manifest,
)


WRONG_HASH = "b" * 64
FIXED_CREATED_AT = "2026-06-12T15:04:05Z"
FIXED_UPDATED_AT = "2026-06-12T15:05:05Z"


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


def write_events(path, events):
    path.write_text("".join(event.to_canonical_json() + "\n" for event in events), encoding="utf-8")


def write_payloads(path, payloads):
    path.write_text("".join(json.dumps(payload, sort_keys=True) + "\n" for payload in payloads), encoding="utf-8")


def linked_events():
    first = make_event()
    second = make_event(sequence=2, previous_event_hash=first.current_event_hash)
    return first, second


def codes(result):
    return {finding["code"] for finding in result.to_dict()["findings"]}


def test_valid_ledger_without_manifest_returns_passed_with_warnings(tmp_path):
    ledger_path = tmp_path / "events.jsonl"
    write_events(ledger_path, linked_events())

    result = verify_ledger(ledger_path)

    assert result.status == "passed_with_warnings"
    assert result.chain_valid is True
    assert result.manifest_valid is False
    assert "LEDGER_MANIFEST_NOT_PROVIDED" in codes(result)


def test_valid_ledger_with_matching_manifest_returns_passed(tmp_path):
    ledger_path = tmp_path / "events.jsonl"
    manifest_path = tmp_path / "manifest.json"
    ledger = DecisionLedger(ledger_path)
    for event in linked_events():
        ledger.append(event)
    write_manifest(build_manifest(ledger), manifest_path)

    result = verify_ledger(ledger_path, manifest_path)

    assert result.status == "passed"
    assert result.chain_valid is True
    assert result.manifest_valid is True
    assert result.findings == ()


def test_result_exposes_stable_machine_readable_dict(tmp_path):
    ledger_path = tmp_path / "events.jsonl"
    first, second = linked_events()
    write_events(ledger_path, [first, second])

    data = verify_ledger(ledger_path).to_dict()

    assert data["verification_schema"] == "ledge.ledger_verification.v1"
    assert data["status"] == "passed_with_warnings"
    assert data["events_checked"] == 2
    assert data["first_event_hash"] == first.current_event_hash
    assert data["last_event_hash"] == second.current_event_hash
    assert data["critical_findings"] == []
    assert data["warnings"][0]["code"] == "LEDGER_MANIFEST_NOT_PROVIDED"


def test_result_exposes_deterministic_json(tmp_path):
    ledger_path = tmp_path / "events.jsonl"
    write_events(ledger_path, linked_events())
    result = verify_ledger(ledger_path)

    assert result.to_json() == result.to_json()
    assert json.loads(result.to_json()) == result.to_dict()


def test_result_exposes_human_readable_text(tmp_path):
    ledger_path = tmp_path / "events.jsonl"
    write_events(ledger_path, linked_events())

    text = verify_ledger(ledger_path).to_text()

    assert "Ledge ledger verification" in text
    assert "Status: passed_with_warnings" in text
    assert "LEDGER_MANIFEST_NOT_PROVIDED" in text


def test_missing_ledger_file_returns_failed_result(tmp_path):
    result = verify_ledger(tmp_path / "missing.jsonl")

    assert result.status == "failed"
    assert "LEDGER_FILE_MISSING" in codes(result)


def test_blank_line_returns_failed_result(tmp_path):
    ledger_path = tmp_path / "events.jsonl"
    ledger_path.write_text("\n", encoding="utf-8")

    result = verify_ledger(ledger_path)

    assert result.status == "failed"
    assert "LEDGER_BLANK_LINE" in codes(result)


def test_invalid_json_line_returns_failed_result(tmp_path):
    ledger_path = tmp_path / "events.jsonl"
    ledger_path.write_text("{bad-json}\n", encoding="utf-8")

    result = verify_ledger(ledger_path)

    assert result.status == "failed"
    assert "LEDGER_INVALID_JSON" in codes(result)


def test_invalid_event_schema_returns_failed_result(tmp_path):
    ledger_path = tmp_path / "events.jsonl"
    payload = make_event().to_dict()
    del payload["event_id"]
    write_payloads(ledger_path, [payload])

    result = verify_ledger(ledger_path)

    assert result.status == "failed"
    assert "LEDGER_INVALID_EVENT_SCHEMA" in codes(result)


def test_tampered_event_action_returns_hash_mismatch(tmp_path):
    _assert_tampered_field_reports_hash_mismatch(tmp_path, "action", "auto_refund")


def test_tampered_confidence_score_returns_hash_mismatch(tmp_path):
    _assert_tampered_field_reports_hash_mismatch(tmp_path, "confidence_score", 0.12)


def test_tampered_policy_hash_returns_hash_mismatch(tmp_path):
    _assert_tampered_field_reports_hash_mismatch(tmp_path, "policy_hash", "sha256:changed-policy")


def test_tampered_evidence_hash_returns_hash_mismatch(tmp_path):
    _assert_tampered_field_reports_hash_mismatch(tmp_path, "evidence_hash", "sha256:changed-evidence")


def test_sequence_gap_returns_failed_result(tmp_path):
    ledger_path = tmp_path / "events.jsonl"
    first = make_event()
    gap_payload = make_event(sequence=2, previous_event_hash=first.current_event_hash).to_dict()
    gap_payload["sequence"] = 3
    gap_payload["current_event_hash"] = compute_event_hash(gap_payload)
    write_payloads(ledger_path, [first.to_dict(), gap_payload])

    result = verify_ledger(ledger_path)

    assert result.status == "failed"
    assert "LEDGER_SEQUENCE_GAP" in codes(result)


def test_duplicate_sequence_returns_failed_result(tmp_path):
    ledger_path = tmp_path / "events.jsonl"
    first = make_event()
    duplicate = make_event(event_id="evt_duplicate")
    write_events(ledger_path, [first, duplicate])

    result = verify_ledger(ledger_path)

    assert result.status == "failed"
    assert "LEDGER_DUPLICATE_SEQUENCE" in codes(result)


def test_first_event_with_previous_hash_returns_failed_result(tmp_path):
    ledger_path = tmp_path / "events.jsonl"
    event = make_event(sequence=1, previous_event_hash=WRONG_HASH)
    write_events(ledger_path, [event])

    result = verify_ledger(ledger_path)

    assert result.status == "failed"
    assert "LEDGER_PREVIOUS_HASH_MISMATCH" in codes(result)


def test_second_event_missing_previous_hash_returns_failed_result(tmp_path):
    ledger_path = tmp_path / "events.jsonl"
    first = make_event()
    second_payload = make_event(sequence=2, previous_event_hash=first.current_event_hash).to_dict()
    second_payload["previous_event_hash"] = None
    second_payload["current_event_hash"] = compute_event_hash(second_payload)
    write_payloads(ledger_path, [first.to_dict(), second_payload])

    result = verify_ledger(ledger_path)

    assert result.status == "failed"
    assert "LEDGER_PREVIOUS_HASH_MISSING" in codes(result)


def test_second_event_wrong_previous_hash_returns_failed_result(tmp_path):
    ledger_path = tmp_path / "events.jsonl"
    first = make_event()
    second = make_event(sequence=2, previous_event_hash=WRONG_HASH)
    write_events(ledger_path, [first, second])

    result = verify_ledger(ledger_path)

    assert result.status == "failed"
    assert "LEDGER_PREVIOUS_HASH_MISMATCH" in codes(result)


def test_manifest_not_provided_is_warning_not_critical_for_valid_ledger(tmp_path):
    ledger_path = tmp_path / "events.jsonl"
    write_events(ledger_path, linked_events())

    result = verify_ledger(ledger_path)

    assert result.status == "passed_with_warnings"
    assert result.critical_findings == ()
    assert result.warnings[0].code == "LEDGER_MANIFEST_NOT_PROVIDED"


def test_missing_manifest_path_returns_failed_result(tmp_path):
    ledger_path = tmp_path / "events.jsonl"
    write_events(ledger_path, linked_events())

    result = verify_ledger(ledger_path, tmp_path / "missing-manifest.json")

    assert result.status == "failed"
    assert "LEDGER_MANIFEST_FILE_MISSING" in codes(result)


def test_manifest_event_count_mismatch_returns_failed_result(tmp_path):
    ledger_path, manifest_path = _write_valid_ledger_and_manifest(tmp_path)
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    payload["event_count"] = 99
    manifest_path.write_text(json.dumps(payload), encoding="utf-8")

    result = verify_ledger(ledger_path, manifest_path)

    assert result.status == "failed"
    assert "LEDGER_MANIFEST_EVENT_COUNT_MISMATCH" in codes(result)


def test_manifest_first_hash_mismatch_returns_failed_result(tmp_path):
    ledger_path, manifest_path = _write_valid_ledger_and_manifest(tmp_path)
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    payload["first_event_hash"] = WRONG_HASH
    manifest_path.write_text(json.dumps(payload), encoding="utf-8")

    result = verify_ledger(ledger_path, manifest_path)

    assert result.status == "failed"
    assert "LEDGER_MANIFEST_FIRST_HASH_MISMATCH" in codes(result)


def test_manifest_last_hash_mismatch_returns_failed_result(tmp_path):
    ledger_path, manifest_path = _write_valid_ledger_and_manifest(tmp_path)
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    payload["last_event_hash"] = WRONG_HASH
    manifest_path.write_text(json.dumps(payload), encoding="utf-8")

    result = verify_ledger(ledger_path, manifest_path)

    assert result.status == "failed"
    assert "LEDGER_MANIFEST_LAST_HASH_MISMATCH" in codes(result)


def test_malformed_manifest_returns_failed_result(tmp_path):
    ledger_path = tmp_path / "events.jsonl"
    manifest_path = tmp_path / "manifest.json"
    write_events(ledger_path, linked_events())
    manifest_path.write_text("{bad-json}", encoding="utf-8")

    result = verify_ledger(ledger_path, manifest_path)

    assert result.status == "failed"
    assert "LEDGER_MANIFEST_INVALID" in codes(result)


def test_verifier_result_never_includes_raw_input_or_output_values(tmp_path):
    ledger_path = tmp_path / "events.jsonl"
    payload = make_event().to_dict()
    payload["raw_input"] = "SECRET_SHOULD_NOT_LEAK"
    write_payloads(ledger_path, [payload])

    result = verify_ledger(ledger_path)
    rendered = result.to_json() + "\n" + result.to_text()

    assert result.status == "failed"
    assert "LEDGER_INVALID_EVENT_SCHEMA" in codes(result)
    assert "SECRET_SHOULD_NOT_LEAK" not in rendered


def test_public_exports_import_correctly():
    from ledge_lang.ledger import (  # noqa: PLC0415
        LedgerFinding as ExportedLedgerFinding,
        LedgerVerificationResult as ExportedLedgerVerificationResult,
        LedgerVerifier as ExportedLedgerVerifier,
        verify_ledger as exported_verify_ledger,
    )

    assert ExportedLedgerFinding is LedgerFinding
    assert ExportedLedgerVerificationResult is LedgerVerificationResult
    assert ExportedLedgerVerifier is LedgerVerifier
    assert exported_verify_ledger is verify_ledger


def _assert_tampered_field_reports_hash_mismatch(tmp_path, field, value):
    ledger_path = tmp_path / "events.jsonl"
    payload = make_event().to_dict()
    payload[field] = value
    write_payloads(ledger_path, [payload])

    result = verify_ledger(ledger_path)

    assert result.status == "failed"
    assert "LEDGER_EVENT_HASH_MISMATCH" in codes(result)


def _write_valid_ledger_and_manifest(tmp_path):
    ledger_path = tmp_path / "events.jsonl"
    manifest_path = tmp_path / "manifest.json"
    ledger = DecisionLedger(ledger_path)
    for event in linked_events():
        ledger.append(event)
    manifest = build_manifest(ledger)
    write_manifest(manifest, manifest_path)
    return ledger_path, manifest_path
