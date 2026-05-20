import textwrap

import pytest

from ledge_lang import LedgeError, checked_run, checked_run_file, run


def ledge_source(source):
    return textwrap.dedent(source).strip()


def test_checked_run_executes_safe_program():
    output = []

    lines, _ = checked_run(
        ledge_source("""
        define r as classify("message") using ["safe", "unsafe"]
        if confidence_of(r) >= 0.8:
            show value_of(r)
        else:
            show "fallback"
        """),
        output_fn=output.append,
    )

    assert output == ["fallback"]
    assert lines == ["fallback"]


def test_checked_run_rejects_unchecked_value_of_before_execution():
    output = []

    with pytest.raises(LedgeError) as exc:
        checked_run(
            ledge_source("""
            define r as classify("message") using ["safe", "unsafe"]
            show value_of(r)
            show "SHOULD_NOT_RUN"
            """),
            output_fn=output.append,
        )

    message = str(exc.value)
    assert "static typecheck failed" in message
    assert "value_of" in message
    assert output == []


def test_checked_run_rejects_direct_uncertain_use_before_execution():
    output = []

    with pytest.raises(LedgeError) as exc:
        checked_run(
            ledge_source("""
            define r as classify("message") using ["safe", "unsafe"]
            show r
            show "SHOULD_NOT_RUN"
            """),
            output_fn=output.append,
        )

    message = str(exc.value)
    assert "static typecheck failed" in message
    assert "Unsafe use of Uncertain value" in message
    assert output == []


def test_checked_run_rejects_unchecked_value_of_inside_interpolation():
    output = []

    with pytest.raises(LedgeError) as exc:
        checked_run(
            ledge_source("""
            define r as classify("invoice") using ["release_payment", "hold_payment"]
            show "AI payment classification: {value_of(r)}"
            show "PAYMENT_RELEASED"
            """),
            output_fn=output.append,
        )

    message = str(exc.value)
    assert "static typecheck failed" in message
    assert "value_of" in message
    assert output == []


def test_run_remains_low_level_direct_execution():
    output = []

    lines, _ = run(
        ledge_source("""
        define r as classify("message") using ["safe", "unsafe"]
        show value_of(r)
        show "RUN_EXECUTED"
        """),
        output_fn=output.append,
    )

    assert output == ["nothing", "RUN_EXECUTED"]
    assert lines == ["nothing", "RUN_EXECUTED"]


def test_checked_run_file_delegates_to_checked_run(tmp_path):
    program = tmp_path / "safe.ledge"
    program.write_text('show "from file"\n', encoding="utf-8")
    output = []

    lines, _ = checked_run_file(str(program), output_fn=output.append)

    assert output == ["from file"]
    assert lines == ["from file"]
