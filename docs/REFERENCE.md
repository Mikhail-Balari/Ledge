# Ledge Quick Reference — v1.2.0
**One page. Every construct. No fluff.**

---

## Variables

```ledge
define x as 42          # create
define x: number as 42  # create with type annotation (checked at runtime)
set x to 100            # mutate (x must already exist)
```

## Literals

```ledge
42      3.14    -7        # number (double)
"hello" "tab\t"           # text
true    false             # truth (≠ 1, ≠ 0)
nothing                   # absence (≠ false, ≠ 0, ≠ null)
list [1, 2, 3]            # list
map {"k": "v", "n": 42}   # map
```

## Control flow

```ledge
if x > 0:
    show x
else if x = 0:
    show "zero"
else:
    show "negative"

while i < 10:
    set i to i + 1

repeat 5 times:
    do_something()

for each item in collection:
    process(item)

match value:
    case 1: show "one"
    case 2: show "two"
    otherwise: show "other"
```

## Functions

```ledge
define add(a, b):           # define
    return a + b

define add(a: number, b: number):  # typed params
    requires: a > 0         # precondition (runtime checked)
    ensures: result > 0     # postcondition (runtime checked)
    return a + b

define gen():               # generator (lazy)
    yield 1
    yield 2

given x: x * 2             # lambda
```

## Error handling

```ledge
expr or default            # fallback if expr is nothing
divide(a, b) or 0          # safe division

check:
    risky_operation()
recover error:
    show "failed: " + error
always:
    cleanup()
```

## AI instructions (the core feature)

```ledge
define r as analyze(text) using sentiment    # → Uncertain[map]
define r as classify(text) using ["a","b"]   # → Uncertain[text]
define r as generate(prompt) using text      # → Uncertain[text]
define r as ask("question")                  # → Uncertain[text]
define r as embed(text)                      # → Uncertain[list]
```

**Always handle uncertainty explicitly:**

```ledge
when(r, 0.8, "fallback")      # extract if confidence >= 0.8, else fallback
value_of(r)                    # checked path requires a confidence guard
confidence_of(r)               # get confidence [0.0, 1.0]
is_confident(r)                # confidence >= 0.8

if is_confident(r):            # type-narrowed inside block
    show value_of(r)           # r is now safe to use
```

**Without a backend: confidence=0.0, value=nothing. ALWAYS. Not 0.5.**

## Streams & parallel

```ledge
define s as stream_of(list [1,2,3])
when s has new item as x:
    process(x)

define results as parallel [fn1(), fn2(), fn3()]
```

## Python FFI

```ledge
import "python:numpy" as np
show np["array"]([1, 2, 3])
```

## Audit trail (automatic)

```ledge
# Every AI call is logged automatically — no extra code needed
show len(audit_query())     # count calls
show audit_query()          # inspect entries
show audit_export()         # export as JSON
```

## Key semantic invariants

| Expression | Result |
|------------|--------|
| `true = 1` | `false` |
| `false = 0` | `false` |
| `nothing = false` | `false` |
| `divide(x, 0)` | `nothing` |
| `list[99]` (out of bounds) | `nothing` |
| `nothing or fallback` | `fallback` |

---

## Native compilation

Native compilation is experimental and not part of the stable CLI quickstart.
Use `ledge run file.ledge` for checked execution.

## Install

```bash
python -m pip install dist/ledge_lang-1.2.0-py3-none-any.whl
ledge version
```

After Ledge 1.2.0 is published to PyPI, use `python -m pip install ledge-lang`.
