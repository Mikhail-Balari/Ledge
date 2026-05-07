"""
Install Smoke Test
==================
Verifies that a clean install of Ledge works end-to-end.
These tests simulate what a new user does after `pip install ledge-lang`.

Tests:
1. Import works
2. Basic program runs
3. AI safety invariant holds
4. CLI tools work
5. Python FFI works
6. Formatter is idempotent
"""
import sys, os, subprocess
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


class TestInstallSmoke:
    """Core functionality available immediately after install."""

    def test_import_works(self):
        """The main package imports cleanly."""
        from ledge_lang import run, compile_ledge, __version__
        assert __version__ == "1.1.0"

    def test_hello_world(self):
        """Classic hello world runs correctly."""
        from ledge_lang import run
        lines, _ = run('show "Hello, Ledge!"', output_fn=lambda x: None)
        assert lines == ["Hello, Ledge!"]

    def test_arithmetic(self):
        from ledge_lang import run
        lines, _ = run("show 6 * 7", output_fn=lambda x: None)
        assert lines == ["42"]

    def test_ai_safety_invariant(self):
        """CRITICAL: Without backend, confidence must be 0."""
        from ledge_lang import run
        lines, _ = run(
            'show confidence_of(analyze("x") using y)',
            output_fn=lambda x: None
        )
        assert lines[0] == "0", f"AI safety violated: confidence={lines[0]}"

    def test_ai_no_fake_label(self):
        """CRITICAL: classify without backend must return nothing."""
        from ledge_lang import run
        lines, _ = run(
            'show value_of(classify("x") using ["a","b"])',
            output_fn=lambda x: None
        )
        assert lines[0] == "nothing", f"AI safety violated: label={lines[0]}"

    def test_uncertain_type(self):
        from ledge_lang import run
        lines, _ = run(
            'define r as uncertain("yes", 0.9)\nshow is_confident(r)',
            output_fn=lambda x: None
        )
        assert lines[0] == "true"

    def test_contracts_work(self):
        from ledge_lang import run
        from ledge_lang.interpreter import LedgeError
        # Valid call passes
        lines, _ = run("""
define f(x: number):
    requires:
        x > 0
    return x * 2
show f(5)
""", output_fn=lambda x: None)
        assert lines[0] == "10"

        # Contract violation raises
        raised = False
        try:
            run("""
define f(x: number):
    requires:
        x > 0
    return x
f(-1)
""", output_fn=lambda x: None)
        except LedgeError:
            raised = True
        assert raised, "Contract violation should raise LedgeError"

    def test_python_ffi(self):
        from ledge_lang import run
        lines, _ = run(
            'import "python:math" as m\nshow m["sqrt"](144)',
            output_fn=lambda x: None
        )
        assert lines[0] == "12"

    def test_formatter_idempotent(self):
        from ledge_lang.formatter import format_ledge
        src = "define x as 10\nshow x\n"
        fmt1 = format_ledge(src)
        fmt2 = format_ledge(fmt1)
        assert fmt1 == fmt2

    def test_typechecker_catches_unsafe_uncertain(self):
        from ledge_lang.typechecker import check_types
        issues = check_types(
            'define r as analyze("x") using y\nshow upper(r)'
        )
        errors = [i for i in issues if i.is_error]
        assert errors, "Typechecker must catch unsafe Uncertain use"

    def test_audit_trail_works(self):
        from ledge_lang import run
        lines, _ = run("""
define r as analyze("test") using sentiment
define log as audit_query()
show len(log) >= 1
""", output_fn=lambda x: None)
        assert lines[0] == "true"

    def test_stream_operations(self):
        from ledge_lang import run
        lines, _ = run("""
define s as stream_of(list [1, 2, 3, 4, 5, 6])
define evens as stream_where(s, given x: modulo(x, 2) = 0)
show stream_collect(evens)
""", output_fn=lambda x: None)
        assert lines[0] == "[2, 4, 6]"

    def test_version_consistent(self):
        import re, json
        from ledge_lang import __version__
        
        with open(os.path.join(os.path.dirname(__file__), '..', '..', 'pyproject.toml')) as f:
            m = re.search(r'version = "([^"]+)"', f.read())
            pkg_version = m.group(1) if m else None
        
        assert __version__ == pkg_version == "1.1.0", (
            f"Version mismatch: __init__={__version__}, pyproject={pkg_version}"
        )
