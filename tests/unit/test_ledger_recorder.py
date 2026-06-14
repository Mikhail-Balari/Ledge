import pytest

from ledge_lang.sdk import DecisionResult
from ledge_lang.ledger import (
    DecisionLedger,
    LedgerMappingError,
    LedgerRecordContext,
    LedgerRecorder,
    LedgerStoreError,
    LedgerValidationError,
    LedgerVerifier,
    record_decision_event,
    record_decision_result,
)


def context(**overrides):
    values = {
        "boundary_id": "refund_routing",
        "boundary_version": "refund_routing.v1",
        "policy_hash": "sha256:policy",
        "redaction_profile": "hash_only",
    }
    values.update(overrides)
    return LedgerRecordContext(**values)


def record_kwargs(**overrides):
    values = {
        "evidence_hash": "sha256:evidence",
        "input_hash": "sha256:input",
        "output_hash": "sha256:output",
        "confidence_score": 0.82,
        "action": "route_to_manual_review",
        "policy_result": "escalate",
        "warnings": ["low_sample_size"],
    }
    values.update(overrides)
    return values


def sdk_result(**overrides):
    values = {
        "action": "human_review",
        "allowed": False,
        "value": {"raw_output": "SECRET_SHOULD_NOT_LEAK"},
        "confidence": 0.73,
        "reason": "low confidence",
        "warnings": ["sdk_warning"],
        "metadata": {"raw_output": "SECRET_SHOULD_NOT_LEAK"},
    }
    values.update(overrides)
    return DecisionResult(**values)


class ResultStub:
    def __init__(self, **values):
        self.__dict__.update(values)


def line_count(path):
    if not path.exists():
        return 0
    return len(path.read_text(encoding="utf-8").splitlines())


def test_recorder_initializes_missing_ledger_when_requested(tmp_path):
    ledger_path = tmp_path / "ledger.jsonl"

    recorder = LedgerRecorder(ledger_path, context(), initialize=True)

    assert recorder.ledger.exists()
    assert ledger_path.exists()


def test_recorder_fails_on_missing_ledger_without_initialize(tmp_path):
    with pytest.raises(LedgerStoreError):
        LedgerRecorder(tmp_path / "missing.jsonl", context())


def test_recorder_records_first_event_with_sequence_one(tmp_path):
    recorder = LedgerRecorder(tmp_path / "ledger.jsonl", context(), initialize=True)

    event = recorder.record(**record_kwargs())

    assert event.sequence == 1
    assert event.previous_event_hash is None
    assert DecisionLedger(recorder.ledger.path).read_events() == [event]


def test_recorder_records_second_event_with_linked_previous_hash(tmp_path):
    recorder = LedgerRecorder(tmp_path / "ledger.jsonl", context(), initialize=True)
    first = recorder.record(**record_kwargs())

    second = recorder.record(**record_kwargs(event_id="evt_second"))

    assert second.sequence == 2
    assert second.previous_event_hash == first.current_event_hash
    assert DecisionLedger(recorder.ledger.path).read_events() == [first, second]


def test_returned_event_verifies_hash(tmp_path):
    recorder = LedgerRecorder(tmp_path / "ledger.jsonl", context(), initialize=True)

    event = recorder.record(**record_kwargs())

    assert event.verify_hash()


def test_ledger_verifies_after_recorder_appends_events(tmp_path):
    ledger_path = tmp_path / "ledger.jsonl"
    recorder = LedgerRecorder(ledger_path, context(), initialize=True)
    recorder.record(**record_kwargs())
    recorder.record(**record_kwargs(event_id="evt_second"))

    result = LedgerVerifier().verify(ledger_path)

    assert result.status == "passed_with_warnings"
    assert result.chain_valid is True


def test_recorder_auto_generates_event_id_when_missing(tmp_path):
    recorder = LedgerRecorder(tmp_path / "ledger.jsonl", context(), initialize=True)

    event = recorder.record(**record_kwargs())

    assert event.event_id.startswith("evt_")
    assert len(event.event_id) > 4


def test_recorder_auto_generates_utc_timestamp(tmp_path):
    recorder = LedgerRecorder(tmp_path / "ledger.jsonl", context(), initialize=True)

    event = recorder.record(**record_kwargs())

    assert event.timestamp_utc.endswith("Z")
    assert "T" in event.timestamp_utc


def test_explicit_event_id_and_timestamp_are_preserved(tmp_path):
    recorder = LedgerRecorder(tmp_path / "ledger.jsonl", context(), initialize=True)

    event = recorder.record(
        **record_kwargs(
            event_id="evt_explicit",
            timestamp_utc="2026-06-14T12:34:56Z",
        )
    )

    assert event.event_id == "evt_explicit"
    assert event.timestamp_utc == "2026-06-14T12:34:56Z"


def test_context_correlation_fields_are_copied_into_event(tmp_path):
    recorder = LedgerRecorder(
        tmp_path / "ledger.jsonl",
        context(
            trace_id="trace-1",
            span_id="span-1",
            request_id="request-1",
            actor_id_hash="actor-hash",
            service_name="refund-service",
            environment="test",
        ),
        initialize=True,
    )

    event = recorder.record(**record_kwargs())

    assert event.trace_id == "trace-1"
    assert event.span_id == "span-1"
    assert event.request_id == "request-1"
    assert event.actor_id_hash == "actor-hash"
    assert event.service_name == "refund-service"
    assert event.environment == "test"


def test_invalid_confidence_rejected(tmp_path):
    recorder = LedgerRecorder(tmp_path / "ledger.jsonl", context(), initialize=True)

    with pytest.raises(LedgerValidationError):
        recorder.record(**record_kwargs(confidence_score=1.1))


def test_invalid_policy_result_rejected(tmp_path):
    recorder = LedgerRecorder(tmp_path / "ledger.jsonl", context(), initialize=True)

    with pytest.raises(LedgerValidationError):
        recorder.record(**record_kwargs(policy_result="approve"))


def test_invalid_redaction_profile_rejected():
    with pytest.raises(LedgerValidationError):
        context(redaction_profile="raw")


def test_raw_looking_fields_cannot_be_passed_through_context_or_record_api(tmp_path):
    with pytest.raises(TypeError):
        LedgerRecordContext(
            boundary_id="refund_routing",
            boundary_version="refund_routing.v1",
            policy_hash="sha256:policy",
            raw_input="SECRET_SHOULD_NOT_LEAK",
        )

    recorder = LedgerRecorder(tmp_path / "ledger.jsonl", context(), initialize=True)
    with pytest.raises(TypeError):
        recorder.record(**record_kwargs(raw_output="SECRET_SHOULD_NOT_LEAK"))


def test_record_decision_event_helper_works(tmp_path):
    ledger_path = tmp_path / "ledger.jsonl"

    event = record_decision_event(
        ledger_path,
        context(),
        initialize=True,
        **record_kwargs(event_id="evt_helper"),
    )

    assert event.event_id == "evt_helper"
    assert DecisionLedger(ledger_path).read_events() == [event]


def test_public_exports_import_correctly():
    assert LedgerRecorder is not None
    assert LedgerRecordContext is not None
    assert record_decision_event is not None
    assert record_decision_result is not None
    assert LedgerMappingError is not None


def test_no_raw_input_or_output_values_appear_in_recorded_event(tmp_path):
    recorder = LedgerRecorder(tmp_path / "ledger.jsonl", context(), initialize=True)

    event = recorder.record(**record_kwargs())
    rendered = event.to_canonical_json()

    assert "SECRET_SHOULD_NOT_LEAK" not in rendered
    assert "raw_input" not in rendered
    assert "raw_output" not in rendered
    assert '"input"' not in rendered
    assert '"output"' not in rendered


def test_record_decision_result_records_with_explicit_fields(tmp_path):
    ledger_path = tmp_path / "ledger.jsonl"

    event = record_decision_result(
        ledger_path,
        sdk_result(),
        context=context(),
        evidence_hash="sha256:evidence",
        input_hash="sha256:input",
        output_hash="sha256:output",
        policy_result="escalate",
        initialize=True,
    )

    assert event.confidence_score == 0.73
    assert event.action == "human_review"
    assert event.policy_result == "escalate"
    assert event.evidence_hash == "sha256:evidence"
    assert event.input_hash == "sha256:input"
    assert event.output_hash == "sha256:output"
    assert event.warnings == ("sdk_warning",)
    assert event.verify_hash()


def test_record_decision_result_ledger_verifies_after_append(tmp_path):
    ledger_path = tmp_path / "ledger.jsonl"

    record_decision_result(
        ledger_path,
        sdk_result(),
        context=context(),
        evidence_hash="sha256:evidence",
        input_hash="sha256:input",
        output_hash="sha256:output",
        policy_result="escalate",
        initialize=True,
    )

    result = LedgerVerifier().verify(ledger_path)

    assert result.status == "passed_with_warnings"
    assert result.chain_valid is True


def test_record_decision_result_uses_explicit_action_when_provided(tmp_path):
    ledger_path = tmp_path / "ledger.jsonl"

    event = record_decision_result(
        ledger_path,
        sdk_result(action="block"),
        context=context(),
        evidence_hash="sha256:evidence",
        input_hash="sha256:input",
        output_hash="sha256:output",
        policy_result="block",
        action="manual_block",
        initialize=True,
    )

    assert event.action == "manual_block"


def test_record_decision_result_uses_explicit_warnings_when_provided(tmp_path):
    ledger_path = tmp_path / "ledger.jsonl"

    event = record_decision_result(
        ledger_path,
        sdk_result(warnings=["ignored_sdk_warning"]),
        context=context(),
        evidence_hash="sha256:evidence",
        input_hash="sha256:input",
        output_hash="sha256:output",
        policy_result="escalate",
        warnings=["explicit_warning"],
        initialize=True,
    )

    assert event.warnings == ("explicit_warning",)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("policy_result", None),
        ("evidence_hash", None),
        ("input_hash", None),
        ("output_hash", None),
        ("policy_result", ""),
        ("evidence_hash", ""),
        ("input_hash", ""),
        ("output_hash", ""),
    ],
)
def test_record_decision_result_missing_required_mapping_fails_closed(
    tmp_path,
    field,
    value,
):
    ledger_path = tmp_path / "ledger.jsonl"
    kwargs = {
        "context": context(),
        "evidence_hash": "sha256:evidence",
        "input_hash": "sha256:input",
        "output_hash": "sha256:output",
        "policy_result": "escalate",
        "initialize": True,
    }
    kwargs[field] = value

    with pytest.raises(LedgerMappingError):
        record_decision_result(ledger_path, sdk_result(), **kwargs)

    assert line_count(ledger_path) == 0


def test_record_decision_result_missing_action_fails_closed(tmp_path):
    ledger_path = tmp_path / "ledger.jsonl"
    result = ResultStub(confidence=0.7, warnings=[])

    with pytest.raises(LedgerMappingError):
        record_decision_result(
            ledger_path,
            result,
            context=context(),
            evidence_hash="sha256:evidence",
            input_hash="sha256:input",
            output_hash="sha256:output",
            policy_result="escalate",
            initialize=True,
        )

    assert line_count(ledger_path) == 0


@pytest.mark.parametrize("confidence", [True, "0.7", float("nan"), float("inf"), -0.1, 1.1])
def test_record_decision_result_invalid_confidence_fails_closed(tmp_path, confidence):
    ledger_path = tmp_path / "ledger.jsonl"
    result = ResultStub(confidence=confidence, action="human_review", warnings=[])

    with pytest.raises(LedgerMappingError):
        record_decision_result(
            ledger_path,
            result,
            context=context(),
            evidence_hash="sha256:evidence",
            input_hash="sha256:input",
            output_hash="sha256:output",
            policy_result="escalate",
            initialize=True,
        )

    assert line_count(ledger_path) == 0


def test_record_decision_result_invalid_policy_result_fails_closed(tmp_path):
    ledger_path = tmp_path / "ledger.jsonl"

    with pytest.raises(LedgerValidationError):
        record_decision_result(
            ledger_path,
            sdk_result(),
            context=context(),
            evidence_hash="sha256:evidence",
            input_hash="sha256:input",
            output_hash="sha256:output",
            policy_result="approve",
            initialize=True,
        )

    assert line_count(ledger_path) == 0


def test_record_decision_result_invalid_warnings_fail_closed(tmp_path):
    ledger_path = tmp_path / "ledger.jsonl"
    result = ResultStub(confidence=0.7, action="human_review", warnings=[object()])

    with pytest.raises(LedgerMappingError):
        record_decision_result(
            ledger_path,
            result,
            context=context(),
            evidence_hash="sha256:evidence",
            input_hash="sha256:input",
            output_hash="sha256:output",
            policy_result="escalate",
            initialize=True,
        )

    assert line_count(ledger_path) == 0


def test_record_decision_result_never_serializes_result_value(tmp_path):
    ledger_path = tmp_path / "ledger.jsonl"

    event = record_decision_result(
        ledger_path,
        sdk_result(value={"payload": "SECRET_SHOULD_NOT_LEAK"}),
        context=context(),
        evidence_hash="sha256:evidence",
        input_hash="sha256:input",
        output_hash="sha256:output",
        policy_result="escalate",
        initialize=True,
    )
    rendered = event.to_canonical_json()

    assert "SECRET_SHOULD_NOT_LEAK" not in rendered
    assert "payload" not in rendered
    assert "raw_output" not in rendered


def test_record_decision_result_never_serializes_raw_looking_result_fields(tmp_path):
    ledger_path = tmp_path / "ledger.jsonl"
    result = ResultStub(
        confidence=0.7,
        action="human_review",
        warnings=[],
        prompt="SECRET_SHOULD_NOT_LEAK",
        completion="SECRET_SHOULD_NOT_LEAK",
        raw_output="SECRET_SHOULD_NOT_LEAK",
        payload="SECRET_SHOULD_NOT_LEAK",
    )

    event = record_decision_result(
        ledger_path,
        result,
        context=context(),
        evidence_hash="sha256:evidence",
        input_hash="sha256:input",
        output_hash="sha256:output",
        policy_result="escalate",
        initialize=True,
    )
    rendered = event.to_canonical_json()

    assert "SECRET_SHOULD_NOT_LEAK" not in rendered
    assert "prompt" not in rendered
    assert "completion" not in rendered
    assert "raw_output" not in rendered
    assert "payload" not in rendered
