# Run from repo root: python demo_guarantee1.py
import sys; sys.path.insert(0, '.')
from ledge_lang import run

cases = [
    ('classify', 'define r as classify("chest pain") using ["urgent","routine"]\nshow confidence_of(r)'),
    ('analyze',  'define r as analyze("contract with ambiguous terms") using legal\nshow confidence_of(r)'),
    ('generate', 'define r as generate("write a summary") using text_gen\nshow confidence_of(r)'),
]

for name, code in cases:
    lines, _ = run(code, output_fn=lambda x: None)
    conf = lines[0]
    print(f"{name:10s} without backend -> confidence = {conf}")
    assert conf == '0', f"FAILED: expected 0, got {conf}"

print("\nGuarantee verified: without backend, confidence = 0 in all cases.")
