"""Hashing helpers for canonical decision ledger events."""

from __future__ import annotations

import hashlib
import hmac
from collections.abc import Mapping
from typing import Any

from .canonical import canonical_json


EVENT_HASH_DOMAIN = "ledge-decision-event-v1:"
CURRENT_EVENT_HASH_FIELD = "current_event_hash"


def compute_event_hash(event_payload_without_current_hash: Mapping[str, Any]) -> str:
    """Compute the SHA-256 hash for a decision event payload."""
    payload = {
        key: value
        for key, value in event_payload_without_current_hash.items()
        if key != CURRENT_EVENT_HASH_FIELD
    }
    encoded = (EVENT_HASH_DOMAIN + canonical_json(payload)).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def verify_event_hash(event: Mapping[str, Any]) -> bool:
    """Return whether an event's stored current hash matches its canonical hash."""
    if not isinstance(event, Mapping):
        return False

    current_hash = event.get(CURRENT_EVENT_HASH_FIELD)
    if not isinstance(current_hash, str):
        return False
    try:
        expected_hash = compute_event_hash(event)
    except Exception:
        return False
    return hmac.compare_digest(current_hash, expected_hash)
