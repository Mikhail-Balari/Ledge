from ledge_lang.python_linter.config import LintConfig
from ledge_lang.python_linter.scanner import lint_paths, lint_source


def ids_for(source):
    diagnostics = lint_source(source, "scanner_example.py", LintConfig())
    return [diagnostic.rule_id for diagnostic in diagnostics]


def test_tracks_uncertain_from_validation_factory():
    ids = ids_for(
        """
from ledge_lang.sdk import uncertain_from_validation
risk = uncertain_from_validation("x", 0.9, lambda value: True)
print(risk.value)
"""
    )

    assert "LPY002" in ids


def test_tracks_fake_client_predict_as_uncertain():
    ids = ids_for(
        """
from ledge_lang.sdk import FakeAIClient
client = FakeAIClient({"case": {"value": "x", "confidence": 0.9}})
risk = client.predict("case")
print(risk.value)
"""
    )

    assert "LPY002" in ids


def test_tracks_function_annotated_as_returning_uncertain():
    ids = ids_for(
        """
from ledge_lang.sdk import Uncertain
def classify() -> Uncertain[str]:
    return Uncertain(value="x", confidence=0.9)
risk = classify()
print(risk.value)
"""
    )

    assert "LPY002" in ids


def test_tracks_uncertain_from_ledge_lang_sdk_import():
    ids = ids_for(
        """
from ledge_lang import sdk
risk = sdk.Uncertain(value="x", confidence=0.9)
print(risk.value)
"""
    )

    assert "LPY002" in ids


def test_tracks_critical_action_from_ledge_lang_sdk_import():
    diagnostics = lint_source(
        """
from ledge_lang import sdk
def refund_customer(route): pass
risk = sdk.Uncertain(value="refund", confidence=0.7)
refund_customer(risk)
refund_customer(risk.value)
""",
        "scanner_example.py",
        LintConfig(critical_actions={"refund_customer"}),
    )
    ids = [diagnostic.rule_id for diagnostic in diagnostics]

    assert "LPY002" in ids
    assert ids.count("LPY003") == 2


def test_lint_paths_ignores_generated_directories(tmp_path):
    safe = tmp_path / "safe.py"
    safe.write_text("print('ok')\n", encoding="utf-8")
    ignored_dir = tmp_path / "dist"
    ignored_dir.mkdir()
    ignored = ignored_dir / "unsafe.py"
    ignored.write_text(
        "\n".join(
            [
                "from ledge_lang.sdk import Uncertain",
                "risk = Uncertain(value='x', confidence=0.9)",
                "print(risk.value)",
            ]
        ),
        encoding="utf-8",
    )

    result = lint_paths([tmp_path], LintConfig())

    assert result.files_scanned == 1
    assert result.diagnostics == []
