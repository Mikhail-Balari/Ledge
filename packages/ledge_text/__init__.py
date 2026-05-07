"""
ledge_text — Text processing for Ledge AI pipelines
=====================================================
Tokenization, chunking, and text utilities for AI workflows.

Usage:
    import "python:ledge_text" as text
    define chunks as text["chunk"](long_document, 500)
    for each chunk in chunks:
        define result as analyze(chunk) using sentiment
"""
import re

LEDGE_PACKAGE = "ledge_text"
VERSION = "1.0.0"

def chunk(text, max_words=500):
    """Split text into chunks of max_words words."""
    words = text.split()
    return [' '.join(words[i:i+max_words]) for i in range(0, len(words), max_words)]

def tokenize(text):
    """Simple word tokenization."""
    return re.findall(r'\\b\\w+\\b', text.lower())

def clean(text):
    """Remove extra whitespace and normalize."""
    return ' '.join(text.split())

def truncate(text, max_chars=200, suffix="..."):
    """Truncate text to max_chars."""
    if len(text) <= max_chars:
        return text
    return text[:max_chars-len(suffix)] + suffix

def word_count(text):
    """Count words in text."""
    return len(text.split())

def sentences(text):
    """Split text into sentences."""
    return [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]
