"""
Ledge with real OpenAI backend.

Runs examples/showcase/medical_triage.ledge with a real OpenAI model
and shows the difference between confidence=0 (without backend) and
real model confidences.

Usage:
    export OPENAI_API_KEY=sk-...
    python examples/showcase/real_backend.py

Without API key, the script prints instructions and exits cleanly.
"""

import sys
import os

# ── 1. Check API key ──────────────────────────────────────────────────────────

api_key = os.environ.get("OPENAI_API_KEY")

if not api_key:
    print("OPENAI_API_KEY not found.")
    print()
    print("To test Ledge with a real model:")
    print()
    print("  1. Create an account at https://platform.openai.com")
    print("  2. Generate an API key at https://platform.openai.com/api-keys")
    print("  3. Install the OpenAI client:")
    print("       pip install openai")
    print("  4. Export the key in your terminal:")
    print("       export OPENAI_API_KEY=sk-...")        # bash/zsh
    print("       $env:OPENAI_API_KEY='sk-...'", "     # PowerShell")
    print("  5. Run this script again:")
    print("       python examples/showcase/real_backend.py")
    print()
    print("Alternative: pass the key directly (not recommended):")
    print("  OPENAI_API_KEY=sk-... python examples/showcase/real_backend.py")
    print()
    print("Without API key, all Ledge showcases still work —")
    print("but with confidence=0 and safe failure by design.")
    sys.exit(0)

# ── 2. Check dependencies ─────────────────────────────────────────────────────

try:
    import openai as _openai_check
except ImportError:
    print("Missing openai package.")
    print("Install with:  pip install openai")
    sys.exit(1)

# ── 3. Setup ──────────────────────────────────────────────────────────────────

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from ledge_lang import run
from ledge_lang.ai_types import GLOBAL_AUDIT
from ledge_lang.backends import openai_backend

SHOWCASE = os.path.join(os.path.dirname(__file__), 'medical_triage.ledge')

with open(SHOWCASE, encoding='utf-8') as f:
    src = f.read()

# ── 4. Run WITHOUT backend (baseline) ─────────────────────────────────────────

print("=" * 60)
print("WITHOUT BACKEND (baseline — confidence=0 guaranteed)")
print("=" * 60)

lines_without, _ = run(src, output_fn=lambda x: None, reset_audit=True)
for l in lines_without:
    print(f"  {l}")

escalated_without = sum(1 for l in lines_without if 'ESCALATE' in l)
print(f"\n  → {escalated_without}/3 patients escalated to human (confidence=0)")

# ── 5. Create real backend ─────────────────────────────────────────────────────

print()
print("=" * 60)
print("WITH REAL OPENAI BACKEND (gpt-4o-mini)")
print("=" * 60)
print(f"  API key: {api_key[:8]}...{api_key[-4:]}")
print()

try:
    backend = openai_backend(api_key=api_key, model="gpt-4o-mini")
except Exception as e:
    print(f"Error creating backend: {e}")
    sys.exit(1)

# ── 6. Run WITH backend ───────────────────────────────────────────────────────

output_lines = []

def capture(line):
    output_lines.append(line)

print("Running medical triage with real AI...")
print("(each patient makes a real call to OpenAI)")
print()

try:
    lines_with, _ = run(
        src,
        output_fn=capture,
        ai_backend=backend,
        reset_audit=True,
    )
except Exception as e:
    print(f"Error during execution: {e}")
    sys.exit(1)

for l in lines_with:
    print(f"  {l}")

# ── 7. Compare results ────────────────────────────────────────────────────────

print()
print("=" * 60)
print("COMPARISON")
print("=" * 60)

escalated_with  = sum(1 for l in lines_with    if 'ESCALATE' in l)
urgent_with     = sum(1 for l in lines_with    if 'URGENT'   in l)
routine_with    = sum(1 for l in lines_with    if 'ROUTINE'  in l)
escalated_without_b = sum(1 for l in lines_without if 'ESCALATE' in l)

print(f"  Without backend:  {escalated_without_b}/3 escalated (confidence=0, none classified)")
print(f"  With backend:     {escalated_with}/3 escalated | {urgent_with} urgent | {routine_with} routine")
print()
print("  Key difference: with a real backend, the model analyzes")
print("  symptoms and can classify patients with confidence > 0.")
print("  Without backend, Ledge guarantees safe failure: nobody is classified.")

# ── 8. Verify audit trail ─────────────────────────────────────────────────────

print()
print("=" * 60)
print("AUDIT TRAIL")
print("=" * 60)

entries = len(GLOBAL_AUDIT._entries)
chain_ok = GLOBAL_AUDIT.verify()

print(f"  Entries recorded: {entries}")
print(f"  Cryptographic chain: {'intact ✓' if chain_ok else 'COMPROMISED ✗'}")

if entries > 0:
    print()
    print("  First log entries:")
    for i, entry in enumerate(GLOBAL_AUDIT._entries[:3]):
        print(f"    [{i+1}] op={entry['operation']}"
              f"  input_hash={entry['input_hash']}"
              f"  confidence={entry['confidence']:.2f}")

print()
if chain_ok:
    print("  Guarantee verified: all AI decisions are recorded")
    print("  and the cryptographic chain is intact.")
else:
    print("  WARNING: the chain was compromised.")
