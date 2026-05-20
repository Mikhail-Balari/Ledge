# Run from repo root: python demo_guarantee3.py
import sys; sys.path.insert(0, '.')
from ledge_lang import run
from ledge_lang.ai_types import GLOBAL_AUDIT

# ── Record three AI operations ────────────────────────────────────────────────
run(
    'define r1 as classify("urgent text") using ["urgent","routine"]\n'
    'define r2 as analyze("clause 3.2") using legal\n'
    'define r3 as classify("edge case") using ["yes","no"]',
    output_fn=lambda x: None,
    reset_audit=True
)

print(f"Entries recorded:        {len(GLOBAL_AUDIT._entries)}")
print(f"Chain intact (initial):  {GLOBAL_AUDIT.verify()}")

# ── Tamper: modify confidence of one entry ────────────────────────────────────
original_conf = GLOBAL_AUDIT._entries[0]["confidence"]
GLOBAL_AUDIT._entries[0]["confidence"] = 0.99
print(f"\nAfter modifying confidence[0]: {original_conf} -> 0.99")
print(f"Chain after tamper:            {GLOBAL_AUDIT.verify()}")

# ── Tamper: insert a fake entry ───────────────────────────────────────────────
from ledge_lang.core_types import LedgeMap
GLOBAL_AUDIT._entries[0]["confidence"] = original_conf  # revert
fake = LedgeMap({
    "id": "fake", "operation": "fake_approve", "input_hash": "0" * 16,
    "output_type": "text", "confidence": 1.0, "model": "evil",
    "caller": "attacker", "timestamp": 0.0,
    "prev_hash": GLOBAL_AUDIT._entries[0]["chain_hash"],
    "chain_hash": "f" * 64,
})
GLOBAL_AUDIT._entries.insert(1, fake)
print(f"\nAfter inserting fake entry:    {GLOBAL_AUDIT.verify()}")
print("\nProperty checked: this modification to the log breaks the chain.")
