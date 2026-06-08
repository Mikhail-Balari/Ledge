from ledge_lang.sdk import uncertain_from_validation, validate_with


def test_validate_with_succeeds():
    ok, warnings = validate_with({"status": "ok"}, lambda value: value["status"] == "ok")
    assert ok is True
    assert warnings == []


def test_validate_with_handles_false_result():
    ok, warnings = validate_with({"status": "bad"}, lambda value: False)
    assert ok is False
    assert warnings


def test_validate_with_handles_raised_exception():
    def boom(value):
        raise RuntimeError("broken validator")

    ok, warnings = validate_with({}, boom)
    assert ok is False
    assert "broken validator" in warnings[0]


def test_uncertain_from_validation_success_path():
    result = uncertain_from_validation(
        value={"status": "ok"},
        confidence=0.8,
        validator=lambda value: value["status"] == "ok",
        source="validator",
        metadata={"case": "success"},
    )
    assert result.value == {"status": "ok"}
    assert result.confidence == 0.8
    assert result.source == "validator"
    assert result.metadata["case"] == "success"


def test_uncertain_from_validation_failure_path_sets_confidence_zero():
    result = uncertain_from_validation(
        value={"status": "bad"},
        confidence=0.8,
        validator=lambda value: False,
    )
    assert result.value is None
    assert result.confidence == 0.0
    assert result.warnings
