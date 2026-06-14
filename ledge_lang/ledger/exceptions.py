"""Exceptions for the decision ledger core."""

from __future__ import annotations


class LedgerError(Exception):
    """Base error for decision ledger failures."""


class LedgerValidationError(LedgerError):
    """Raised when a ledger event or payload fails validation."""


class LedgerHashError(LedgerError):
    """Raised when a ledger event hash is malformed or inconsistent."""


class LedgerStoreError(LedgerError):
    """Raised when a local ledger store cannot be read or written safely."""


class LedgerSequenceError(LedgerStoreError):
    """Raised when ledger sequence or previous-hash continuity is broken."""


class LedgerManifestError(LedgerError):
    """Raised when a ledger manifest is malformed or inconsistent."""


class LedgerExportError(LedgerError):
    """Raised when a local ledger review export cannot be produced safely."""


class LedgerReviewPackError(LedgerError):
    """Raised when an AI-readable ledger review pack cannot be produced safely."""


class LedgerMappingError(LedgerError):
    """Raised when an SDK result cannot be safely mapped into a ledger event."""
