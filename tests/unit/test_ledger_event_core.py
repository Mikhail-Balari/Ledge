import math

import pytest

from ledge_lang.ledger import (
    DecisionEvent,
    LedgerHashError,
    LedgerValidationError,
    canonical_json,
    compute_event_hash,
    verify_event_hash,
)


PREVIOUS_HASH = "a" * 64


def make_event(**overrides):
    values = {
        "event_id": "evt_refund_0001",
        "sequence": 1,
        "timestamp_utc": "2026-06-12T15:04:05Z",
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
        "previous_event_hash": None,
    }
    values.update(overrides)
    return DecisionEvent.create(**values)


def test_can_create_valid_first_decision_event():
    event = make_event()

    assert event.schema_version == "ledge.decision_event.v1"
    assert event.sequence == 1
    assert event.previous_event_hash is None
    assert len(event.current_event_hash) == 64
    assert event.verify_hash()


def test_event_computes_deterministic_current_hash():
    first = make_event()
    second = make_event()

    assert first.current_event_hash == second.current_event_hash
    assert compute_event_hash(first.to_dict()) == first.current_event_hash


def test_canonical_json_is_stable_independent_of_dict_insertion_order():
    first = {"b": 2, "a": {"d": 4, "c": [3, "safe"]}}
    second = {"a": {"c": [3, "safe"], "d": 4}, "b": 2}

    assert canonical_json(first) == canonical_json(second)
    assert canonical_json(first) == '{"a":{"c":[3,"safe"],"d":4},"b":2}'


def test_current_event_hash_is_excluded_from_its_own_hash_input():
    event = make_event()
    payload = event.to_dict()
    tampered_current_hash = dict(payload)
    tampered_current_hash["current_event_hash"] = "0" * 64

    assert compute_event_hash(payload) == event.current_event_hash
    assert compute_event_hash(tampered_current_hash) == event.current_event_hash


def test_from_dict_round_trip_preserves_event_and_hash():
    event = make_event()
    restored = DecisionEvent.from_dict(event.to_dict())

    assert restored == event
    assert restored.current_event_hash == event.current_event_hash
    assert restored.verify_hash()


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("action", "auto_refund"),
        ("confidence_score", 0.12),
        ("policy_hash", "sha256:changed-policy"),
        ("evidence_hash", "sha256:changed-evidence"),
        ("input_hash", "sha256:changed-input"),
        ("output_hash", "sha256:changed-output"),
        ("redaction_profile", "redacted_summary"),
    ],
)
def test_identity_defining_field_changes_break_hash_verification(field, value):
    event = make_event()
    payload = event.to_dict()
    payload[field] = value

    assert not verify_event_hash(payload)
    with pytest.raises(LedgerHashError):
        DecisionEvent.from_dict(payload)


def test_changing_previous_event_hash_changes_hash_and_breaks_verification():
    event = make_event(sequence=2, previous_event_hash=PREVIOUS_HASH)
    payload = event.to_dict()
    changed = dict(payload)
    changed["previous_event_hash"] = "b" * 64

    assert compute_event_hash(changed) != event.current_event_hash
    assert not verify_event_hash(changed)
    with pytest.raises(LedgerHashError):
        DecisionEvent.from_dict(changed)


@pytest.mark.parametrize("confidence_score", [-0.01, 1.01, math.nan, math.inf, -math.inf])
def test_invalid_confidence_values_are_rejected(confidence_score):
    with pytest.raises(LedgerValidationError):
        make_event(confidence_score=confidence_score)


def test_invalid_policy_result_rejected():
    with pytest.raises(LedgerValidationError):
        make_event(policy_result="review_later")


def test_invalid_redaction_profile_rejected():
    with pytest.raises(LedgerValidationError):
        make_event(redaction_profile="raw_payload")


def test_unknown_top_level_fields_rejected_in_from_dict():
    payload = make_event().to_dict()
    payload["unexpected"] = "value"

    with pytest.raises(LedgerValidationError):
        DecisionEvent.from_dict(payload)


@pytest.mark.parametrize(
    "field",
    [
        "input",
        "output",
        "raw_input",
        "raw_output",
        "prompt",
        "completion",
        "messages",
        "response",
        "payload",
    ],
)
def test_raw_looking_fields_are_rejected(field):
    payload = make_event().to_dict()
    payload[field] = "sensitive value"

    with pytest.raises(LedgerValidationError):
        DecisionEvent.from_dict(payload)


def test_optional_correlation_fields_round_trip_when_present():
    event = make_event(
        trace_id="trace-123",
        span_id="span-456",
        request_id="req-789",
        actor_id_hash="sha256:actor",
        service_name="refund-router",
        environment="staging",
    )
    restored = DecisionEvent.from_dict(event.to_dict())

    assert restored.trace_id == "trace-123"
    assert restored.span_id == "span-456"
    assert restored.request_id == "req-789"
    assert restored.actor_id_hash == "sha256:actor"
    assert restored.service_name == "refund-router"
    assert restored.environment == "staging"


def test_previous_event_hash_may_be_none_for_first_event():
    event = make_event(sequence=1, previous_event_hash=None)

    assert event.previous_event_hash is None
    assert event.verify_hash()


def test_previous_event_hash_required_for_later_events():
    with pytest.raises(LedgerValidationError):
        make_event(sequence=2, previous_event_hash=None)


def test_invalid_previous_hash_rejected():
    with pytest.raises(LedgerValidationError):
        make_event(sequence=2, previous_event_hash="not-a-sha256")


def test_invalid_current_hash_rejected_in_from_dict():
    payload = make_event().to_dict()
    payload["current_event_hash"] = "not-a-sha256"

    with pytest.raises(LedgerValidationError):
        DecisionEvent.from_dict(payload)


def test_mismatched_current_hash_rejected_in_from_dict():
    payload = make_event().to_dict()
    payload["current_event_hash"] = "0" * 64

    with pytest.raises(LedgerHashError):
        DecisionEvent.from_dict(payload)


@pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf])
def test_canonical_json_rejects_non_finite_numbers(value):
    with pytest.raises(LedgerValidationError):
        canonical_json({"value": value})


def test_same_event_data_produces_same_hash_across_repeated_calls():
    event = make_event(sequence=2, previous_event_hash=PREVIOUS_HASH)
    payload = event.to_dict()

    assert compute_event_hash(payload) == event.current_event_hash
    assert compute_event_hash(payload) == event.current_event_hash
    assert make_event(sequence=2, previous_event_hash=PREVIOUS_HASH).current_event_hash == event.current_event_hash
