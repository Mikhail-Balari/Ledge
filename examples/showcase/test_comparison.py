import sys; sys.path.insert(0,'.')

print('=== PYTHON: can fail silently ===')
print()

# Simulates what Python does without Ledge
def classify_python(text, model_available=False):
    if model_available:
        return {'label': 'urgent', 'confidence': 0.9}
    else:
        # Classic bug: model is not available but the code continues anyway
        return {'label': 'not-urgent', 'confidence': 0.0}

# Without a connected model — Python returns a result as if it were real
result = classify_python('chest pain', model_available=False)
print('Python without model:', result)
print('Python uses the result anyway:', result['label'])
print('Nobody knows confidence was 0.0')
print()

print('=== LEDGE: impossible to fail silently ===')
print()

from ledge_lang import run
from ledge_lang.typechecker import check_types

# This Ledge code is impossible to write without handling uncertainty
unsafe_code = '''
define r as classify("chest pain") using ["urgent", "not-urgent"]
show r
'''

issues = check_types(unsafe_code)
errors = [i for i in issues if i.is_error]
print('Unsafe code in Ledge:')
print('  show r  (without verifying confidence)')
print('  Typechecker errors:', len(errors))
if errors:
    print('  Error:', errors[0].message[:80])

print()
safe_code = '''
define r as classify("chest pain") using ["urgent", "not-urgent"]
if confidence_of(r) >= 0.85:
    show value_of(r)
else:
    show "ESCALATE TO HUMAN"
'''
issues2 = check_types(safe_code)
errors2 = [i for i in issues2 if i.is_error]
print('Safe code in Ledge:')
print('  if confidence_of(r) >= 0.85: ...')
print('  Typechecker errors:', len(errors2))
lines, _ = run(safe_code, output_fn=lambda x:None)
print('  Output:', lines)
print()
print('CONCLUSION: Python allows the bug. Ledge makes it impossible.')
