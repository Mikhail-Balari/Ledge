"""Audit-ready confidence evidence primitives."""

from .evidence import ConfidenceEvidence, EvidenceSource
from .ensemble import evaluate_ensemble
from .exceptions import (
    CanonicalSerializationError,
    ConfidenceEvidenceError,
    InvalidEvidenceError,
    InvalidEvidenceScoreError,
    InvalidEvidenceSourceError,
    SchemaEvidenceError,
)
from .hashing import hash_bytes, hash_dict, hash_text, sha256_text, stable_json_dumps
from .logprobs import extract_logprob_signal
from .redaction import hash_input, hash_output, redacted_summary
from .schema import evaluate_schema
from .scoring import score_evidence

__all__ = [
    "CanonicalSerializationError",
    "ConfidenceEvidence",
    "ConfidenceEvidenceError",
    "EvidenceSource",
    "InvalidEvidenceError",
    "InvalidEvidenceScoreError",
    "InvalidEvidenceSourceError",
    "SchemaEvidenceError",
    "evaluate_ensemble",
    "evaluate_schema",
    "extract_logprob_signal",
    "hash_bytes",
    "hash_dict",
    "hash_input",
    "hash_output",
    "hash_text",
    "redacted_summary",
    "score_evidence",
    "sha256_text",
    "stable_json_dumps",
]
