"""Exceptions for audit-ready confidence evidence."""


class ConfidenceEvidenceError(Exception):
    """Base class for confidence evidence errors."""


class InvalidEvidenceError(ConfidenceEvidenceError):
    """Raised when a confidence evidence record is invalid."""


class InvalidEvidenceScoreError(ConfidenceEvidenceError):
    """Raised when an evidence score is not a finite number in [0.0, 1.0]."""


class InvalidEvidenceSourceError(ConfidenceEvidenceError):
    """Raised when an evidence source record is invalid."""


class CanonicalSerializationError(ConfidenceEvidenceError):
    """Raised when evidence cannot be serialized deterministically."""


class SchemaEvidenceError(ConfidenceEvidenceError):
    """Raised when schema evidence configuration is invalid."""
