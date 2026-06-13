import json

import pytest

from ledge_lang.ledger import (
    DecisionEvent,
    DecisionLedger,
    LedgerHashError,
    LedgerManifest,
    LedgerManifestError,
    LedgerSequenceError,
    LedgerStoreError,
    build_manifest,
    compute_event_hash,
    read_manifest,
    write_manifest,
)


PREVIOUS_HASH = "a" * 64
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


def unsafe_event_from_payload(payload):
    values = dict(payload)
    values["warnings"] = tuple(values["warnings"])
    return DecisionEvent(**values)


def test_initialize_creates_ledger_file(tmp_path):
    ledger_path = tmp_path / "ledger.jsonl"
    ledger = DecisionLedger(ledger_path)

    assert not ledger.exists()
    ledger.initialize()

    assert ledger.exists()
    assert ledger_path.read_text(encoding="utf-8") == ""


def test_initialize_creates_parent_directories(tmp_path):
    ledger_path = tmp_path / "nested" / "ledger" / "events.jsonl"

    DecisionLedger(ledger_path).initialize()

    assert ledger_path.exists()


def test_empty_ledger_reads_as_empty_list(tmp_path):
    ledger = DecisionLedger(tmp_path / "events.jsonl")
    ledger.initialize()

    assert ledger.read_events() == []


def test_append_valid_first_event_and_read_back(tmp_path):
    ledger = DecisionLedger(tmp_path / "events.jsonl")
    event = make_event()

    ledger.append(event)

    assert ledger.read_events() == [event]
    assert ledger.last_event() == event


def test_append_valid_second_event_linked_to_first_hash(tmp_path):
    ledger = DecisionLedger(tmp_path / "events.jsonl")
    first = make_event()
    second = make_event(sequence=2, previous_event_hash=first.current_event_hash)

    ledger.append(first)
    ledger.append(second)

    assert ledger.read_events() == [first, second]


def test_next_sequence_returns_expected_values(tmp_path):
    ledger = DecisionLedger(tmp_path / "events.jsonl")
    first = make_event()

    assert ledger.next_sequence() == 1
    ledger.append(first)
    assert ledger.next_sequence() == 2


def test_expected_previous_hash_for_empty_and_non_empty_ledger(tmp_path):
    ledger = DecisionLedger(tmp_path / "events.jsonl")
    first = make_event()

    assert ledger.expected_previous_hash() is None
    ledger.append(first)
    assert ledger.expected_previous_hash() == first.current_event_hash


def test_reject_first_event_with_sequence_other_than_one(tmp_path):
    ledger = DecisionLedger(tmp_path / "events.jsonl")
    payload = make_event().to_dict()
    payload["sequence"] = 2
    payload["previous_event_hash"] = PREVIOUS_HASH
    payload["current_event_hash"] = compute_event_hash(payload)

    with pytest.raises(LedgerSequenceError):
        ledger.append(unsafe_event_from_payload(payload))


def test_reject_first_event_with_non_none_previous_hash(tmp_path):
    ledger = DecisionLedger(tmp_path / "events.jsonl")
    event = make_event(sequence=1, previous_event_hash=PREVIOUS_HASH)

    with pytest.raises(LedgerSequenceError):
        ledger.append(event)


def test_reject_second_event_without_previous_hash(tmp_path):
    ledger = DecisionLedger(tmp_path / "events.jsonl")
    first = make_event()
    payload = make_event(sequence=2, previous_event_hash=first.current_event_hash).to_dict()
    payload["previous_event_hash"] = None
    payload["current_event_hash"] = compute_event_hash(payload)

    ledger.append(first)
    with pytest.raises(LedgerSequenceError):
        ledger.append(unsafe_event_from_payload(payload))


def test_reject_second_event_with_wrong_previous_hash(tmp_path):
    ledger = DecisionLedger(tmp_path / "events.jsonl")
    first = make_event()
    second = make_event(sequence=2, previous_event_hash=WRONG_HASH)

    ledger.append(first)
    with pytest.raises(LedgerSequenceError):
        ledger.append(second)


def test_reject_duplicate_sequence(tmp_path):
    ledger = DecisionLedger(tmp_path / "events.jsonl")
    first = make_event()
    duplicate = make_event(event_id="evt_refund_duplicate")

    ledger.append(first)
    with pytest.raises(LedgerSequenceError):
        ledger.append(duplicate)


def test_reject_hash_tampered_event_before_append(tmp_path):
    ledger = DecisionLedger(tmp_path / "events.jsonl")
    event = make_event()
    object.__setattr__(event, "current_event_hash", "0" * 64)

    with pytest.raises(LedgerHashError):
        ledger.append(event)


def test_reject_ledger_containing_malformed_json_line(tmp_path):
    ledger_path = tmp_path / "events.jsonl"
    ledger_path.write_text("{not-json}\n", encoding="utf-8")

    with pytest.raises(LedgerStoreError):
        DecisionLedger(ledger_path).read_events()


def test_reject_ledger_containing_event_with_invalid_hash(tmp_path):
    event = make_event()
    payload = event.to_dict()
    payload["current_event_hash"] = "0" * 64
    ledger_path = tmp_path / "events.jsonl"
    ledger_path.write_text(json.dumps(payload) + "\n", encoding="utf-8")

    with pytest.raises(LedgerStoreError):
        DecisionLedger(ledger_path).read_events()


def test_reject_blank_ledger_line(tmp_path):
    ledger_path = tmp_path / "events.jsonl"
    ledger_path.write_text("\n", encoding="utf-8")

    with pytest.raises(LedgerStoreError):
        DecisionLedger(ledger_path).read_events()


def test_manifest_from_empty_ledger_is_allowed(tmp_path):
    ledger = DecisionLedger(tmp_path / "events.jsonl")
    ledger.initialize()

    manifest = build_manifest(ledger)

    assert manifest.event_count == 0
    assert manifest.first_event_hash is None
    assert manifest.last_event_hash is None


def test_manifest_from_non_empty_ledger_has_correct_count_and_hashes(tmp_path):
    ledger = DecisionLedger(tmp_path / "events.jsonl")
    first = make_event()
    second = make_event(sequence=2, previous_event_hash=first.current_event_hash)
    ledger.append(first)
    ledger.append(second)

    manifest = build_manifest(ledger)

    assert manifest.event_count == 2
    assert manifest.first_event_hash == first.current_event_hash
    assert manifest.last_event_hash == second.current_event_hash


def test_manifest_canonical_json_is_stable(tmp_path):
    ledger_path = tmp_path / "events.jsonl"
    payload = {
        "updated_at_utc": FIXED_UPDATED_AT,
        "created_at_utc": FIXED_CREATED_AT,
        "last_event_hash": None,
        "first_event_hash": None,
        "event_count": 0,
        "ledger_path": str(ledger_path),
        "schema_version": "ledge.ledger_manifest.v1",
        "ledge_version": "1.6.0",
    }
    manifest = LedgerManifest.from_dict(payload)
    reordered = LedgerManifest.from_dict(dict(reversed(list(payload.items()))))

    assert manifest.to_canonical_json() == reordered.to_canonical_json()


def test_write_read_manifest_round_trip(tmp_path):
    ledger = DecisionLedger(tmp_path / "events.jsonl")
    event = make_event()
    ledger.append(event)
    manifest = LedgerManifest.from_events(
        ledger_path=ledger.path,
        events=ledger.read_events(),
        created_at_utc=FIXED_CREATED_AT,
        updated_at_utc=FIXED_UPDATED_AT,
    )
    manifest_path = tmp_path / "manifest.json"

    write_manifest(manifest, manifest_path)
    restored = read_manifest(manifest_path)

    assert restored == manifest


def test_manifest_rejects_unknown_fields(tmp_path):
    manifest = LedgerManifest.from_events(
        ledger_path=tmp_path / "events.jsonl",
        events=[],
        created_at_utc=FIXED_CREATED_AT,
        updated_at_utc=FIXED_UPDATED_AT,
    )
    payload = manifest.to_dict()
    payload["unexpected"] = "value"

    with pytest.raises(LedgerManifestError):
        LedgerManifest.from_dict(payload)


def test_manifest_rejects_raw_fields(tmp_path):
    manifest = LedgerManifest.from_events(
        ledger_path=tmp_path / "events.jsonl",
        events=[],
        created_at_utc=FIXED_CREATED_AT,
        updated_at_utc=FIXED_UPDATED_AT,
    )
    payload = manifest.to_dict()
    payload["raw_input"] = "sensitive"

    with pytest.raises(LedgerManifestError):
        LedgerManifest.from_dict(payload)


def test_manifest_does_not_include_raw_input_or_output_fields(tmp_path):
    manifest = LedgerManifest.from_events(
        ledger_path=tmp_path / "events.jsonl",
        events=[],
        created_at_utc=FIXED_CREATED_AT,
        updated_at_utc=FIXED_UPDATED_AT,
    )

    assert "input" not in manifest.to_dict()
    assert "output" not in manifest.to_dict()
    assert "raw_input" not in manifest.to_dict()
    assert "raw_output" not in manifest.to_dict()


def test_public_exports_import_correctly():
    from ledge_lang.ledger import (  # noqa: PLC0415
        DecisionLedger as ExportedDecisionLedger,
        LedgerManifest as ExportedLedgerManifest,
        build_manifest as exported_build_manifest,
        read_manifest as exported_read_manifest,
        write_manifest as exported_write_manifest,
    )

    assert ExportedDecisionLedger is DecisionLedger
    assert ExportedLedgerManifest is LedgerManifest
    assert exported_build_manifest is build_manifest
    assert exported_read_manifest is read_manifest
    assert exported_write_manifest is write_manifest
