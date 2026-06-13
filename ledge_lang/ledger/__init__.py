"""Tamper-evident decision ledger core primitives."""

from .canonical import canonical_json
from .event import DecisionEvent
from .exceptions import (
    LedgerError,
    LedgerHashError,
    LedgerManifestError,
    LedgerSequenceError,
    LedgerStoreError,
    LedgerValidationError,
)
from .hashing import compute_event_hash, verify_event_hash
from .manifest import LedgerManifest, build_manifest, read_manifest, write_manifest
from .store import DecisionLedger
from .verifier import LedgerFinding, LedgerVerificationResult, LedgerVerifier, verify_ledger

__all__ = [
    "DecisionEvent",
    "DecisionLedger",
    "LedgerManifest",
    "LedgerFinding",
    "LedgerVerificationResult",
    "LedgerVerifier",
    "LedgerError",
    "LedgerValidationError",
    "LedgerHashError",
    "LedgerStoreError",
    "LedgerSequenceError",
    "LedgerManifestError",
    "canonical_json",
    "compute_event_hash",
    "verify_event_hash",
    "build_manifest",
    "write_manifest",
    "read_manifest",
    "verify_ledger",
]
