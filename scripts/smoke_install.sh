#!/bin/bash
# Ledge Smoke Install Test
# Tests that Ledge installs and works from scratch
# Usage: ./scripts/smoke_install.sh

set -e  # Exit on any error

echo "=== Ledge Smoke Install Test ==="
echo ""

# 1. Install from current directory
echo "1. Installing Ledge..."
pip install -e . --quiet
echo "   ✓ Installation successful"

# 2. Check version
VERSION=$(python -c "from ledge_lang import __version__; print(__version__)")
echo "2. Version: $VERSION ✓"

# 3. Run REPL with a simple program
echo "3. Running 'show 42'..."
OUTPUT=$(python -c "
import sys; sys.path.insert(0,'.')
from ledge_lang import run
lines, _ = run('show 42', output_fn=lambda x:None)
print(lines[0])
")
if [ "$OUTPUT" = "42" ]; then
    echo "   ✓ Basic program works"
else
    echo "   ✗ Expected '42', got '$OUTPUT'"
    exit 1
fi

# 4. Verify AI safety
echo "4. Checking AI safety..."
python -c "
import sys; sys.path.insert(0,'.')
from ledge_lang import run
lines, _ = run('show confidence_of(analyze("test") using y)', output_fn=lambda x:None)
assert lines[0] == '0', f'AI safety violated: confidence={lines[0]}'
print('   ✓ AI safety: confidence=0 without backend')
"

# 5. Run examples
echo "5. Running all official examples..."
python -c "
import sys, glob; sys.path.insert(0,'.')
from ledge_lang import run
fails = []
for path in sorted(glob.glob('examples/*.ledge')):
    with open(path) as f: src = f.read()
    try:
        lines, _ = run(src, output_fn=lambda x:None)
    except Exception as e:
        fails.append(f'{path}: {e}')
if fails:
    for f in fails: print(f'   FAIL: {f}')
    sys.exit(1)
import os
print(f'   ✓ All {len(glob.glob("examples/*.ledge"))} examples pass')
"

# 6. Check formatter
echo "6. Testing formatter..."
python -c "
import sys; sys.path.insert(0,'.')
from ledge_lang.formatter import format_ledge
src = 'define x as 42
show x'
fmt1 = format_ledge(src)
fmt2 = format_ledge(fmt1)
assert fmt1 == fmt2, 'Formatter not idempotent'
print('   ✓ Formatter idempotent')
"

# 7. Check typechecker
echo "7. Testing typechecker..."
python -c "
import sys; sys.path.insert(0,'.')
from ledge_lang.typechecker import check_types
issues = check_types('define r as analyze("x") using y
show upper(r)')
errors = [i for i in issues if i.is_error]
assert errors, 'Typechecker should catch unsafe Uncertain use'
print(f'   ✓ Typechecker catches unsafe Uncertain use')
"

echo ""
echo "=== Smoke install: ALL CHECKS PASSED ==="
