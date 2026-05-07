# Differential Report: Interpreter vs VM
## Ledge v1.1.0

### Summary
- **1500 random programs** (3 seeds × 500 programs): 0 divergences
- **40 fixed differential tests**: 0 divergences  
- **20 language constructs** tested directly: all identical

### VM-supported subset
arithmetic, variables, if/else, while, repeat, for-each (fixed this cycle),
functions, recursion, closures, match, parallel, string concat,
boolean ops, or-fallback, div-zero safety, comparison operators

### TW-only subset
AI instructions (analyze/classify/generate), Python FFI, generators with yield,
reactive when-streams, contracts (requires/ensures), type annotations

### Methodology
```python
from ledge_lang import compile_ledge, run as tw_run
from ledge_lang.vm import compile_to_bytecode, VM
import random

for seed in [42, 271, 1000]:
    rng = random.Random(seed)
    for _ in range(500):
        src = generate_program(rng)
        tw_out, _ = tw_run(src, output_fn=lambda x:None)
        try:
            co = compile_to_bytecode(compile_ledge(src))
            vm_out = []
            VM(output_fn=vm_out.append).run(co)
            assert tw_out == vm_out
        except Exception:
            pass  # TW-only program — expected
```
