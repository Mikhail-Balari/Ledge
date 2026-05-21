"""Deterministic adversarial surface tests for parsing and type checking."""

from ledge_lang.typechecker import check_file, check_types


def errors_for(source: str):
    return [issue for issue in check_types(source) if issue.is_error]


def assert_no_internal_crash(source: str):
    issues = check_types(source)
    assert isinstance(issues, list)
    return issues


def assert_has_error(source: str):
    errors = errors_for(source)
    assert errors, "expected at least one checker or syntax error"
    return errors


def test_unusual_unicode_and_control_like_strings_do_not_crash_checker():
    source = 'show "unicode: cafe \u03bb \u2603 zero-width:\u200d controls:\\t\\n raw:\x00\x1f"'
    assert_no_internal_crash(source)


def test_malformed_interpolation_is_treated_as_user_input_not_checker_crash():
    source = '''
define r as classify("invoice") using ["release_payment", "hold_payment"]
show "unfinished interpolation {value_of(r"
show "extra closing brace } is literal text"
'''
    assert_no_internal_crash(source)


def test_value_of_inside_interpolation_is_rejected():
    errors = assert_has_error('''
define r as classify("invoice") using ["release_payment", "hold_payment"]
show "AI decision: {value_of(r)}"
''')
    assert any("value_of" in issue.message for issue in errors)


def test_direct_uncertain_inside_interpolation_is_rejected():
    errors = assert_has_error('''
define r as classify("invoice") using ["release_payment", "hold_payment"]
show "AI decision: {r}"
''')
    assert any("string interpolation" in issue.message for issue in errors)


def test_unsafe_nested_call_argument_is_rejected_beyond_first_position():
    errors = assert_has_error('''
define r as classify("invoice") using ["release_payment", "hold_payment"]
show append(list ["audit"], r)
''')
    assert any("append" in issue.message for issue in errors)


def test_malformed_when_value_of_and_confidence_guards_fail_gracefully():
    malformed_sources = [
        'define r as classify("x") using ["a", "b"]\nshow when(r, , "fallback")',
        'define r as classify("x") using ["a", "b"]\nshow value_of(',
        'define r as classify("x") using ["a", "b"]\nif confidence_of(r) >=:\n    show r',
    ]

    for source in malformed_sources:
        assert_has_error(source)


def test_long_string_does_not_crash_or_hang_checker():
    long_text = "x" * 12000
    assert_no_internal_crash(f'show "{long_text}"')


def test_bom_prefixed_source_still_typechecks(tmp_path):
    path = tmp_path / "bom.ledge"
    path.write_text('show "ok"\n', encoding="utf-8-sig")

    errors = [issue for issue in check_file(str(path)) if issue.is_error]
    assert not errors


def test_braces_escaped_braces_and_interpolation_edges():
    sources = [
        'show "literal \\{brace\\}"',
        'show "empty braces {} are literal enough for the checker"',
        'define x as 2\nshow "computed={x + 3}"',
        'show "nested-looking {str(1 + 2)} text"',
    ]

    for source in sources:
        errors = errors_for(source)
        assert not errors, f"unexpected errors for {source!r}: {errors}"
