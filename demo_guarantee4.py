# Run from repo root: python demo_guarantee4.py
import sys; sys.path.insert(0, '.')
from ledge_lang import run

# Full medical triage system, with no model connected
with open('examples/showcase/medical_triage.ledge', encoding='utf-8') as f:
    src = f.read()

lines, _ = run(src, output_fn=lambda x: None, reset_audit=True)

print("Triage system output WITHOUT AI backend:")
print()
for l in lines:
    print(f"  {l}")

escalated = [l for l in lines if 'ESCALATE' in l]
automatic = [l for l in lines if 'URGENT' in l or 'ROUTINE' in l]

print()
print(f"Patients escalated to human:   {len(escalated)}")
print(f"Patients classified automatic: {len(automatic)}")
assert len(automatic) == 0, "FAILED: classified patients without a backend"
print("\nGuarantee verified: without backend, zero automatic decisions.")
