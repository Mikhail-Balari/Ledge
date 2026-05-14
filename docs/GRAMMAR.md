# Ledge Grammar — EBNF Reference
## Version 1.0.0 — Synchronized with parser.py

This grammar is a description of the language as accepted by the reference
parser, not a normative formal specification with a mechanized
equivalence proof. Every construct that appears here parses in the
reference implementation, and every parseable public construct is
intended to appear here.
Grammar marked [EXPERIMENTAL] parses but has incomplete runtime support.
Grammar marked [ROADMAP] is planned but not yet parseable.

---

## Notation

```
rule        ::= definition
X*          zero or more X
X+          one or more X
X?          zero or one X
X | Y       either X or Y
( X )       grouping
"keyword"   literal keyword
UPPER       terminal token from lexer
indent      synthetic INDENT token (4 spaces)
dedent      synthetic DEDENT token
newline     end of logical line
```

---

## Top-level structure

```ebnf
program     ::= statement* EOF

statement   ::= define_stmt
              | assign_stmt
              | show_stmt
              | if_stmt
              | for_stmt
              | while_stmt
              | repeat_stmt
              | match_stmt
              | check_stmt
              | return_stmt
              | break_stmt
              | continue_stmt
              | pass_stmt
              | yield_stmt
              | import_stmt
              | type_def_stmt
              | when_stmt
              | agent_def_stmt
              | run_stmt
              | expr_stmt
```

---

## Statements

```ebnf
define_stmt ::= "define" name (":" type_hint)? "as" fallback_expr newline
              | "define" name "(" params ")" ":" contract? block

assign_stmt ::= "set" name "to" fallback_expr newline

show_stmt   ::= "show" fallback_expr ("as" format_hint)? newline

format_hint ::= "json" | "table" | "raw"

if_stmt     ::= "if" expr ":" block
                ("else" "if" expr ":" block)*
                ("else" ":" block)?

for_stmt    ::= "for" "each" name ("," name)? "in" expr ":" block

while_stmt  ::= "while" expr ":" block

repeat_stmt ::= "repeat" expr "times" ":" block
              | "repeat" "until" expr ":" block

match_stmt  ::= "match" expr ":" indent
                  ("case" expr ":" block)+
                  ("otherwise" ":" block)?
                dedent

check_stmt  ::= "check" ":" block
                ("recover" name? ":" block)?
                ("always" ":" block)?

return_stmt ::= "return" expr? newline

break_stmt  ::= "break" newline
continue_stmt ::= "continue" newline
pass_stmt   ::= "pass" newline

yield_stmt  ::= "yield" expr newline

import_stmt ::= "import" STRING "as" name newline
              | "from" STRING "import" name ("," name)* newline

type_def_stmt ::= "type" name "has" ":" indent
                    (type_field newline)+
                  dedent

type_field  ::= name ":" type_hint ("=" expr)?

when_stmt   ::= "when" expr "has" "new"? "item"? ("as" name)? ":" block
              | "when" expr ":" block

agent_def_stmt ::= "agent" name ":" indent    [EXPERIMENTAL]
                     ("tools" ":" indent
                       (name "from" "mcp" expr newline)+
                     dedent)?
                     ("model" ":" expr newline)?
                     ("behavior" ":" block)?
                   dedent

run_stmt    ::= "run" expr ("wait" | "distributed" "across" expr "workers")? newline

expr_stmt   ::= expr newline
```

---

## Blocks

```ebnf
block       ::= indent statement+ dedent

contract    ::= requires_clause? ensures_clause?

requires_clause ::= "requires" ":" indent (expr newline)+ dedent

ensures_clause  ::= "ensures" ":" indent (expr newline)+ dedent
```

---

## Function parameters

```ebnf
params      ::= (param ("," param)*)?

param       ::= name (":" type_hint)?

type_hint   ::= "text" | "number" | "truth" | "list" | "map"
              | "any" | "nothing" | name
```

---

## Expressions (in order of precedence, lowest first)

```ebnf
fallback_expr ::= expr ("or" expr)?

expr        ::= or_expr

or_expr     ::= and_expr ("or" and_expr)*

and_expr    ::= not_expr ("and" not_expr)*

not_expr    ::= "not" not_expr | comparison

comparison  ::= arithmetic (comp_op arithmetic)?
              | arithmetic "is" "not"? arithmetic

comp_op     ::= "=" | "!=" | "<" | ">" | "<=" | ">="

arithmetic  ::= term (("+"|"-") term)*

term        ::= unary (("*"|"/") unary)*

unary       ::= "-" unary | "not" unary | postfix

postfix     ::= primary
                ( "(" args ")" ("using" (name | "[" expr_list "]"))?
                | "[" expr "]"
                | "." name
                | "|" pipe_op
                )*

pipe_op     ::= "where" (name ":")? expr
              | "transform" (name ":")? expr
              | "take" expr
              | "collect"
              | name                    # generic pipe to function

args        ::= (arg ("," arg)*)?

arg         ::= expr
              | name "=" expr           # keyword argument
```

---

## Primary expressions

```ebnf
primary     ::= NUMBER
              | STRING
              | "true"
              | "false"
              | "nothing"
              | name
              | "list" "[" expr_list "]"
              | "map" "{" map_pairs "}"
              | "(" expr ")"
              | lambda_expr
              | parallel_expr
              | stream_expr             [EXPERIMENTAL]
              | ai_instruction
              | "mcp" expr              [EXPERIMENTAL]

lambda_expr ::= "given" name ":" expr
              | "given" "(" params ")" ":" expr

parallel_expr ::= "parallel" "[" expr_list "]"

stream_expr ::= "stream" "from" expr ("|" pipe_op)*   [EXPERIMENTAL]
              | "stream" "[" expr_list "]"              [EXPERIMENTAL]

ai_instruction ::= "analyze" "(" expr ")" "using" name
                 | "classify" "(" expr ")" "using" "[" expr_list "]"
                 | "generate" "(" expr ")" "using" name
                 | "ask" "(" expr ")"
                 | "embed" "(" expr ")"

expr_list   ::= (expr ("," expr)*)?

map_pairs   ::= (STRING ":" expr ("," STRING ":" expr)*)?
```

---

## Lexical tokens

```ebnf
NUMBER      ::= [0-9]+ ("." [0-9]+)?
              | "-" [0-9]+ ("." [0-9]+)?

STRING      ::= '"' (char | interpolation)* '"'

interpolation ::= "{" expr "}"

char        ::= any UTF-8 character except '"' and '{', or escape sequence

escape      ::= '\n' | '\t' | '\"' | '\\' | '\{' | '\}'

IDENT       ::= [a-zA-Z_][a-zA-Z0-9_]*

INDENT      ::= start of line with 4 more spaces than previous line
DEDENT      ::= start of line with 4 fewer spaces than previous line
```

---

## Reserved keywords

The following identifiers are reserved:

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
stream    when      where     window    agent
behavior  tools     model     requires  ensures
mcp       tool      emit      subscribe async
between   seconds   minutes   across    workers
```

**Context-sensitive keywords:** `analyze`, `classify`, `generate`, `ask`, `embed`,
`collect`, `when`, `agent` can also be used as function/variable names when
followed by `(` without the AI-instruction pattern. The parser uses lookahead
to disambiguate.

---

## Operator precedence table

| Level | Operators | Associativity |
|---|---|---|
| 7 (highest) | `.field`, `[idx]`, `(call)`, `\|pipe` | left |
| 6 | `-` (unary), `not` | right |
| 5 | `*`, `/` | left |
| 4 | `+`, `-` | left |
| 3 | `=`, `!=`, `<`, `>`, `<=`, `>=`, `is`, `is not` | none |
| 2 | `and` | left |
| 1 | `or` | left |
| 0 (lowest) | `or` (fallback, after fallible) | right |

---

## Significant indentation rules

1. Blocks are opened by `:` followed by a newline and `INDENT`
2. Each level of indentation is exactly **4 spaces** — tabs are a lexical error
3. Indentation inside balanced brackets `()`, `[]`, `{}` is suppressed
4. Empty lines do not affect indentation tracking
5. The `DEDENT` token may close multiple block levels at once

---

## Grammar notes

- The `or` operator serves dual purpose: logical OR and fallback. Context
  disambiguates: after a fallible operation (divide, list index, map access,
  AI instruction), `or` provides the fallback. See SEMANTICS.md §4.5.

- AI instructions (`analyze`, `classify`, etc.) are distinguished from
  user-defined function calls by the `using` keyword: `f(x) using mode` parses
  as an AI instruction; `f(x)` parses as a function call.

- `stream from "url"` is [EXPERIMENTAL] — the syntax parses but external
  URL sources are not connected to real transports in v1.0.

- `agent ... :` blocks are [EXPERIMENTAL] — they parse and produce a
  LedgeMap representation but full MCP connectivity requires external servers.
