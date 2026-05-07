"""
Typechecker tests — verifies AI-native type safety enforcement
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from ledge_lang.typechecker import check_types, Issue


def has_error(src):
    issues = check_types(src)
    return any(i.is_error for i in issues)

def has_warning(src):
    issues = check_types(src)
    return any(i.is_warning for i in issues)

def clean(src):
    issues = check_types(src)
    errors = [i for i in issues if i.is_error]
    assert not errors, f"Expected no errors, got: {[str(e) for e in errors]}"


class TestUncertainEnforcement:
    """Uncertain[T] must not be usable as T without extraction."""

    def test_ai_result_in_typed_var_is_error(self):
        assert has_error('define name: text as analyze("hi") using sentiment')

    def test_ai_result_passed_to_upper_is_error(self):
        assert has_error('''
define r as analyze("hi") using sentiment
show upper(r)
''')

    def test_ai_result_in_number_var_is_error(self):
        assert has_error('define n: number as classify("x") using ["a","b"]')

    def test_show_uncertain_directly_is_error(self):
        assert has_error('define r as analyze("x") using y\nshow r')

    def test_when_extraction_is_safe(self):
        clean('define r as analyze("x") using y\nshow when(r, 0.8, "default")')

    def test_confidence_of_is_safe(self):
        clean('define r as analyze("x") using y\nshow confidence_of(r)')

    def test_value_of_is_safe(self):
        clean('define r as analyze("x") using y\nshow value_of(r)')

    def test_is_confident_is_safe(self):
        clean('define r as analyze("x") using y\nshow is_confident(r)')

    def test_is_uncertain_is_safe(self):
        clean('define r as analyze("x") using y\nshow is_uncertain(r)')

    def test_set_uncertain_to_typed_var_is_error(self):
        assert has_error('''
define x: text as "hello"
define r as analyze("x") using y
set x to r
''')


class TestTypeAnnotations:
    """Standard type annotation checking."""

    def test_number_string_mismatch_error(self):
        # Type mismatch on concrete types is an ERROR (aligned with runtime behavior)
        assert has_error('define x: number as "hello"')

    def test_text_number_mismatch_error(self):
        # Type mismatch on concrete types is an ERROR (aligned with runtime behavior)
        assert has_error('define x: text as 42')

    def test_number_number_clean(self):
        clean('define x: number as 42')

    def test_text_text_clean(self):
        clean('define x: text as "hello"')

    def test_any_accepts_all(self):
        clean('define x: any as 42')
        clean('define x: any as "hello"')
        clean('define x: any as true')

    def test_set_wrong_type_is_error(self):
        assert has_error('define x: number as 1\nset x to "string"')

    def test_set_same_type_clean(self):
        clean('define x: number as 1\nset x to 2')

    def test_nothing_always_compatible(self):
        clean('define x: number as nothing')


class TestIssueStructure:
    """Issues must have useful information for developers."""

    def test_error_has_line(self):
        issues = check_types('define x: number as "bad"')
        errors = [i for i in issues if i.is_error or i.is_warning]
        assert any(i.line >= 0 for i in errors)

    def test_ai_error_has_suggestion(self):
        issues = check_types('define name: text as analyze("hi") using sentiment')
        errors = [i for i in issues if i.is_error]
        assert errors, "Expected errors"
        assert any(i.suggestion for i in errors), "Errors must include suggestions"

    def test_unsafe_uncertain_has_suggestion(self):
        issues = check_types('''
define r as analyze("hi") using sentiment
show upper(r)
''')
        errors = [i for i in issues if i.is_error]
        assert any(i.suggestion for i in errors)


class TestListUncertain:
    """map() with AI-producing lambda yields list[uncertain] — iterating without check is ERROR."""

    def test_map_classify_unsafe_show_is_error(self):
        assert has_error('''
define items as list ["a", "b"]
define results as map(items, given x: classify(x) using ["pos","neg"])
for each item in results:
    show item
''')

    def test_map_analyze_unsafe_show_is_error(self):
        assert has_error('''
define items as list ["a", "b"]
define results as map(items, given x: analyze(x) using sentiment)
for each item in results:
    show item
''')

    def test_map_classify_confidence_of_is_safe(self):
        clean('''
define items as list ["a", "b"]
define results as map(items, given x: classify(x) using ["pos","neg"])
for each item in results:
    show confidence_of(item)
''')

    def test_map_classify_value_of_is_safe(self):
        clean('''
define items as list ["a", "b"]
define results as map(items, given x: classify(x) using ["pos","neg"])
for each item in results:
    show value_of(item)
''')

    def test_map_non_ai_lambda_is_safe(self):
        clean('''
define items as list [1, 2, 3]
define results as map(items, given x: x + 1)
for each item in results:
    show item
''')


class TestConfidenceAlias:
    """define c as confidence_of(r) enables narrowing via if c >= 0.85:"""

    def test_alias_guard_narrows_uncertain_in_if(self):
        clean('''
define r as analyze("x") using y
define c as confidence_of(r)
if c >= 0.85:
    show r
''')

    def test_alias_defined_but_no_guard_still_errors(self):
        assert has_error('''
define r as analyze("x") using y
define c as confidence_of(r)
show r
''')

    def test_alias_classify_narrows(self):
        clean('''
define r as classify("x") using ["a","b"]
define conf as confidence_of(r)
if conf >= 0.80:
    show r
''')

    def test_direct_confidence_check_still_works(self):
        clean('''
define r as analyze("x") using y
if confidence_of(r) >= 0.85:
    show r
''')

    def test_alias_guard_does_not_narrow_outside_if(self):
        assert has_error('''
define r as analyze("x") using y
define c as confidence_of(r)
if c >= 0.85:
    show r
show r
''')
