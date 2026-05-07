"""
Ledge AI Mock Fixtures
=======================
Provides deterministic AI responses for testing.
Use instead of real AI backends so tests never depend on network or randomness.

Usage:
    from tests.fixtures.ai_mocks import SENTIMENT_BACKEND, CLASSIFIER_BACKEND
    
    lines, _ = run(source, ai_backend=SENTIMENT_BACKEND)
    # All AI calls return deterministic, high-confidence results
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from ledge_lang.core_types import LedgeMap, NOTHING
from ledge_lang.ai_types import Uncertain


def _make_uncertain(value, confidence=0.9, source="mock"):
    return Uncertain(value, confidence, source=source)


# ── Sentiment analysis mock ──────────────────────────────────────────────────
def _sentiment_analyze(text, mode):
    """Returns deterministic sentiment based on keywords."""
    text_lower = str(text).lower()
    if any(w in text_lower for w in ["great", "good", "excellent", "love", "wonderful"]):
        return LedgeMap({"sentiment": "positive", "score": 0.9})
    elif any(w in text_lower for w in ["bad", "terrible", "awful", "hate", "worst"]):
        return LedgeMap({"sentiment": "negative", "score": 0.85})
    else:
        return LedgeMap({"sentiment": "neutral", "score": 0.7})

def _sentiment_classify(text, labels):
    """Classify text into first label if positive sentiment."""
    text_lower = str(text).lower()
    if any(w in text_lower for w in ["great", "good", "excellent"]):
        return str(labels[0]) if labels else "positive"
    return str(labels[-1]) if labels else "negative"

SENTIMENT_BACKEND = {
    "analyze": lambda text, mode: _sentiment_analyze(text, mode),
    "classify": lambda text, labels: _sentiment_classify(text, labels),
    "generate": lambda prompt, mode: f"[MOCK] Response to: {str(prompt)[:50]}",
    "ask": lambda question: f"[MOCK] Answer to: {str(question)[:50]}",
    "embed": lambda text: [0.1, 0.2, 0.3, 0.4, 0.5],  # 5-dim mock embedding
}


# ── Classification mock ──────────────────────────────────────────────────────
def _classify_by_keywords(text, labels):
    """Deterministic keyword-based classifier."""
    text_lower = str(text).lower()
    rules = {
        "urgent": ["urgent", "critical", "emergency", "asap", "immediately"],
        "spam":   ["buy now", "limited offer", "click here", "free money"],
        "medical": ["pain", "symptoms", "diagnosis", "treatment", "doctor"],
        "positive": ["great", "good", "excellent", "wonderful", "amazing"],
        "negative": ["bad", "terrible", "awful", "horrible", "worst"],
    }
    for label in labels:
        label_str = str(label).lower()
        if label_str in rules:
            if any(kw in text_lower for kw in rules[label_str]):
                return label
        elif label_str in text_lower:
            return label
    return labels[0] if labels else "unknown"

CLASSIFIER_BACKEND = {
    "analyze": lambda text, mode: LedgeMap({"classification": _classify_by_keywords(text, ["pos", "neg"]), "confidence": 0.88}),
    "classify": _classify_by_keywords,
    "generate": lambda prompt, mode: f"Generated: {str(prompt)[:30]}",
    "ask": lambda q: f"Answer: {str(q)[:30]}",
    "embed": lambda text: [float(ord(c)) / 1000.0 for c in str(text)[:5]],
}


# ── Minimal mock (lowest possible confidence that still works) ────────────────
MINIMAL_MOCK = {
    "analyze": lambda text, mode: LedgeMap({"result": "unknown"}),
    "classify": lambda text, labels: labels[0] if labels else "unknown",
    "generate": lambda prompt, mode: "mock output",
    "ask": lambda q: "mock answer",
    "embed": lambda text: [0.0],
}


# ── Test helpers ─────────────────────────────────────────────────────────────
def run_with_sentiment(source, output_fn=None):
    """Run Ledge program with deterministic sentiment backend."""
    from ledge_lang import run
    return run(source, output_fn=output_fn, ai_backend=SENTIMENT_BACKEND)

def run_with_classifier(source, output_fn=None):
    """Run Ledge program with deterministic classifier backend."""
    from ledge_lang import run
    return run(source, output_fn=output_fn, ai_backend=CLASSIFIER_BACKEND)
