# Ledge Quickstart
## From zero to productive in 10 minutes

---

## 1. Install

```bash
pip install ledge-lang
```

Verify:
```bash
ledge version
# Ledge 1.0.0
```

---

## 2. Hello, Ledge

Create `hello.ledge`:

```ledge
define name as "world"
show "Hello, {name}!"
show "1 + 1 = {1 + 1}"
```

Run it:
```bash
ledge run hello.ledge
# Hello, world!
# 1 + 1 = 2
```

---

## 3. The three rules of Ledge

**Rule 1: `=` is always comparison, never assignment.**
```ledge
define x as 10      # create a variable
set x to 20         # change its value
show x = 20         # compare: prints true
```

**Rule 2: Operations that can fail return `nothing`, never crash.**
```ledge
show divide(10, 0)      # → nothing  (not an error)
show list [1, 2][99]    # → nothing  (not an error)

# Use `or` to provide a fallback:
show divide(10, 0) or -1    # → -1
show list [1, 2][99] or 0   # → 0
```

**Rule 3: AI operations return `Uncertain[T]` — always handle confidence.**
```ledge
define result as classify(text) using ["spam", "ham"]

# Wrong — the typechecker will error:
# show upper(result)    # ERROR: unsafe use of Uncertain value

# Right — use when() to extract safely:
show when(result, 0.8, "not sure")
```

---

## 4. Variables and types

```ledge
# Basic types
define name    as "Alice"          # text
define age     as 30               # number
define active  as true             # truth
define nothing_here as nothing     # nothing

# Type annotations (optional, enforced on mutation)
define score: number as 0
set score to 99      # OK
# set score to "hi"  # ERROR: type mismatch

# Any type
define flexible: any as 42
set flexible to "now a string"    # OK
```

---

## 5. Collections

```ledge
# Lists
define nums as list [3, 1, 4, 1, 5, 9]
show len(nums)                        # 6
show sort(nums)                       # [1, 1, 3, 4, 5, 9]
show filter(nums, given x: x > 4)    # [5, 9]
show map(nums, given x: x * 2)       # [6, 2, 8, 2, 10, 18]

# Safe indexing — never crashes
show nums[0]     # 3
show nums[99]    # nothing (out of bounds)
show nums[99] or 0    # 0 (with fallback)

# Maps
define person as map {"name": "Alice", "age": 30}
show person["name"]    # Alice
show person.age        # 30 (dot notation)
show person["x"]       # nothing (missing key)
```

---

## 6. Control flow

```ledge
# If/else
if age >= 18:
    show "adult"
else if age >= 13:
    show "teenager"
else:
    show "child"

# For loops
for each item in list [1, 2, 3, 4, 5]:
    show item

# While
define i as 0
while i < 5:
    set i to i + 1
show i    # 5

# Match
match status:
    case "active":
        show "running"
    case "stopped":
        show "idle"
    otherwise:
        show "unknown: {status}"
```

---

## 7. Functions

```ledge
# Basic function
define greet(name: text):
    return "Hello, {name}!"

show greet("Alice")    # Hello, Alice!

# Lambda (single expression)
define double as given x: x * 2
show double(21)    # 42

# Functions with contracts
define safe_divide(a: number, b: number):
    requires:
        b != 0
    ensures:
        result != nothing
    return divide(a, b) or 0

show safe_divide(10, 2)    # 5
# safe_divide(10, 0)       # ERROR: Contract violated: b != 0
```

---

## 8. Error handling

```ledge
check:
    define data as json_parse(raw_input)
    show data["name"]
recover error:
    show "Could not parse: {error}"
always:
    show "Done"    # runs whether or not there was an error
```

---

## 9. AI operations — the Ledge advantage

```ledge
# Every AI operation returns Uncertain[T]
define sentiment as analyze("I love Ledge!") using sentiment
define category  as classify(email) using ["urgent", "normal", "spam"]
define summary   as generate("Summarize: " + document) using text

# Extract safely — specify what to do when confidence is low
show when(sentiment, 0.8, "unclear")
show when(category, 0.7, "unclassified")
show when(summary,  0.6, "could not summarize")

# Check confidence explicitly
show confidence_of(sentiment)    # number in [0.0, 1.0]
show is_confident(category)      # true if >= 0.8

# The audit trail is automatic — every AI call is logged
define log as audit_query()
show "Total AI decisions: {len(log)}"
```

**Without an AI backend, all operations return `confidence=0.0` and `value=nothing`.**
This is a safety guarantee — Ledge never invents confident AI results.

To connect a backend, pass it when running programmatically:
```python
from ledge_lang import run

def my_classifier(text, labels):
    # Your AI logic here
    return labels[0]

run(source, ai_backend={"classify": my_classifier})
```

---

## 10. Python interop

```ledge
# Use any Python library
import "python:numpy" as np
import "python:pandas" as pd
import "python:requests" as http

define matrix as np["array"](list [list [1, 2], list [3, 4]])
define response as http["get"]("https://api.example.com/data")
show response["status_code"]
```

---

## 11. Streams (reactive data)

```ledge
define numbers as stream_of(list [1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
define evens   as stream_where(numbers, given x: modulo(x, 2) = 0)
define doubled as stream_map(evens, given x: x * 2)
show stream_collect(doubled)    # [4, 8, 12, 16, 20]

# Reactive: process items as they arrive
when evens has new item as n:
    show "Even number: {n}"
```

---

## 12. Tooling

```bash
ledge run file.ledge          # Run a program
ledge check file.ledge        # Check types and syntax
ledge fmt file.ledge          # Format canonically (in place)
ledge fmt --check file.ledge  # Check formatting without modifying
ledge debug file.ledge        # Step-through debugger
ledge version                 # Show version
```

**VS Code extension:** Install `ledge-lang` from the marketplace for
syntax highlighting, autocompletion, and inline type checking.

---

## Next steps

- `docs/SPEC.md` — full language specification
- `docs/SEMANTICS.md` — formal operational semantics
- `examples/` — real-world programs (sensors, medical AI, agents)
- `docs/COMPARATIVE_POSITIONING.md` — how Ledge compares to Python
