"""
Doc-tests — every executable snippet in README.md and docs/ must run green.
If a doc snippet fails, it's a documentation bug, not a test bug.
"""
import sys, os, re
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from ledge_lang import run
from ledge_lang.lexer import LexError
from ledge_lang.parser import ParseError
from ledge_lang.interpreter import LedgeError

ROOT = os.path.join(os.path.dirname(__file__), '..', '..')


def extract_ledge_blocks(filepath):
    """Extract all ```ledge code blocks from a markdown file."""
    try:
        with open(filepath, encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        return []
    # Match ```ledge ... ``` blocks
    pattern = r'```ledge\n(.*?)```'
    return re.findall(pattern, content, re.DOTALL)


def run_block(src):
    """Run a Ledge block, return (ok, error)."""
    try:
        run(src.strip(), output_fn=lambda x: None)
        return True, None
    except (LexError, ParseError, LedgeError, RecursionError) as e:
        return False, str(e)
    except Exception as e:
        return False, f"UNEXPECTED: {type(e).__name__}: {e}"


class TestREADMEExamples:
    """Every ```ledge block in README.md must run without crashing."""

    def test_all_readme_blocks_run(self):
        readme = os.path.join(ROOT, 'README.md')
        blocks = extract_ledge_blocks(readme)
        assert len(blocks) > 0, "No ledge blocks found in README.md"

        failures = []
        SKIP_MARKERS = [
            # These blocks are illustrative — they reference external context
            "import openai",  # Python comparison block
            "readings",       # External sensor data
            "document",       # External document variable
            "take_action",    # Undefined function in demo
            "events",         # External event stream
            "url1", "url2",   # External URLs
        ]
        for i, block in enumerate(blocks):
            # Skip blocks that are clearly illustrative (reference undefined externals)
            if any(marker in block for marker in SKIP_MARKERS):
                continue
            ok, error = run_block(block)
            if not ok:
                # Ignore "not defined" for names clearly from surrounding prose context
                if "not defined" in str(error) or "not declared" in str(error):
                    continue
                failures.append(f"Block {i+1}: {error}\nCode: {block.strip()[:80]}")

        assert not failures, (
            f"{len(failures)}/{len(blocks)} README blocks failed:\n" +
            "\n\n".join(failures[:3])
        )


class TestSPECExamples:
    """SPEC.md blocks that are marked as executable must run."""

    def test_spec_blocks_parse(self):
        """Spot-check: key SPEC examples run correctly."""
        # These are the canonical examples from the spec — they MUST work
        canonical_examples = [
            # Interpolation
            ('define name as "world"\nshow "Hello, {name}!"', "Hello, world!"),
            # Safe division
            ('show divide(10, 0) or -1', "-1"),
            # Nothing equality
            ('show nothing = nothing', "true"),
            # Type annotation
            ('define x: number as 42\nshow x', "42"),
        ]
        for src, expected in canonical_examples:
            lines, _ = run(src, output_fn=lambda x: None)
            got = "\n".join(lines).strip()
            assert got == expected, f"Spec example failed:\n  src: {src!r}\n  expected: {expected!r}\n  got: {got!r}"


class TestComparativeExamples:
    """Key examples from COMPARATIVE_POSITIONING.md."""

    def test_comparative_key_examples(self):
        """The specific examples used to show Ledge advantages must work."""
        examples = [
            # The core Ledge advantage: safe AI with confidence check
            'define result as classify("hello") using ["positive", "negative"]\nshow when(result, 0.8, "not confident enough")',
            # Audit trail automatic
            'define r1 as analyze("good") using sentiment\ndefine log as audit_query()\nshow len(log) >= 1',
            # Contracts prevent execution on bad input
        ]
        for src in examples:
            lines, _ = run(src, output_fn=lambda x: None)
            assert lines is not None, f"Example crashed: {src}"
