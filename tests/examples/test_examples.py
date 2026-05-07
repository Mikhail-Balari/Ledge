"""
Example files — all must run green in CI.
If an example fails, it's a bug — not a test problem.
"""
import sys, os, glob
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from ledge_lang import run, compile_ledge
from ledge_lang.interpreter import LedgeError
from ledge_lang.lexer import LexError
from ledge_lang.parser import ParseError

EXAMPLES_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'examples')


def test_all_examples_parse():
    """Every .ledge example must parse without errors."""
    examples = glob.glob(os.path.join(EXAMPLES_DIR, '*.ledge'))
    assert len(examples) > 0, "No examples found"
    for path in examples:
        with open(path) as f:
            src = f.read()
        try:
            compile_ledge(src)
        except (LexError, ParseError) as e:
            assert False, f"{os.path.basename(path)}: parse error: {e}"


def test_tour_runs():
    """The tour example must run completely."""
    with open(os.path.join(EXAMPLES_DIR, 'tour.ledge')) as f:
        src = f.read()
    lines, _ = run(src, output_fn=lambda x: None)
    assert len(lines) > 10, "Tour produced very little output"


def test_industrial_sensors_runs():
    """Industrial sensors example must produce correct output."""
    with open(os.path.join(EXAMPLES_DIR, 'industrial_sensors.ledge')) as f:
        src = f.read()
    lines, _ = run(src, output_fn=lambda x: None)
    output = "\n".join(lines)
    assert "Sensor Report" in output
    assert "Alerts:" in output
    assert "Warnings:" in output


def test_industrial_sensors_no_false_ai_confidence():
    """
    CRITICAL: When AI has no backend, the example must NOT claim
    high confidence. It must show 0 or 'not confident'.
    """
    with open(os.path.join(EXAMPLES_DIR, 'industrial_sensors.ledge')) as f:
        src = f.read()
    lines, _ = run(src, output_fn=lambda x: None)
    output = "\n".join(lines)
    # Must NOT show confidence "1" — that would be fake confidence
    assert "confidence: 1" not in output.lower(), \
        "Example shows fake AI confidence = 1 without real backend"


def test_universal_deploy_runs():
    """Universal deploy example must complete without errors."""
    with open(os.path.join(EXAMPLES_DIR, 'universal_deploy.ledge')) as f:
        src = f.read()
    lines, _ = run(src, output_fn=lambda x: None)
    output = "\n".join(lines)
    assert "Classifier" in output
    assert "Classified" in output or "Processed" in output


def test_universal_deploy_no_false_confidence():
    """
    CRITICAL: The classifier example must NOT show high-confidence
    results without a real AI backend.
    """
    with open(os.path.join(EXAMPLES_DIR, 'universal_deploy.ledge')) as f:
        src = f.read()
    lines, _ = run(src, output_fn=lambda x: None)
    
    # The confidence bar should be empty (0 confidence = no blocks)
    # Previously this showed "████████" (8 blocks) — fake confidence
    for line in lines:
        if "positive" in line or "negative" in line or "neutral" in line:
            # Line has a label — check it doesn't have fake confidence blocks
            # With 0 confidence: bar should be empty or very short
            block_count = line.count("█")
            assert block_count == 0, \
                f"Fake confidence shown: '{line}' has {block_count} confidence blocks without AI backend"
