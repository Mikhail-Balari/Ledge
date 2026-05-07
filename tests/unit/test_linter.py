"""
Linter Tests — Ledge v1.0.0
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from ledge_lang.linter import lint


def has_code(src, code):
    return any(i.code == code for i in lint(src))

def no_errors(src):
    return all(i.kind != "error" for i in lint(src))


class TestLinterAINative:

    def test_E001_uncertain_in_unsafe_fn(self):
        src = 'define r as analyze("x") using y\nshow upper(r)'
        assert has_code(src, "E001")

    def test_E001_not_triggered_for_when(self):
        src = 'define r as analyze("x") using y\nshow when(r, 0.8, "default")'
        assert no_errors(src)

    def test_E001_not_triggered_for_confidence_of(self):
        src = 'define r as analyze("x") using y\nshow confidence_of(r)'
        assert no_errors(src)

    def test_E001_not_triggered_after_is_confident_guard(self):
        src = 'define r as analyze("x") using y\nif is_confident(r):\n    show value_of(r)'
        assert no_errors(src)

    def test_W011_fn_with_ai_no_requires(self):
        src = 'define f(t: text):\n    return classify(t) using ["a", "b"]'
        assert has_code(src, "W011")

    def test_W011_not_triggered_when_requires_present(self):
        src = """define f(t: text):
    requires:
        len(t) > 0
    return classify(t) using ["a", "b"]"""
        w011 = [i for i in lint(src) if i.code == "W011"]
        assert len(w011) == 0


class TestLinterStyle:

    def test_S022_unused_variable(self):
        src = "define x as 42\nshow 1"
        assert has_code(src, "S022")

    def test_S022_not_triggered_when_used(self):
        src = "define x as 42\nshow x"
        s022 = [i for i in lint(src) if i.code == "S022"]
        assert len(s022) == 0

    def test_clean_program_no_errors(self):
        src = "define x as 10\ndefine y as 20\nshow x + y"
        errors = [i for i in lint(src) if i.kind == "error"]
        assert len(errors) == 0


class TestLinterOutput:

    def test_issue_has_code(self):
        src = 'define r as analyze("x") using y\nshow upper(r)'
        issues = lint(src)
        assert len(issues) > 0
        assert any(i.code.startswith(("E", "W", "S")) for i in issues)

    def test_issue_has_suggestion(self):
        src = 'define r as analyze("x") using y\nshow upper(r)'
        e001 = [i for i in lint(src) if i.code == "E001"]
        assert e001
        assert e001[0].suggestion

    def test_issue_str_readable(self):
        src = 'define r as analyze("x") using y\nshow upper(r)'
        e001 = next(i for i in lint(src) if i.code == "E001")
        text = str(e001)
        assert "E001" in text
