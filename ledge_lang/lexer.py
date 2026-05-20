"""
Ledge Language — Lexer
Converts source text into a stream of tokens.
"""

from dataclasses import dataclass
from enum import Enum, auto
from typing import List, Optional


class TT(Enum):
    """Token types."""
    # Literals
    NUMBER    = auto()
    STRING    = auto()
    BOOL      = auto()
    NOTHING   = auto()

    # Identifiers and keywords
    IDENT     = auto()

    # Keywords
    DEFINE    = auto()
    AS        = auto()
    SET       = auto()
    TO        = auto()
    SHOW      = auto()
    FOR       = auto()
    EACH      = auto()
    IN        = auto()
    IF        = auto()
    ELSE      = auto()
    WHILE     = auto()
    REPEAT    = auto()
    UNTIL     = auto()
    TIMES     = auto()
    RETURN    = auto()
    FROM      = auto()
    USE       = auto()
    IMPORT    = auto()
    EXPORT    = auto()
    IS        = auto()
    NOT       = auto()
    AND       = auto()
    OR        = auto()
    GIVEN     = auto()
    CHECK     = auto()
    WHEN      = auto()
    OTHERWISE = auto()
    RUN       = auto()
    WAIT      = auto()
    PARALLEL  = auto()
    COLLECT   = auto()
    STOP      = auto()
    PASS      = auto()
    TYPE      = auto()
    HAS       = auto()
    WITH      = auto()
    WITHOUT   = auto()
    DONE      = auto()
    THEN      = auto()
    ALWAYS    = auto()
    MATCH     = auto()
    CASE      = auto()
    BREAK     = auto()
    CONTINUE  = auto()
    YIELD     = auto()
    STREAM    = auto()
    PIPE      = auto()   # | pipeline operator
    WHERE     = auto()   # stream where condition
    WINDOW    = auto()   # stream window N seconds
    SECONDS   = auto()   # time unit
    MINUTES   = auto()   # time unit
    REQUIRES  = auto()   # contract requires:
    ENSURES   = auto()   # contract ensures:
    BETWEEN   = auto()   # contract between N and M
    MCP       = auto()   # mcp tool
    TOOL      = auto()   # tool keyword
    AGENT     = auto()   # agent keyword
    BEHAVIOR  = auto()   # agent behavior:
    TOOLS     = auto()   # agent tools:
    MODEL     = auto()   # agent model:
    ACROSS    = auto()   # distributed across N workers
    WORKERS   = auto()   # workers keyword
    SUBSCRIBE = auto()   # subscribe to stream
    EMIT      = auto()   # emit value to stream
    ASYNC     = auto()   # async modifier
    RECOVER   = auto()
    ANALYZE   = auto()
    GENERATE  = auto()
    ASK       = auto()
    EMBED     = auto()
    CLASSIFY  = auto()
    USING     = auto()
    LIST      = auto()
    MAP       = auto()
    NATIVE    = auto()
    TRUE      = auto()
    FALSE     = auto()
    GIVEN_KW  = auto()
    TABLE     = auto()
    JSON      = auto()
    RAW       = auto()

    # Operators
    PLUS      = auto()
    MINUS     = auto()
    STAR      = auto()
    SLASH     = auto()
    EQ        = auto()
    NEQ       = auto()
    LT        = auto()
    GT        = auto()
    LTE       = auto()
    GTE       = auto()
    ASSIGN    = auto()  # = (in definitions)

    # Delimiters
    COLON     = auto()
    COMMA     = auto()
    LPAREN    = auto()
    RPAREN    = auto()
    LBRACKET  = auto()
    RBRACKET  = auto()
    LBRACE    = auto()
    RBRACE    = auto()
    DOT       = auto()

    # Structure
    INDENT    = auto()
    DEDENT    = auto()
    NEWLINE   = auto()
    EOF       = auto()


KEYWORDS = {
    "define":    TT.DEFINE,
    "as":        TT.AS,
    "set":       TT.SET,
    "to":        TT.TO,
    "show":      TT.SHOW,
    "for":       TT.FOR,
    "each":      TT.EACH,
    "in":        TT.IN,
    "if":        TT.IF,
    "else":      TT.ELSE,
    "while":     TT.WHILE,
    "repeat":    TT.REPEAT,
    "until":     TT.UNTIL,
    "times":     TT.TIMES,
    "return":    TT.RETURN,
    "from":      TT.FROM,
    "use":       TT.USE,
    "import":    TT.IMPORT,
    "export":    TT.EXPORT,
    "is":        TT.IS,
    "not":       TT.NOT,
    "and":       TT.AND,
    "or":        TT.OR,
    "given":     TT.GIVEN,
    "check":     TT.CHECK,
    "when":      TT.WHEN,
    "otherwise": TT.OTHERWISE,
    "run":       TT.RUN,
    "wait":      TT.WAIT,
    "parallel":  TT.PARALLEL,
    "collect":   TT.COLLECT,
    "stop":      TT.STOP,
    "pass":      TT.PASS,
    "type":      TT.TYPE,
    "has":       TT.HAS,
    "with":      TT.WITH,
    "without":   TT.WITHOUT,
    "done":      TT.DONE,
    "then":      TT.THEN,
    "always":    TT.ALWAYS,
    "match":     TT.MATCH,
    "case":      TT.CASE,
    "break":     TT.BREAK,
    "continue":  TT.CONTINUE,
    "yield":     TT.YIELD,
    "stream":    TT.STREAM,
    "from":      TT.FROM,
    "where":     TT.WHERE,
    "window":    TT.WINDOW,
    "seconds":   TT.SECONDS,
    "minutes":   TT.MINUTES,
    "requires":  TT.REQUIRES,
    "ensures":   TT.ENSURES,
    "between":   TT.BETWEEN,
    "mcp":       TT.MCP,
    "tool":      TT.TOOL,
    "agent":     TT.AGENT,
    "behavior":  TT.BEHAVIOR,
    "tools":     TT.TOOLS,
    "model":     TT.MODEL,
    "across":    TT.ACROSS,
    "workers":   TT.WORKERS,
    "subscribe": TT.SUBSCRIBE,
    "emit":      TT.EMIT,
    "async":     TT.ASYNC,
    "recover":   TT.RECOVER,
    "analyze":   TT.ANALYZE,
    "generate":  TT.GENERATE,
    "ask":       TT.ASK,
    "embed":     TT.EMBED,
    "classify":  TT.CLASSIFY,
    "using":     TT.USING,
    "list":      TT.LIST,
    "map":       TT.MAP,
    "native":    TT.NATIVE,
    "true":      TT.BOOL,
    "false":     TT.BOOL,
    "nothing":   TT.NOTHING,
    "table":     TT.TABLE,
    "json":      TT.JSON,
    "raw":       TT.RAW,
}


@dataclass
class Token:
    type: TT
    value: object
    line: int
    col: int

    def __repr__(self):
        return f"Token({self.type.name}, {self.value!r}, {self.line}:{self.col})"


class LexError(Exception):
    def __init__(self, msg, line, col):
        super().__init__(f"[Line {line}:{col}] Lex error: {msg}")
        self.line = line
        self.col = col


class Lexer:
    def __init__(self, source: str):
        if source.startswith("\ufeff"):
            source = source[1:]
        self.source = source
        self.pos = 0
        self.line = 1
        self.col = 1
        self.tokens: List[Token] = []
        self.indent_stack = [0]

    def error(self, msg):
        raise LexError(msg, self.line, self.col)

    def peek(self, offset=0) -> Optional[str]:
        p = self.pos + offset
        return self.source[p] if p < len(self.source) else None

    def advance(self) -> str:
        ch = self.source[self.pos]
        self.pos += 1
        if ch == '\n':
            self.line += 1
            self.col = 1
        else:
            self.col += 1
        return ch

    def match(self, ch: str) -> bool:
        if self.peek() == ch:
            self.advance()
            return True
        return False

    def add(self, tt: TT, value=None):
        self.tokens.append(Token(tt, value, self.line, self.col))

    def tokenize(self) -> List[Token]:
        while self.pos < len(self.source):
            self._scan_line()

        # Close all open indent levels
        while len(self.indent_stack) > 1:
            self.indent_stack.pop()
            self.add(TT.DEDENT)

        self.add(TT.EOF)
        # Post-process: remove INDENT/DEDENT inside brackets (implicit continuation)
        self.tokens = self._strip_bracket_indents(self.tokens)
        return self.tokens

    def _strip_bracket_indents(self, tokens):
        result = []
        depth = 0  # bracket/paren/brace depth
        for tok in tokens:
            if tok.type in (TT.LPAREN, TT.LBRACKET, TT.LBRACE):
                depth += 1
            elif tok.type in (TT.RPAREN, TT.RBRACKET, TT.RBRACE):
                depth -= 1
            if depth > 0 and tok.type in (TT.INDENT, TT.DEDENT, TT.NEWLINE):
                continue  # skip structural tokens inside brackets
            result.append(tok)
        return result

    def _scan_line(self):
        """Scan one logical line."""
        # Handle indentation at start of line
        col_start = self.col
        indent = 0
        while self.peek() == ' ':
            self.advance()
            indent += 1

        # Blank line or comment-only line: skip, no INDENT/DEDENT
        if self.peek() in ('\n', None) or self.peek() == '#':
            while self.peek() not in ('\n', None):
                self.advance()
            if self.peek() == '\n':
                self.advance()
            return

        # Tab check
        if self.peek() == '\t':
            self.error("Tabs are not allowed — use 4 spaces per indent level")

        # Emit INDENT / DEDENT tokens
        current = self.indent_stack[-1]
        if indent > current:
            if (indent - current) % 4 != 0:
                self.error(f"Indent must be a multiple of 4 spaces (got {indent - current} extra)")
            levels = (indent - current) // 4
            for _ in range(levels):
                self.indent_stack.append(self.indent_stack[-1] + 4)
                self.add(TT.INDENT)
        elif indent < current:
            while self.indent_stack[-1] > indent:
                self.indent_stack.pop()
                self.add(TT.DEDENT)
            if self.indent_stack[-1] != indent:
                self.error(f"Inconsistent dedent — got {indent} spaces, expected {self.indent_stack[-1]}")

        # Scan tokens on this line
        while self.peek() not in ('\n', None):
            self._scan_token()

        # End of line
        if self.peek() == '\n':
            self.advance()
            self.add(TT.NEWLINE)

    def _scan_token(self):
        ch = self.peek()

        # Skip spaces mid-line
        if ch == ' ':
            self.advance()
            return

        # Comment
        if ch == '#':
            while self.peek() not in ('\n', None):
                self.advance()
            return

        # String literal
        if ch == '"':
            self._scan_string()
            return

        # Number
        # CONTEXT CHECK: `-digit` is negative literal ONLY if previous token
        # is an operator, open paren, comma, or there are no tokens yet.
        # After an identifier, number, or closing paren/bracket, `-` is MINUS.
        _after_value = (self.tokens and self.tokens[-1].type in (
            TT.IDENT, TT.NUMBER, TT.STRING, TT.TRUE, TT.FALSE, TT.NOTHING,
            TT.RPAREN, TT.RBRACKET
        ))
        if ch.isdigit() or (ch == '-' and self.peek(1) and self.peek(1).isdigit()
                            and not _after_value):
            self._scan_number()
            return

        # Identifier or keyword
        if ch.isalpha() or ch == '_':
            self._scan_ident()
            return

        # Operators and delimiters
        self.advance()
        if ch == '+':   self.add(TT.PLUS)
        elif ch == '-': self.add(TT.MINUS)
        elif ch == '*': self.add(TT.STAR)
        elif ch == '/': self.add(TT.SLASH)
        elif ch == '=':
            self.match('=')  # consume optional second = for == compatibility
            self.add(TT.EQ)
        elif ch == '!':
            if self.match('='):
                self.add(TT.NEQ)
            else:
                self.error(f"Unexpected character '!' — did you mean '!='?")
        elif ch == '<':
            if self.match('='):
                self.add(TT.LTE)
            else:
                self.add(TT.LT)
        elif ch == '>':
            if self.match('='):
                self.add(TT.GTE)
            else:
                self.add(TT.GT)
        elif ch == ':': self.add(TT.COLON)
        elif ch == ',': self.add(TT.COMMA)
        elif ch == '(': self.add(TT.LPAREN)
        elif ch == ')': self.add(TT.RPAREN)
        elif ch == '[': self.add(TT.LBRACKET)
        elif ch == ']': self.add(TT.RBRACKET)
        elif ch == '{': self.add(TT.LBRACE)
        elif ch == '}': self.add(TT.RBRACE)
        elif ch == '.': self.add(TT.DOT)
        elif ch == '|': self.add(TT.PIPE)
        else:
            self.error(f"Unexpected character: '{ch}'")

    def _scan_string(self):
        """Scan a double-quoted string with {expr} interpolation markers."""
        self.advance()  # opening "
        start_line, start_col = self.line, self.col
        chars = []
        raw = []

        while True:
            ch = self.peek()
            if ch is None:
                raise LexError("Unterminated string", start_line, start_col)
            if ch == '"':
                self.advance()
                break
            if ch == '\n':
                raise LexError("Newline inside string — use \\n", start_line, start_col)
            if ch == '\\':
                self.advance()
                esc = self.advance()
                escape_map = {'n': '\n', 't': '\t', '"': '"', '\\': '\\', '{': '{', '}': '}'}
                if esc in escape_map:
                    chars.append(escape_map[esc])
                else:
                    self.error(f"Unknown escape: \\{esc}")
            else:
                chars.append(self.advance())

        raw_str = ''.join(chars)
        self.add(TT.STRING, raw_str)

    def _scan_number(self):
        start = self.pos
        negative = False
        if self.peek() == '-':
            self.advance()
            negative = True

        while self.peek() and self.peek().isdigit():
            self.advance()

        is_float = False
        if self.peek() == '.' and self.peek(1) and self.peek(1).isdigit():
            is_float = True
            self.advance()
            while self.peek() and self.peek().isdigit():
                self.advance()

        raw = self.source[start:self.pos]
        value = float(raw) if is_float else int(raw)
        self.add(TT.NUMBER, value)

    def _scan_ident(self):
        start = self.pos
        while self.peek() and (self.peek().isalnum() or self.peek() == '_'):
            self.advance()
        word = self.source[start:self.pos]
        tt = KEYWORDS.get(word, TT.IDENT)
        if tt == TT.BOOL:
            self.add(TT.BOOL, word == 'true')
        elif tt == TT.NOTHING:
            self.add(TT.NOTHING, None)
        else:
            self.add(tt, word if tt == TT.IDENT else None)
