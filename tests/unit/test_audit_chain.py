"""
Cryptographic Audit Chain — pytest test suite

Validates that the SHA-256 chain in AuditTrail detects any tampering.
Every modification to any field of any entry must break verify().
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import pytest
from ledge_lang import run
from ledge_lang.ai_types import AuditTrail, GLOBAL_AUDIT
from ledge_lang.core_types import LedgeMap


# ── Helpers ───────────────────────────────────────────────────────────────────

def fresh_trail(*ops):
    """Create a new AuditTrail and record `ops` (list of operation names)."""
    trail = AuditTrail()
    for op in ops:
        trail.record(op, f"input for {op}", f"output for {op}",
                     model="test-model", confidence=0.9, caller="test")
    return trail


def ledge_run(src, backend=None):
    lines, _ = run(src.strip(), output_fn=lambda x: None, ai_backend=backend,
                   reset_audit=True)
    return lines


# ── Basic chain integrity ─────────────────────────────────────────────────────

class TestChainIntegrity:

    def test_empty_trail_verifies(self):
        trail = AuditTrail()
        assert trail.verify() is True

    def test_single_entry_verifies(self):
        trail = fresh_trail("analyze")
        assert trail.verify() is True

    def test_multi_entry_verifies(self):
        trail = fresh_trail("analyze", "classify", "generate", "ask")
        assert trail.verify() is True

    def test_entries_have_chain_hash(self):
        trail = fresh_trail("analyze")
        entry = trail._entries[0]
        assert "chain_hash" in entry
        assert len(entry["chain_hash"]) == 64  # full SHA-256 hex

    def test_entries_have_prev_hash(self):
        trail = fresh_trail("analyze", "classify")
        assert "prev_hash" in trail._entries[0]
        assert "prev_hash" in trail._entries[1]

    def test_chain_links_correctly(self):
        """Entry N's prev_hash must equal entry N-1's chain_hash."""
        trail = fresh_trail("a", "b", "c")
        assert trail._entries[1]["prev_hash"] == trail._entries[0]["chain_hash"]
        assert trail._entries[2]["prev_hash"] == trail._entries[1]["chain_hash"]

    def test_first_entry_anchors_to_genesis(self):
        trail = fresh_trail("analyze")
        assert trail._entries[0]["prev_hash"] == AuditTrail._GENESIS

    def test_different_entries_have_different_chain_hashes(self):
        trail = fresh_trail("op1", "op2")
        assert trail._entries[0]["chain_hash"] != trail._entries[1]["chain_hash"]


# ── Tampering detection ───────────────────────────────────────────────────────

class TestTamperingDetection:

    def test_modify_operation_breaks_chain(self):
        trail = fresh_trail("analyze", "classify")
        trail._entries[0]["operation"] = "tampered"
        assert trail.verify() is False

    def test_modify_confidence_breaks_chain(self):
        trail = fresh_trail("analyze", "classify")
        trail._entries[0]["confidence"] = 0.0
        assert trail.verify() is False

    def test_modify_model_breaks_chain(self):
        trail = fresh_trail("analyze")
        trail._entries[0]["model"] = "evil-model"
        assert trail.verify() is False

    def test_modify_input_hash_breaks_chain(self):
        trail = fresh_trail("analyze", "classify")
        trail._entries[1]["input_hash"] = "000000000000000"
        assert trail.verify() is False

    def test_modify_chain_hash_itself_breaks_chain(self):
        """Overwriting chain_hash must also break verification of next entry."""
        trail = fresh_trail("a", "b", "c")
        trail._entries[1]["chain_hash"] = "a" * 64
        assert trail.verify() is False

    def test_modify_prev_hash_breaks_chain(self):
        trail = fresh_trail("a", "b")
        trail._entries[1]["prev_hash"] = "b" * 64
        assert trail.verify() is False

    def test_modify_middle_entry_breaks_chain(self):
        """Modifying entry 2 of 5 must invalidate entries 2–5."""
        trail = fresh_trail("a", "b", "c", "d", "e")
        trail._entries[2]["caller"] = "attacker"
        assert trail.verify() is False

    def test_modify_last_entry_breaks_chain(self):
        trail = fresh_trail("a", "b", "c")
        trail._entries[-1]["confidence"] = 0.0001
        assert trail.verify() is False

    def test_inject_entry_breaks_chain(self):
        """Inserting a fake entry in the middle breaks the chain."""
        trail = fresh_trail("a", "b")
        fake = LedgeMap({
            "id": "fake", "operation": "fake_op", "input_hash": "0" * 16,
            "output_type": "text", "confidence": 1.0, "model": "evil",
            "caller": "attacker", "timestamp": 0.0,
            "prev_hash": trail._entries[0]["chain_hash"],
            "chain_hash": "f" * 64,  # wrong hash
        })
        trail._entries.insert(1, fake)
        assert trail.verify() is False

    def test_delete_entry_breaks_chain(self):
        """Removing an entry breaks the link for the entry after it."""
        trail = fresh_trail("a", "b", "c")
        del trail._entries[1]
        assert trail.verify() is False


# ── Ledge builtin audit_verify ───────────────────────────────────────────────

class TestAuditVerifyBuiltin:

    def test_verify_returns_true_after_clean_run(self):
        lines = ledge_run("""
define r as analyze("test") using sentiment
show audit_verify()
""")
        assert lines[-1] == "true"

    def test_verify_returns_true_with_multiple_ops(self):
        lines = ledge_run("""
define a as analyze("x") using sentiment
define b as classify("y") using ["pos","neg"]
define c as generate("z") using text
show audit_verify()
""")
        assert lines[-1] == "true"

    def test_verify_type_is_truth(self):
        lines = ledge_run("show type(audit_verify())")
        assert lines[-1] == "truth"


# ── Python-level tampering demo ───────────────────────────────────────────────

class TestTamperingDemo:
    """
    Shows that the in-memory list can be modified in Python,
    and verify() catches it — but without verify(), nothing does.
    """

    def test_undetected_without_verify(self):
        """Without verify(), a modification silently passes."""
        trail = fresh_trail("analyze")
        trail._entries[0]["operation"] = "tampered"
        # query() returns modified entry without complaint
        results = trail.query()
        assert results[0]["operation"] == "tampered"  # silent corruption

    def test_detected_with_verify(self):
        """With verify(), the same modification is caught."""
        trail = fresh_trail("analyze")
        trail._entries[0]["operation"] = "tampered"
        assert trail.verify() is False

    def test_chain_survives_many_entries(self):
        trail = AuditTrail()
        for i in range(100):
            trail.record("op", f"input_{i}", f"output_{i}",
                         confidence=0.5 + (i % 5) * 0.1)
        assert trail.verify() is True
        # Now tamper somewhere in the middle
        trail._entries[50]["confidence"] = 0.0
        assert trail.verify() is False
