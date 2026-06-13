"""Exceptions for the decision ledger core."""

from __future__ import annotations


class LedgerError(Exception):
    """Base error for decision ledger failures."""


class LedgerValidationError(LedgerError):
    """Raised when a ledger event or payload fails validation."""


class LedgerHashError(LedgerError):
    """Raised when a ledger event hash is malformed or inconsistent."""
