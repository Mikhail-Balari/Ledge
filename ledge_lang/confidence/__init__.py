"""Audit-ready confidence evidence primitives."""

from .evidence import ConfidenceEvidence, EvidenceSource
from .exceptions import (
    CanonicalSerializationError,
    ConfidenceEvidenceError,
    InvalidEvidenceError,
    InvalidEvidenceScoreError,
    InvalidEvidenceSourceError,
    SchemaEvidenceError,
)
from .hashing import hash_bytes, hash_dict, hash_text, sha256_text, stable_json_dumps
from .redaction import hash_input, hash_output, redacted_summary
from .schema import evaluate_schema

__all__ = [
    "CanonicalSerializationError",
    "ConfidenceEvidence",
    "ConfidenceEvidenceError",
    "EvidenceSource",
    "InvalidEvidenceError",
    "InvalidEvidenceScoreError",
    "InvalidEvidenceSourceError",
    "SchemaEvidenceError",
    "evaluate_schema",
    "hash_bytes",
    "hash_dict",
    "hash_input",
    "hash_output",
    "hash_text",
    "redacted_summary",
    "sha256_text",
    "stable_json_dumps",
]
