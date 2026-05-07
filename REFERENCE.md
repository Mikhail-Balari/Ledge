# Ledge Quick Reference — v1.1.0
**One page. Every construct. No fluff.**

## Variables

    define x as 42             # create
    define x: number as 42     # typed (checked at runtime)
    set x to 100               # mutate

## Literals

    42   3.14   -7             # number (double)
    "hello"                    # text
    true   false               # truth (NOT equal to 1 and 0)
    nothing                    # absence (NOT equal to false or null)
    list [1, 2, 3]             # list
    map {"k": "v"}             # map

## Control flow

    if x > 0:
        show x
    else if x = 0:
        show "zero"
    else:
        show "negative"

    while i < 10:
        set i to i + 1

    repeat 5 times:
        body()

    for each item in collection:
        process(item)

    match value:
        case 1: show "one"
        otherwise: show "other"

## Functions

    define add(a, b):
        return a + b

    define safe(x: number):
        requires: x > 0
        ensures: result > 0
        return x

    define gen():              # generator
        yield 1
        yield 2

    given x: x * 2             # lambda

## Error handling

    expr or default            # fallback if nothing
    check:
        risky()
    recover e:
        show "failed: " + e
    always:
        cleanup()

## AI instructions — the core feature

    define r as analyze(text) using sentiment    # Uncertain[map]
    define r as classify(text) using ["a","b"]   # Uncertain[text]
    define r as generate(prompt) using text      # Uncertain[text]
    define r as ask("question")                  # Uncertain[text]
    define r as embed(text)                      # Uncertain[list]

    # Safe extraction (required — typechecker enforces this)
    when(r, 0.8, "fallback")       # extract if confident
    value_of(r)                    # extract (may be nothing)
    confidence_of(r)               # float in [0.0, 1.0]
    is_confident(r)                # confidence >= 0.8

    if is_confident(r):            # flow-narrowed inside block
        show value_of(r)           # r is safe here

    # Without a backend: confidence=0.0, value=nothing. Always. Enforced.

## Parallel and streams

    define results as parallel [fn1(), fn2(), fn3()]

    define s as stream_of(list [1,2,3])
    when s has new item as x:
        process(x)

## Python FFI

    import "python:numpy" as np
    show np["array"]([1,2,3])

## Audit trail (automatic, zero code required)

    show len(audit_query())    # every AI call is logged automatically
    show audit_export()        # export as JSON

## Key invariants (always true)

    true = 1       => false
    false = 0      => false
    nothing = false => false
    divide(x, 0)   => nothing
    list[99]       => nothing (no crash)
    nothing or X   => X

## Compile to native

    ledge compile program.ledge --target native -o program
    ./program      # 10-80x faster than CPython for numeric code

    Nota: requiere gcc instalado.
    En macOS: xcode-select --install
    En Ubuntu: sudo apt install gcc
    Verificá con: gcc --version

## Install

    pip install ledge-lang
    pip install ledge-lang[openai]      # + OpenAI backend
    pip install ledge-lang[anthropic]   # + Anthropic backend
