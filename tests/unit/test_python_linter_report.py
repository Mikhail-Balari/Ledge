import json

from ledge_lang.python_linter.report import Diagnostic, diagnostics_to_json, format_diagnostics


def test_text_report_contains_location_rule_and_suggestion():
    diagnostic = Diagnostic(
        path="app.py",
        line=3,
        column=4,
        rule_id="LPY001",
        severity="error",
        message="unsafe_unwrap requires a non-empty reason",
        suggestion='Pass reason="..." explaining the manual override.',
    )

    text = format_diagnostics([diagnostic])

    assert "app.py:3:5" in text
    assert "LPY001" in text
    assert "unsafe_unwrap requires" in text
    assert "Suggestion:" in text


def test_json_report_is_valid_json():
    diagnostic = Diagnostic(
        path="app.py",
        line=1,
        column=0,
        rule_id="LPY002",
        severity="error",
        message="direct .value access",
        suggestion="Use .handle(...)",
    )

    data = json.loads(diagnostics_to_json([diagnostic]))

    assert data[0]["rule_id"] == "LPY002"
    assert data[0]["path"] == "app.py"
