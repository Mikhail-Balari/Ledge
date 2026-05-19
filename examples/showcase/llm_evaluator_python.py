"""
LLM evaluator - Python version without Ledge's checked patterns.
Demonstrates how calibration can fail silently.
"""


def evaluate_python(question, expected_answer, ai_fn):
    """Python version: can accept answers with any confidence."""
    result = ai_fn(question)

    # PROBLEM 1: the developer can forget to check confidence
    # The AI can answer "Paris" with confidence=0.1 and the code counts it anyway
    answer = result.get("answer", "")
    correct = answer.strip().lower() == expected_answer.strip().lower()
    return correct


def evaluate_python_with_calibration_bug(questions, ai_fn):
    """
    Calibration bug: counts ALL answers, even low-confidence ones.
    The LLM may be guessing, but the code counts it as a valid answer.
    """
    correct = 0
    total = 0

    for question, expected in questions:
        result = ai_fn(question)

        # PROBLEM 2: nothing forces confidence to be checked
        # This code is written "in good faith" but is incorrect
        answer = result.get("answer", "")
        if answer.lower() == expected.lower():
            correct += 1
        total += 1

    # Reports 80% accuracy but the LLM was actually
    # guessing in 40% of cases with confidence < 0.5
    return correct / total if total else 0


def evaluate_python_correct(questions, ai_fn, min_confidence=0.5):
    """
    Python version that tries to mirror Ledge's checked pattern.
    But: depends on the developer remembering to include it.
    """
    correct = 0
    counted = 0

    for question, expected in questions:
        result = ai_fn(question)
        if result is None:
            continue
        conf = result.get("confidence", 0)  # may not exist
        if conf < min_confidence:
            continue  # easy to forget

        answer = result.get("answer", "")
        if answer.lower() == expected.lower():
            correct += 1
        counted += 1

    return correct / counted if counted else 0


# Contrast:
# - In Ledge, `analyze()` ALWAYS returns Uncertain[T].
#   The developer CANNOT access the value without deciding what to do with confidence.
# - In Python, `result.get("confidence", 0)` is optional.
#   A typo ("confience") returns 0 silently and excludes all answers.
# - In Ledge, the confidence filter is part of the type, not the application code.
