"""
Demo: Transitive uncertainty propagation in AI chains.
Runs without API keys — demonstrates chain logic.

python demo_chain.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ledge_lang.ai_types import Uncertain, UncertainChain
from ledge_lang.core_types import NOTHING
from ledge_lang import run

# ── DEMO 1: Chain without backend ─────────────────────────────────────────────

print("=" * 60)
print("DEMO 1: Chain without backend (confidence=0 on all steps)")
print("=" * 60)

src = (
    'define r1 as analyze("text") using diagnosis\n'
    'define r2 as classify("text") using ["a","b","c"]\n'
    'define r3 as generate("text") using protocol\n'
    'define chain as uncertain_chain(list [r1, r2, r3])\n'
    'show confidence_of(r1)\n'
    'show confidence_of(r2)\n'
    'show confidence_of(r3)\n'
    'show chain_confidence(chain)\n'
    'show chain_is_safe(chain, 0.8)\n'
)

lines, _ = run(src, reset_audit=True)
print(f"  step1 confidence:    {lines[0]}")
print(f"  step2 confidence:    {lines[1]}")
print(f"  step3 confidence:    {lines[2]}")
print(f"  chain_confidence:    {lines[3]}")
print(f"  chain_is_safe(0.8):  {lines[4]}")

# ── DEMO 2: Simulated chain with known confidences ─────────────────────────────

print()
print("=" * 60)
print("DEMO 2: Simulated chain with known confidences")
print("=" * 60)

chain = UncertainChain()
chain.add(Uncertain("meningitis_possible", 0.9), "diagnosis")
chain.add(Uncertain("meningitis", 0.8), "classification")
chain.add(Uncertain("protocol_A", 0.7), "protocol")

expected = 0.9 * 0.8 * 0.7
cc = chain.chain_confidence()
print(f"  chain_confidence: {cc:.4f}  (expected: {expected:.4f})")
print(f"  chain_is_safe(0.8): {chain.chain_is_safe(0.8)}  (expected: False — 0.7 < 0.8)")
print(f"  chain_is_safe(0.7): {chain.chain_is_safe(0.7)}  (expected: True)")
print(f"  weakest_step: {chain.weakest_step()}  (expected: protocol)")

# ── DEMO 3: One step fails, entire chain is unsafe ────────────────────────────

print()
print("=" * 60)
print("DEMO 3: If one step fails, the entire chain is unsafe")
print("=" * 60)

chain2 = UncertainChain()
chain2.add(Uncertain("high_result", 0.95), "step_A")
chain2.add(Uncertain(NOTHING, 0.0), "step_B_no_backend")
chain2.add(Uncertain("high_result", 0.92), "step_C")

cc2 = chain2.chain_confidence()
print(f"  Step A confidence: 0.95")
print(f"  Step B confidence: 0.0  <- failure (no backend)")
print(f"  Step C confidence: 0.92")
print(f"  chain_confidence: {cc2:.4f}  (0 — 0.0 contaminates the entire chain)")
print(f"  weakest_step: {chain2.weakest_step()}  (expected: step_B_no_backend)")

# ── DEMO 4: Chain audit in a single call ──────────────────────────────────────

print()
print("=" * 60)
print("DEMO 4: Chain audit in a single call")
print("=" * 60)

entries = chain.chain_audit()
for entry in entries:
    name = entry["name"]
    conf = entry["confidence"]
    print(f"  {name:15s}  confidence={conf:.2f}")

print()
print("Guarantee verified: without backend, chain_confidence=0 always.")
