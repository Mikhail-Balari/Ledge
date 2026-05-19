# Ledge Language Specification
## Version 1.2.0 - Reference Document

---

## 1. Introduction

### 1.1 Purpose

This document describes the implemented Ledge language surface: syntax,
runtime semantics, static checker behavior, standard library interface, and
execution model. It is a reference for implementors and reviewers, not a
mechanized formal specification.

### 1.2 Design Philosophy

Ledge is an experimental DSL for AI-assisted decision paths where uncertainty
must be visible in code. Its design priorities are:

1. **Explicit uncertainty** - AI operations return `Uncertain[T]`.
2. **Readable control flow** - confidence checks, fallbacks, and review paths are
   visible in source.
3. **Checked execution paths** - `ledge run` and `checked_run(...)` run the
   static `Uncertain[T]` checker before execution.
4. **Deterministic local behavior** - examples run without an API key and fail
   closed when no backend is configured.
5. **Small implementation surface** - the checker and runtime are intended to be
   inspectable by reviewers.

### 1.3 Scope

This specification covers Ledge version 1.2.0. It defines what conforming
Ledge programs mean in the reference implementation, with limitations called
out in `docs/STATIC_CHECKER.md` and `docs/THREAT_MODEL.md`.

---

## 2. Lexical Structure

### 2.1 Source files

Ledge source files use UTF-8 encoding. The file extension is `.ledge`. Line endings may be LF (`\n`) or CRLF (`\r\n`); both are normalized to LF.

### 2.2 Lines and indentation

Ledge uses significant indentation. Indentation must be exactly **4 spaces** per level. Tabs are a lexical error. Mixed indentation is a lexical error. Empty lines and comment-only lines have no effect on indentation.

The lexer emits synthetic `INDENT` and `DEDENT` tokens when the indentation level changes. Indentation changes inside balanced brackets `()`, `[]`, `{}` are suppressed — this enables multi-line expressions.

### 2.3 Comments

A `#` character outside a string literal begins a comment that extends to the end of the line. Comments have no semantic content.

```ledge
# This is a comment
define x as 10  # This is also a comment
```

### 2.4 Keywords

The following identifiers are reserved and cannot be used as variable names:

```
define    as        set       to        show
for       each      in        if        else
while     repeat    until     times     match
case      otherwise return    break     continue
pass      yield     run       wait      parallel
collect   check     recover   always    given
type      has       import    from      export
not       and       or        is        using
analyze   generate  ask       embed     classify
list      map       true      false     nothing
```

**Note on AI keywords:** `analyze`, `generate`, `ask`, `embed`, and `classify` are reserved as language instructions when followed by the pattern `(expr) using ...`. When used as user-defined function names, they are treated as identifiers. This is the only case of context-sensitive parsing in Ledge.

### 2.5 Identifiers

An identifier begins with a letter (`a-z`, `A-Z`) or underscore (`_`), followed by zero or more letters, digits, or underscores. Identifiers are case-sensitive.

### 2.6 Literals

**Number literals:**
```
42          # integer
3.14        # float
-5          # negative integer (unary minus)
```
All numbers are IEEE 754 double-precision. There is no separate integer type at runtime; integers display without decimal point.

**String literals:** Double-quoted, UTF-8. Escape sequences: `\n`, `\t`, `\"`, `\\`, `\{`, `\}`. Interpolation with `{expr}` — any expression inside braces is evaluated and converted to text.

```ledge
define name as "world"
show "Hello, {name}!"          # Hello, world!
show "2 + 2 = {2 + 2}"        # 2 + 2 = 4
```

**Boolean literals:** `true`, `false`

**Nothing literal:** `nothing` — the only null-like value in Ledge

---

## 3. Types

### 3.1 Value types

| Type name | Description | Example |
|---|---|---|
| `text` | UTF-8 string | `"hello"` |
| `number` | IEEE 754 double | `42`, `3.14` |
| `truth` | Boolean | `true`, `false` |
| `list` | Ordered sequence | `list [1, 2, 3]` |
| `map` | String-keyed dictionary | `map {"k": 1}` |
| `nothing` | Absence of value | `nothing` |
| `function` | Callable | defined functions |
| `any` | Type annotation that accepts all types | — |

### 3.2 Type annotations

Type annotations are optional and advisory. They are checked at the point of definition:

```ledge
define count: number as 0
define name:  text   as "Ledge"
define items: list   as list []
```

A mismatch between annotation and value is a runtime error:

```ledge
define x: number as "hello"   # Runtime error: 'x' should be number, got text
```

Using `any` suppresses type checking:

```ledge
define value: any as 42       # Always valid
```

### 3.3 Nothing and the fallback operator

`nothing` is the only value returned by operations that can produce "no result":

- Safe indexing beyond list bounds: `list [1,2,3][99]` → `nothing`
- Missing map key: `map {}["missing"]` → `nothing`
- Division by zero: `divide(10, 0)` → `nothing`
- Negative sqrt: `sqrt(-1)` → `nothing`
- Failed type conversion: `number("abc")` → `nothing`

The `or` operator provides a fallback when the left side is `nothing`:

```ledge
define result as items[99] or "not found"
define count  as data["n"] or 0
define ratio  as divide(a, b) or 0
```

This is the **mandatory fallback pattern**. There are no exceptions for these cases — the language makes failure handling unavoidable by returning `nothing` instead of crashing.

### 3.4 User-defined types

```ledge
type Point has:
    x: number
    y: number

type Config has:
    host: text
    port: number = 8080
    debug: truth = false

define p as Point(3.0, 4.0)
define c as Config("localhost")   # port and debug use defaults
```

Type instances are immutable maps. Fields are accessed with `.name` or `["name"]` syntax.

---

## 4. Expressions

### 4.1 Operator precedence (highest to lowest)

| Level | Operators | Associativity |
|---|---|---|
| 7 | `.field`, `[index]`, `(call)` | left |
| 6 | `-` (unary), `not` | right |
| 5 | `*`, `/` | left |
| 4 | `+`, `-` | left |
| 3 | `=`, `!=`, `<`, `>`, `<=`, `>=`, `is`, `is not` | none |
| 2 | `and` | left |
| 1 | `or` | left |
| 0 | `or` (fallback — after fallible expr) | right |

### 4.2 Arithmetic

```ledge
show 10 + 3       # 13
show 10 - 3       # 7
show 10 * 3       # 30
show 10 / 3       # 3.3333...
show 10 / 0       # nothing — never crashes
```

The `/` operator returns `nothing` when dividing by zero. Use `divide(a, b) or default` for safe division.

String concatenation uses `+`:

```ledge
show "hello" + " " + "world"   # hello world
show "count: " + 42            # count: 42 (number auto-converted)
```

### 4.3 Comparison operators

`=` is the equality operator (not assignment — assignment uses `set ... to`):

```ledge
if x = 5:       # equality check
    show "five"
```

`is` checks for identity equality (same object), including `nothing`:

```ledge
if result is nothing:
    show "no result"
if value is not nothing:
    show value
```

### 4.4 Logical operators

`and` and `or` short-circuit. `not` is prefix:

```ledge
if x > 0 and x < 100:
    show "in range"

if error is nothing or retry = false:
    show "skip"

show not true   # false
```

### 4.5 Lambda expressions

```ledge
define double as given x: x * 2
define add    as given (a, b): a + b
```

Lambdas are single-expression functions. For multi-statement functions, use `define`.

### 4.6 AI instructions (native)

These are language-level instructions, not library calls:

```ledge
define sentiment as analyze("The product is excellent") using sentiment
# → map {"tone": "positive", "confidence": 0.94}

define summary   as generate("Summarize: " + article) using text
# → text string

define answer    as ask("What is the boiling point of water?")
# → "100°C at sea level"

define vector    as embed("machine learning")
# → list of numbers (embedding vector)

define label     as classify(email) using ["spam", "urgent", "normal"]
# → "normal"
```

The `using` clause selects the AI operation mode. The runtime resolves which model to call — the Ledge program is model-agnostic.

---

## 5. Statements

### 5.1 Variable definition

```ledge
define name as value
define name: type as value
```

Creates a new variable in the current scope. The variable does not exist before this statement. Using an undefined variable is a runtime error.

### 5.2 Variable assignment

```ledge
set name to value
```

Mutates an existing variable. The variable must exist (created by `define`) or it is a runtime error. This intentional distinction makes mutation visible and explicit.

### 5.3 Show

```ledge
show expr
show expr as json
show expr as table
show expr as raw
```

Outputs a value. Format hints:
- `json` — serialize as pretty-printed JSON
- `table` — render a list of maps as an ASCII table
- `raw` — Python `str()` representation

### 5.4 Conditionals

```ledge
if condition:
    statements

if condition:
    statements
else if other_condition:
    statements
else:
    statements
```

No parentheses around conditions. The condition is any expression — truthiness follows: `false`, `nothing`, `0`, `""`, `[]`, `{}` are falsy; everything else is truthy.

### 5.5 For loop

```ledge
for each item in iterable:
    statements

for each key, value in some_map:
    statements
```

Iterates over lists, maps (yielding key-value pairs), and strings (yielding characters). `break` and `continue` are supported.

### 5.6 While loop

```ledge
while condition:
    statements
```

### 5.7 Repeat

```ledge
repeat 5 times:
    statements

repeat until condition:
    statements
```

`repeat N times` is equivalent to `for each _ in range(N)`. `repeat until` loops until the condition becomes true.

### 5.8 Match

```ledge
match subject:
    case value1:
        statements
    case value2:
        statements
    otherwise:
        statements
```

Pattern matching on exact equality. `otherwise` is the default branch (optional). If no case matches and there is no `otherwise`, the match does nothing.

### 5.9 Check (error handling)

```ledge
check:
    statements
recover error:
    statements    # error is the message string
always:
    statements    # always runs, like finally
```

The `check` block is the only way to handle errors in Ledge. The `recover` clause name is optional. The `always` clause runs whether an error occurred or not. Both `recover` and `always` are optional.

### 5.10 Function definition

```ledge
define name(param1, param2):
    statements
    return value

define name(param: type, other: type):
    statements
```

Functions are first-class values. They capture their enclosing scope (closures). Recursion works without special syntax.

If a function reaches its end without a `return`, it returns `nothing`.

### 5.11 Return, break, continue, pass

```ledge
return           # return nothing from function
return value     # return a value
break            # exit innermost loop
continue         # skip to next loop iteration
pass             # no-op placeholder for empty blocks
```

### 5.12 Yield (generators)

A function containing `yield` becomes a generator. When called, it executes until all `yield` statements have been reached and returns a list of all yielded values:

```ledge
define evens(limit):
    define n as 0
    while n <= limit:
        if modulo(n, 2) = 0:
            yield n
        set n to n + 1

define result as evens(10)
# result = list [0, 2, 4, 6, 8, 10]
```

### 5.13 Parallel execution

```ledge
define results as parallel [
    fetch_api_1(),
    fetch_api_2(),
    fetch_api_3()
]
# results = list [result1, result2, result3]
```

In v0.1 this runs sequentially. In v1.0, expressions run concurrently and results are collected in order.

### 5.14 Import

```ledge
import "math" as math
import "collections" as col
from "text" import upper, lower, trim
```

Imports a standard library module. Third-party modules are not supported in v0.1.

### 5.15 Type definition

```ledge
type Name has:
    field1: type = default
    field2: type
```

Defines a new type with named fields. Instances are created by calling the type as a function.

---

## 6. Standard Library

All standard library modules are accessed via `import`.

### 6.1 Built-in functions (always available)

These functions require no import:

**Collections:** `len`, `range`, `append`, `remove`, `slice`, `merge`, `join`, `sum`, `max`, `min`, `sort`, `reverse`, `filter`, `map`, `has`, `keys`, `values`

**Text:** `split`, `trim`, `upper`, `lower`, `replace`, `contains`, `starts_with`, `ends_with`

**Math:** `divide`, `modulo`, `power`, `sqrt`, `abs`, `round`, `floor`, `ceil`, `random`, `log`, `sin`, `cos`

**Type:** `type`, `number`, `text`, `truth`, `len`

**Data:** `json_parse`, `json_stringify`

**Control:** `error`, `assert`, `now`

### 6.2 `math` module

Extended mathematics: `pi`, `e`, `tau`, `sqrt`, `cbrt`, `sin`, `cos`, `tan`, `asin`, `acos`, `atan`, `atan2`, `log`, `log2`, `log10`, `exp`, `gcd`, `lcm`, `clamp`, `lerp`, `degrees`, `radians`, `is_nan`, `is_inf`

### 6.3 `text` module

Extended text: `pad_left`, `pad_right`, `center`, `repeat`, `count`, `index_of`, `is_number`, `is_empty`, `lines`, `words`, `title_case`, `to_camel`

### 6.4 `collections` module

`group_by`, `count_by`, `unique`, `flatten`, `zip`, `take`, `drop`, `reduce`, `chunk`, `frequencies`, `intersection`, `difference`

### 6.5 `file` module

`read(path)`, `write(path, content)`, `append(path, content)`, `exists(path)`, `delete(path)`, `list(path)`, `lines(path)`, `read_json(path)`, `write_json(path, data)`

All file operations return `nothing` on failure — never throw.

### 6.6 `http` module

`get(url)`, `post(url, body)`, `put(url, body)`, `delete(url)`, `fetch(url)`

Returns a map with fields: `status`, `ok`, `body`, `headers`, `data` (auto-parsed JSON).

### 6.7 `regex` module

`match(pattern, text)`, `search(pattern, text)`, `find_all(pattern, text)`, `replace(pattern, replacement, text)`, `split(pattern, text)`, `test(pattern, text)`

### 6.8 `time` module

`now()`, `sleep(seconds)`, `format(timestamp, fmt?)`, `timestamp()`

### 6.9 `env` module

`get(name, default?)`, `set(name, value)`, `all()`

---

## 7. Execution Model

### 7.1 Scoping

Ledge uses lexical scoping with closures. Each function call creates a new scope. Variables are looked up in the enclosing scope chain.

```ledge
define x as 10

define show_x():
    show x        # accesses outer x

define make_counter():
    define count as 0
    define increment():
        set count to count + 1   # mutates outer count
        return count
    return increment
```

### 7.2 Immutability of `define`

`define` creates a binding in the current scope. `set` mutates an existing binding. The distinction is intentional: `set` on an undefined variable is an error:

```ledge
set x to 10     # Error: 'x' is not defined
```

### 7.3 Everything is a value

Functions, types, and modules are all values. They can be assigned, passed as arguments, and returned:

```ledge
define apply(fn, x):
    return fn(x)

show apply(given n: n * 2, 21)   # 42
```

### 7.4 Error propagation

Errors propagate up the call stack until caught by a `check` block. Uncaught errors terminate the program with an error message. There is no equivalent to try/except/raise — `check`/`recover` is the only mechanism.

The `or` fallback handles the most common case (operation returns `nothing`) without requiring a full `check` block.

---

## 8. Grammar

The complete grammar is in `docs/GRAMMAR.md`. This section provides a condensed reference.

```ebnf
program     ::= statement*
statement   ::= define | assign | show | if | for | while | repeat
              | match | check | return | break | continue | pass
              | yield | run | import | type_def | expr_stmt
define      ::= "define" ident (":" type)? "as" fallback_expr
              | "define" ident "(" params ")" ":" block
assign      ::= "set" ident "to" fallback_expr
show        ::= "show" expr ("as" format)?
if          ::= "if" cond ":" block ("else if" cond ":" block)* ("else" ":" block)?
for         ::= "for" "each" ident ("," ident)? "in" expr ":" block
while       ::= "while" cond ":" block
repeat      ::= "repeat" expr "times" ":" block
              | "repeat" "until" cond ":" block
match       ::= "match" expr ":" indent case+ ("otherwise" ":" block)? dedent
check       ::= "check" ":" block ("recover" ident? ":" block)? ("always" ":" block)?
fallback    ::= expr ("or" expr)?
expr        ::= or_expr
or_expr     ::= and_expr ("or" and_expr)*
and_expr    ::= not_expr ("and" not_expr)*
not_expr    ::= "not" not_expr | comparison
comparison  ::= arithmetic (comp_op arithmetic)?
arithmetic  ::= term (("+"|"-") term)*
term        ::= unary (("*"|"/") unary)*
unary       ::= "-" unary | postfix
postfix     ::= primary ("(" args ")" ("using" ident)? | "[" expr "]" | "." ident)*
primary     ::= number | string | bool | nothing | ident
              | "list" "[" exprs "]" | "map" "{" pairs "}"
              | "(" expr ")" | lambda | parallel
              | ai_instruction
```

---

## 9. Conformance

A conforming implementation of Ledge:

1. Accepts all syntactically valid Ledge programs
2. Rejects all syntactically invalid programs with an error message indicating the location
3. Produces the output defined by this specification for all valid programs
4. Reports runtime errors for operations on incompatible types when type annotations are present
5. Returns `nothing` (never crashes) for the safe operations defined in §3.3
6. Implements all built-in functions defined in §6.1

---

## 10. Versioning

Ledge version numbers follow semantic versioning (`MAJOR.MINOR.PATCH`).

- MAJOR changes indicate breaking grammar or semantic changes
- MINOR changes add new language features in a backward-compatible way
- PATCH changes are bug fixes with no semantic change

Programs written for Ledge 0.x may require changes to run on Ledge 1.x. From 1.0 onward, the project intends to preserve backward compatibility within a major version, but no formal compatibility guarantee is offered while Ledge is pre-1.x-stable.

---

## Appendix A: Design decisions

### Why `set x to value` instead of `x = value`?

In every language that uses `x = value`, programmers write `if x = 5` intending comparison, and get assignment. In Ledge, `=` is always comparison. `set x to value` is mutation. The two operations look completely different, preventing an entire class of bugs.

### Why `or` instead of `??` or `?.`?

`or` reads aloud. `divide(a, b) or 0` says "divide a by b, or use zero." `??` and `?.` are operators for eyes that have read too much C.

### Why is there no `null`/`undefined` distinction?

Every language that distinguishes null from undefined creates programs where the difference matters in surprising places. Ledge has one value for "nothing": `nothing`. The language makes working with it safe via the `or` fallback.

### Why no exceptions?

Exceptions create invisible control flow. A function that throws can terminate any caller — including callers that weren't written to handle it. Ledge makes error handling visible: operations that can fail return `nothing`, which the `or` operator handles. Side effects that can fail use `check`/`recover`, which is explicit in the code.

### Why exactly 4 spaces for indentation?

Configurable indentation creates incompatible files. Two-space, four-space, and tab-indented files cannot be mixed. By mandating exactly 4 spaces, every Ledge file looks the same regardless of editor or author. The formatter enforces this.

### Why is AI a language instruction instead of a library?

Because AI inference is categorically different from a function call. It has no deterministic return value, consumes different resources, may require different error handling, and represents a fundamentally different computational primitive. Making it a language instruction rather than a library call:

1. Makes AI use visible in source code (not hidden inside imports)
2. Allows the runtime to optimize, cache, and batch AI calls
3. Lets static analysis tools reason about AI usage
4. Makes AI-powered programs portable across models and providers

---

*Ledge Language Specification, Version 0.1. This document is normative.*

---

## Edge Cases and Boundary Conditions

This section documents important edge cases that any conforming implementation must handle.

### Nothing semantics

`nothing` is a unique value — it is not `false`, not `0`, not `null`. Operations that would
fail return `nothing`, which propagates cleanly:

```ledge
show divide(1, 0)       # → nothing
show list [1][99]        # → nothing
show sqrt(-1)            # → nothing
show map {}["x"]         # → nothing
show nothing = false     # → false (strictly not equal)
show nothing = 0         # → false
show nothing = nothing   # → true
```

### Stream edge cases

```ledge
# Re-iteration: list-based streams are re-iterable
define s as stream_of(list [1, 2, 3])
define e as stream_where(s, given x: x > 1)
show stream_collect(e)   # [2, 3]
show stream_collect(e)   # [2, 3] again — re-iterable

# Infinite generators with lazy evaluation
define naturals(n):
    while true:
        yield n
        set n to n + 1
define g as naturals(0)
show g[999]   # 999 — no hang, evaluated lazily
```

### Uncertain[T] edge cases

```ledge
# Without backend: ALWAYS confidence=0.0, NEVER fake
show confidence_of(analyze("x") using y)    # → 0
show confidence_of(classify("x") using ["a","b"])  # → 0
show value_of(classify("x") using ["a","b"])       # → nothing

# Declared type is preserved even when value is nothing
show type(classify("x") using ["a","b"])  # → uncertain[text]
show type(analyze("x") using y)           # → uncertain[map]

# Confidence clamping
show confidence_of(uncertain("x", 2.5))  # → 1 (clamped to [0.0, 1.0])
show confidence_of(uncertain("x", -1))   # → 0 (clamped)
```

### Arithmetic edge cases

```ledge
# Integer display: floats that equal integers display without decimal
show 1.0        # → 1 (not 1.0)
show 10 / 4     # → 2.5
show 10 / 2     # → 5 (not 5.0)

# String concatenation with numbers
show "n=" + 42   # → n=42
show 1 + "px"    # → 1px
```

### Contract edge cases

```ledge
# Precondition fires BEFORE body — body never executes
define f(x: number):
    requires:
        x > 0
    show "body"  # never runs if x <= 0
    return x

# Postcondition uses 'result' binding
define g(x: number):
    ensures:
        result != nothing
    return x * 2
```

### Boolean/type strict semantics

```ledge
# These are ALWAYS false — critical invariant
show true = 1         # false
show false = 0        # false
show true = false     # false (different values)

# Truthiness in conditions
if 0:     # falsy
if "":    # falsy
if list []: # falsy
if nothing: # falsy
```

---


---

## Python FFI (Foreign Function Interface)

Ledge programs can use any Python module via the `import "python:module"` syntax.

### Syntax

```ledge
import "python:module_name" as alias
import "python:numpy" as np
```

### Type conversion

| Python type | Ledge type |
|-------------|-----------|
| int, float  | number    |
| str         | text      |
| bool        | truth     |
| None        | nothing   |
| list        | list      |
| dict        | map       |
| any object  | python_module (callable, indexable) |

### Calling Python functions

```ledge
import "python:math" as m
show m["sqrt"](25)      # → 5
show m["pi"]            # → 3.141592653589793
show m["floor"](3.7)    # → 3
```

### Security model

By default, all Python modules are accessible. To restrict:

```ledge
# Via API: allowed_modules parameter
run(source, allowed_modules=["math", "json"])

# Via CLI: restrict to safe subset
# ledge run program.ledge --safe-mode
# ledge run program.ledge --allow-import=math,json
```

See `docs/SECURITY.md` for the full security model.

### Failure behavior

If a Python module does not exist:

```ledge
import "python:nonexistent" as m  # → LedgeError: Cannot import Python module
```

If a Python function call fails, the error is wrapped as a `LedgeError`.

## Security Model

See `docs/SECURITY.md` for the full security model and permission documentation.

**Short summary:** FFI is intentionally open for trusted environments. For sandboxed execution, use Docker. Zero fake AI confidence is enforced by the runtime.
