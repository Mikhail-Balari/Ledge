"""Audit-ready confidence evidence primitives."""

from .calibration import (
    CalibrationOutcome,
    CalibrationReport,
    generate_calibration_report,
    load_outcomes,
)
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
from .report import render_calibration_report, render_confidence_report
from .schema import evaluate_schema
from .scoring import score_evidence

__all__ = [
    "CalibrationOutcome",
    "CalibrationReport",
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
    "generate_calibration_report",
    "hash_bytes",
    "hash_dict",
    "hash_input",
    "hash_output",
    "hash_text",
    "load_outcomes",
    "redacted_summary",
    "render_calibration_report",
    "render_confidence_report",
    "score_evidence",
    "sha256_text",
    "stable_json_dumps",
]
