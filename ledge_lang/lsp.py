"""
Ledge Language Server
Implements the Language Server Protocol (LSP) for Ledge.
Provides: diagnostics, completion, hover, document symbols.

Start with: python -m ledge_lang.lsp
Connect via stdio (default) or TCP: --port 2087

Compatible with VS Code, Neovim, Emacs, Helix, and any LSP-capable editor.
"""

import sys
import json
import threading
import traceback
from typing import Any, Dict, List, Optional


# ── LSP message transport ─────────────────────────────────────────────────────

class LSPTransport:
    """stdio-based LSP message transport."""

    def read_message(self) -> Optional[dict]:
        headers = {}
        while True:
            line = sys.stdin.buffer.readline().decode("utf-8").strip()
            if not line:
                break
            if ":" in line:
                key, _, val = line.partition(":")
                headers[key.strip().lower()] = val.strip()

        length = int(headers.get("content-length", 0))
        if length == 0:
            return None

        body = sys.stdin.buffer.read(length).decode("utf-8")
        return json.loads(body)

    def write_message(self, msg: dict):
        body = json.dumps(msg, ensure_ascii=False)
        encoded = body.encode("utf-8")
        header = f"Content-Length: {len(encoded)}\r\n\r\n"
        sys.stdout.buffer.write(header.encode("utf-8") + encoded)
        sys.stdout.buffer.flush()


# ── Ledge knowledge base ──────────────────────────────────────────────────────


# ── AI-native completions ─────────────────────────────────────────────────────

AI_BUILTINS = [
    {
        "label": "analyze",
        "kind": 3,  # Function
        "detail": "analyze(text) using mode → Uncertain[Map]",
        "documentation": "Analyze text with an AI model. Returns Uncertain[Map] with confidence.\n\nSafety: Without a backend, returns confidence=0.0 and value=nothing.\n\nExample:\n  define result as analyze(text) using sentiment\n  show when(result, 0.8, \"not confident\")",
        "insertText": "analyze(${1:text}) using ${2:sentiment}",
    },
    {
        "label": "classify",
        "kind": 3,
        "detail": "classify(text) using [labels] → Uncertain[text]",
        "documentation": "Classify text into one of the given labels. Returns Uncertain[text].\n\nSafety: Without a backend, returns confidence=0.0 and value=nothing.\n\nExample:\n  define label as classify(email) using [\"urgent\", \"normal\", \"spam\"]\n  show when(label, 0.8, \"unclassified\")",
        "insertText": "classify(${1:text}) using [${2:\"label1\", \"label2\"}]",
    },
    {
        "label": "generate",
        "kind": 3,
        "detail": "generate(prompt) using mode → Uncertain[text]",
        "documentation": "Generate text from a prompt. Returns Uncertain[text].\n\nSafety: Without a backend, returns confidence=0.0 and value=nothing.\n\nExample:\n  define draft as generate(\"Write a summary of: \" + text) using text\n  show when(draft, 0.7, \"generation failed\")",
        "insertText": "generate(${1:prompt}) using ${2:text}",
    },
    {
        "label": "ask",
        "kind": 3,
        "detail": "ask(question) → Uncertain[text]",
        "documentation": "Ask a question and get an AI answer. Returns Uncertain[text].\n\nSafety: Without a backend, returns confidence=0.0 and value=nothing.",
        "insertText": "ask(${1:question})",
    },
    {
        "label": "embed",
        "kind": 3,
        "detail": "embed(text) → Uncertain[list]",
        "documentation": "Get a vector embedding for text. Returns Uncertain[list].\n\nSafety: Without a backend, returns confidence=0.0 and value=nothing.",
        "insertText": "embed(${1:text})",
    },
    {
        "label": "when",
        "kind": 3,
        "detail": "when(uncertain, threshold, fallback) → value",
        "documentation": "Safely extract value from Uncertain only if confidence >= threshold.\nThis is the canonical way to use AI results.\n\nExample:\n  show when(sentiment_result, 0.8, \"not confident\")",
        "insertText": "when(${1:result}, ${2:0.8}, ${3:fallback})",
    },
    {
        "label": "confidence_of",
        "kind": 3,
        "detail": "confidence_of(uncertain) → number [0.0–1.0]",
        "documentation": "Get the confidence level of an Uncertain value.\nAlways in range [0.0, 1.0].",
        "insertText": "confidence_of(${1:result})",
    },
    {
        "label": "value_of",
        "kind": 3,
        "detail": "value_of(uncertain) → T | nothing",
        "documentation": "Extract the value from an Uncertain[T] directly.\nReturns nothing if confidence is 0.0 (no backend).",
        "insertText": "value_of(${1:result})",
    },
    {
        "label": "is_confident",
        "kind": 3,
        "detail": "is_confident(uncertain) → truth",
        "documentation": "Returns true if confidence >= 0.8.",
        "insertText": "is_confident(${1:result})",
    },
    {
        "label": "audit_query",
        "kind": 3,
        "detail": "audit_query(operation?, limit?) → list",
        "documentation": "Query the automatic AI audit trail.\nEvery AI operation (analyze, classify, etc.) is automatically logged.\n\nExample:\n  define log as audit_query()\n  show len(log)",
        "insertText": "audit_query()",
    },
    {
        "label": "uncertain",
        "kind": 3,
        "detail": "uncertain(value, confidence) → Uncertain[T]",
        "documentation": "Create an Uncertain value manually.\nUseful for testing or when wrapping external AI results.",
        "insertText": "uncertain(${1:value}, ${2:0.9})",
    },
    {
        "label": "requires",
        "kind": 14,  # Keyword
        "detail": "requires: — function precondition",
        "documentation": "Declare preconditions for a function.\nThe function body will NOT execute if any precondition fails.\n\nExample:\n  define f(x: number):\n      requires:\n          x > 0\n      return x",
        "insertText": "requires:\n    ${1:condition}",
    },
    {
        "label": "ensures",
        "kind": 14,
        "detail": "ensures: — function postcondition",
        "documentation": "Declare postconditions for a function.\nAn error is raised if the return value violates any postcondition.\nUse 'result' to refer to the return value.\n\nExample:\n  define f(x: number):\n      ensures:\n          result >= 0\n      return abs(x)",
        "insertText": "ensures:\n    result ${1:>= 0}",
    },
]

UNCERTAIN_HOVER = {
    "analyze": "**analyze(text) using mode → Uncertain[Map]**\n\nAnalyze text with AI. Returns `Uncertain[Map]`.\n\nWithout a backend: `confidence = 0.0`, `value = nothing`\n\n```ledge\ndefine r as analyze(text) using sentiment\nshow when(r, 0.8, \"not confident\")\n```",
    "classify": "**classify(text) using [labels] → Uncertain[text]**\n\nClassify text into categories. Returns `Uncertain[text]`.\n\nWithout a backend: `confidence = 0.0`, `value = nothing` (never picks first label)\n\n```ledge\ndefine label as classify(email) using [\"urgent\", \"normal\"]\nshow when(label, 0.8, \"unclassified\")\n```",
    "Uncertain": "**Uncertain[T]**\n\nThe primary AI-native type. Every AI operation returns `Uncertain[T]`.\n\nOperations:\n- `confidence_of(r)` → number in [0.0, 1.0]\n- `value_of(r)` → T or nothing\n- `is_confident(r)` → truth (confidence >= 0.8)\n- `when(r, threshold, fallback)` → T or fallback\n\n**Never use Uncertain values directly — always extract with `when()` or `value_of()`**",
}

KEYWORDS = [
    "define", "as", "set", "to", "show", "for", "each", "in", "if", "else",
    "while", "repeat", "until", "times", "return", "from", "use", "import",
    "export", "is", "not", "and", "or", "given", "check", "when", "otherwise",
    "run", "wait", "parallel", "collect", "stop", "pass", "type", "has",
    "with", "without", "done", "then", "always", "match", "case", "break",
    "continue", "yield", "stream", "recover", "analyze", "generate", "ask",
    "embed", "classify", "using", "list", "map", "native", "true", "false",
    "nothing",
]

BUILTINS = {
    "show":        "show value [as format]\nPrint value to output. Format: text, json, table, raw",
    "len":         "len(value) → number\nLength of text, list, or map",
    "range":       "range(n) → list\nrange(start, end) → list\nGenerate a sequence of numbers",
    "append":      "append(list, item) → list\nReturn new list with item added at end",
    "remove":      "remove(list, item) → list\nReturn new list with first occurrence removed",
    "slice":       "slice(list, start, end?) → list\nReturn a portion of a list",
    "merge":       "merge(a, b) → list|map\nCombine two lists or two maps",
    "join":        "join(list, separator?) → text\nCombine list items into a string",
    "sum":         "sum(list) → number\nSum all numbers in a list",
    "max":         "max(list) → number\nLargest value in a list",
    "min":         "min(list) → number\nSmallest value in a list",
    "sort":        "sort(list) → list\nReturn sorted list",
    "filter":      "filter(list, given x: condition) → list\nKeep items matching condition",
    "map":         "map(list, given x: transform) → list\nTransform every item in a list",
    "has":         "has(container, key) → truth\nCheck if list/map/text contains a value",
    "keys":        "keys(map) → list\nGet all keys from a map",
    "values":      "values(map) → list\nGet all values from a map",
    "split":       "split(text, separator?) → list\nSplit text into a list",
    "trim":        "trim(text) → text\nRemove leading and trailing whitespace",
    "upper":       "upper(text) → text\nConvert to uppercase",
    "lower":       "lower(text) → text\nConvert to lowercase",
    "replace":     "replace(text, old, new) → text\nReplace occurrences in text",
    "contains":    "contains(text, substring) → truth\nCheck if text contains substring",
    "starts_with": "starts_with(text, prefix) → truth\nCheck if text starts with prefix",
    "ends_with":   "ends_with(text, suffix) → truth\nCheck if text ends with suffix",
    "divide":      "divide(a, b) → number|nothing\nSafe division — returns nothing if b = 0",
    "modulo":      "modulo(a, b) → number|nothing\nRemainder — returns nothing if b = 0",
    "power":       "power(base, exp) → number\nRaise base to power",
    "sqrt":        "sqrt(n) → number|nothing\nSquare root — returns nothing if n < 0",
    "abs":         "abs(n) → number\nAbsolute value",
    "round":       "round(n, digits?) → number\nRound to decimal places",
    "floor":       "floor(n) → number\nRound down",
    "ceil":        "ceil(n) → number\nRound up",
    "random":      "random() → number\nrandom(min, max) → number\nRandom number",
    "now":         "now() → number\nCurrent Unix timestamp",
    "json_parse":  "json_parse(text) → map|list\nParse JSON string",
    "json_stringify": "json_stringify(value) → text\nSerialize to JSON",
    "type":        "type(value) → text\nGet type name: text, number, truth, list, map, nothing",
    "number":      "number(value) → number|nothing\nConvert to number",
    "text":        "text(value) → text\nConvert to text",
    "truth":       "truth(value) → truth\nConvert to boolean",
    "error":       "error(message)\nRaise a runtime error",
    "assert":      "assert(condition, message?) \nRaise error if condition is false",
    "analyze":     "analyze(text) using mode → map\nAI: analyze text (sentiment, entities, summary)",
    "generate":    "generate(prompt) using mode → text\nAI: generate text from prompt",
    "ask":         "ask(question) → text\nAI: answer a question",
    "embed":       "embed(text) → list\nAI: get vector embedding",
    "classify":    'classify(text) using ["a", "b"] → text\nAI: classify into categories',
}

STDLIB_MODULES = {
    "time":        "Time utilities: now, sleep, format, timestamp",
    "file":        "File I/O: read, write, append, exists, delete, list, lines, read_json, write_json",
    "http":        "HTTP client: get, post, put, delete, fetch",
    "regex":       "Regular expressions: match, search, find_all, replace, split, test",
    "collections": "Collection utilities: group_by, count_by, unique, flatten, zip, take, drop, reduce, chunk",
    "env":         "Environment variables: get, set, all",
    "math":        "Extended math: pi, e, sin, cos, tan, log, exp, gcd, clamp, lerp, degrees, radians",
    "text":        "Extended text: pad_left, pad_right, center, repeat, count, index_of, lines, words, title_case",
}

COMPLETION_TEMPLATES = {
    "define": "define ${1:name} as ${2:value}",
    "set":    "set ${1:name} to ${2:value}",
    "if":     "if ${1:condition}:\n    ${2:pass}",
    "for":    "for each ${1:item} in ${2:items}:\n    ${3:pass}",
    "while":  "while ${1:condition}:\n    ${2:pass}",
    "match":  "match ${1:value}:\n    case ${2:pattern}:\n        ${3:pass}\n    otherwise:\n        ${4:pass}",
    "check":  "check:\n    ${1:pass}\nrecover ${2:error}:\n    ${3:pass}",
    "type":   "type ${1:Name} has:\n    ${2:field}: ${3:text}",
    "import": 'import "${1:module}" as ${2:alias}',
}


# ── Diagnostic engine ─────────────────────────────────────────────────────────

def get_diagnostics(source: str) -> List[dict]:
    """Run Ledge syntax check and return LSP diagnostics."""
    diagnostics = []
    try:
        from .lexer import Lexer, LexError
        from .parser import Parser, ParseError

        try:
            tokens = Lexer(source).tokenize()
        except LexError as e:
            diagnostics.append({
                "range": {
                    "start": {"line": e.line - 1, "character": e.col - 1},
                    "end": {"line": e.line - 1, "character": e.col + 5},
                },
                "severity": 1,  # Error
                "source": "ledge",
                "message": str(e).split(": ", 1)[-1],
            })
            return diagnostics

        try:
            Parser(tokens).parse()
        except ParseError as e:
            line = max(0, e.line - 1)
            diagnostics.append({
                "range": {
                    "start": {"line": line, "character": 0},
                    "end": {"line": line, "character": 100},
                },
                "severity": 1,
                "source": "ledge",
                "message": str(e).split(": ", 1)[-1],
            })

    except Exception as e:
        pass  # Don't crash the server on unexpected errors

    return diagnostics


# ── LSP Server ────────────────────────────────────────────────────────────────

class LedgeLSP:
    def __init__(self):
        self.transport = LSPTransport()
        self.documents: Dict[str, str] = {}
        self.initialized = False
        self._id_counter = 0

    def _response(self, req_id, result):
        return {"jsonrpc": "2.0", "id": req_id, "result": result}

    def _error_response(self, req_id, code, message):
        return {"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": message}}

    def _notification(self, method, params):
        return {"jsonrpc": "2.0", "method": method, "params": params}

    def serve(self):
        while True:
            try:
                msg = self.transport.read_message()
                if msg is None:
                    break
                response = self._handle(msg)
                if response:
                    self.transport.write_message(response)
            except EOFError:
                break
            except Exception as e:
                sys.stderr.write(f"LSP error: {e}\n{traceback.format_exc()}")

    def _handle(self, msg: dict):
        method = msg.get("method", "")
        req_id = msg.get("id")
        params = msg.get("params", {})

        # Initialization
        if method == "initialize":
            self.initialized = True
            return self._response(req_id, {
                "capabilities": {
                    "textDocumentSync": {
                        "openClose": True,
                        "change": 1,  # Full sync
                    },
                    "completionProvider": {
                        "triggerCharacters": [".", " ", "(", "["],
                        "resolveProvider": False,
                    },
                    "hoverProvider": True,
                    "documentSymbolProvider": True,
                    "diagnosticProvider": {
                        "interFileDependencies": False,
                        "workspaceDiagnostics": False,
                    },
                },
                "serverInfo": {"name": "ledge-lsp", "version": "0.1.0"},
            })

        if method == "initialized":
            return None  # Notification, no response

        if method == "shutdown":
            return self._response(req_id, None)

        if method == "exit":
            sys.exit(0)

        # Document sync
        if method == "textDocument/didOpen":
            uri = params["textDocument"]["uri"]
            text = params["textDocument"]["text"]
            self.documents[uri] = text
            self._publish_diagnostics(uri, text)
            return None

        if method == "textDocument/didChange":
            uri = params["textDocument"]["uri"]
            changes = params["contentChanges"]
            if changes:
                self.documents[uri] = changes[-1]["text"]
                self._publish_diagnostics(uri, self.documents[uri])
            return None

        if method == "textDocument/didClose":
            uri = params["textDocument"]["uri"]
            self.documents.pop(uri, None)
            # Clear diagnostics
            self.transport.write_message(
                self._notification("textDocument/publishDiagnostics", {
                    "uri": uri, "diagnostics": []
                })
            )
            return None

        # Completion
        if method == "textDocument/completion":
            uri = params["textDocument"]["uri"]
            pos = params["position"]
            text = self.documents.get(uri, "")
            items = self._get_completions(text, pos)
            return self._response(req_id, {"isIncomplete": False, "items": items})

        # Hover
        if method == "textDocument/hover":
            uri = params["textDocument"]["uri"]
            pos = params["position"]
            text = self.documents.get(uri, "")
            hover = self._get_hover(text, pos)
            return self._response(req_id, hover)

        # Document symbols
        if method == "textDocument/documentSymbol":
            uri = params["textDocument"]["uri"]
            text = self.documents.get(uri, "")
            symbols = self._get_symbols(text)
            return self._response(req_id, symbols)

        # Unknown request — return null
        if req_id is not None:
            return self._response(req_id, None)

        return None

    def _publish_diagnostics(self, uri: str, text: str):
        diagnostics = get_diagnostics(text)
        self.transport.write_message(
            self._notification("textDocument/publishDiagnostics", {
                "uri": uri,
                "diagnostics": diagnostics,
            })
        )

    def _get_completions(self, text: str, pos: dict) -> List[dict]:
        line_num = pos["line"]
        char = pos["character"]
        lines = text.split("\n")
        current_line = lines[line_num][:char] if line_num < len(lines) else ""
        word = self._current_word(current_line)

        items = []

        # Module member completion: alias.
        if "." in current_line:
            prefix = current_line.rsplit(".", 1)[0].split()[-1] if current_line.rsplit(".", 1)[0].split() else ""
            # Could provide module-specific completions here
            return items

        # Keywords
        for kw in KEYWORDS:
            if not word or kw.startswith(word):
                item = {
                    "label": kw,
                    "kind": 14,  # keyword
                    "sortText": "z" + kw,
                }
                if kw in COMPLETION_TEMPLATES:
                    item["insertText"] = COMPLETION_TEMPLATES[kw]
                    item["insertTextFormat"] = 2  # snippet
                items.append(item)

        # Builtins
        for name, doc in BUILTINS.items():
            if not word or name.startswith(word):
                first_line = doc.split("\n")[0]
                items.append({
                    "label": name,
                    "kind": 3,  # function
                    "detail": first_line,
                    "documentation": {"kind": "markdown", "value": f"```ledge\n{doc}\n```"},
                    "sortText": "a" + name,
                    "insertText": f"{name}(${{1}})",
                    "insertTextFormat": 2,
                })

        # Stdlib imports
        if "import" in current_line:
            for mod, desc in STDLIB_MODULES.items():
                items.append({
                    "label": f'"{mod}"',
                    "kind": 9,  # module
                    "detail": desc,
                    "sortText": "b" + mod,
                })

        # User-defined names from document
        user_names = self._extract_names(text)
        for name in user_names:
            if (not word or name.startswith(word)) and name not in BUILTINS:
                items.append({
                    "label": name,
                    "kind": 6,  # variable
                    "sortText": "c" + name,
                })

        return items

    def _get_hover(self, text: str, pos: dict) -> Optional[dict]:
        line_num = pos["line"]
        char = pos["character"]
        lines = text.split("\n")
        if line_num >= len(lines):
            return None

        line = lines[line_num]
        word = self._word_at(line, char)
        if not word:
            return None

        if word in BUILTINS:
            doc = BUILTINS[word]
            return {
                "contents": {
                    "kind": "markdown",
                    "value": f"**{word}** — built-in\n\n```\n{doc}\n```",
                }
            }

        if word in KEYWORDS:
            descriptions = {
                "define": "Create a new variable or function",
                "set": "Update an existing variable (requires define first)",
                "show": "Print a value to output",
                "for": "Iterate over a list or map",
                "while": "Loop while condition is true",
                "check": "Safe block with error recovery",
                "match": "Pattern matching — exhaustive case handling",
                "given": "Inline lambda function",
                "analyze": "AI instruction: analyze text",
                "generate": "AI instruction: generate text",
                "nothing": "The absence of a value — never crashes",
                "or": "Fallback: if left is nothing, use right",
            }
            if word in descriptions:
                return {
                    "contents": {
                        "kind": "markdown",
                        "value": f"**{word}** — keyword\n\n{descriptions[word]}",
                    }
                }

        if word in STDLIB_MODULES:
            return {
                "contents": {
                    "kind": "markdown",
                    "value": f"**{word}** — stdlib module\n\n{STDLIB_MODULES[word]}",
                }
            }

        return None

    def _get_symbols(self, text: str) -> List[dict]:
        symbols = []
        lines = text.split("\n")
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("define "):
                parts = stripped.split()
                if len(parts) >= 2:
                    name = parts[1].rstrip("(")
                    is_fn = "(" in stripped and "):" in stripped
                    symbols.append({
                        "name": name,
                        "kind": 12 if is_fn else 13,  # function or variable
                        "location": {
                            "range": {
                                "start": {"line": i, "character": 0},
                                "end": {"line": i, "character": len(line)},
                            }
                        },
                    })
            elif stripped.startswith("type "):
                parts = stripped.split()
                if len(parts) >= 2:
                    symbols.append({
                        "name": parts[1],
                        "kind": 5,  # class
                        "location": {
                            "range": {
                                "start": {"line": i, "character": 0},
                                "end": {"line": i, "character": len(line)},
                            }
                        },
                    })
        return symbols

    def _current_word(self, text: str) -> str:
        """Get the word being typed at end of text."""
        import re
        m = re.search(r'[a-zA-Z_][a-zA-Z0-9_]*$', text)
        return m.group(0) if m else ""

    def _word_at(self, line: str, char: int) -> str:
        """Get word at position in line."""
        start = char
        while start > 0 and (line[start-1].isalnum() or line[start-1] == "_"):
            start -= 1
        end = char
        while end < len(line) and (line[end].isalnum() or line[end] == "_"):
            end += 1
        return line[start:end]

    def _extract_names(self, text: str) -> List[str]:
        """Extract defined names from document for completion."""
        import re
        names = []
        for m in re.finditer(r'^define\s+([a-zA-Z_][a-zA-Z0-9_]*)', text, re.MULTILINE):
            names.append(m.group(1))
        for m in re.finditer(r'^type\s+([a-zA-Z_][a-zA-Z0-9_]*)', text, re.MULTILINE):
            names.append(m.group(1))
        return list(set(names))


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Ledge Language Server")
    parser.add_argument("--stdio", action="store_true", default=True,
                        help="Use stdio transport (default)")
    parser.add_argument("--port", type=int, default=None,
                        help="Use TCP transport on this port")
    args = parser.parse_args()

    server = LedgeLSP()

    if args.port:
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("127.0.0.1", args.port))
        sock.listen(1)
        sys.stderr.write(f"Ledge LSP listening on port {args.port}\n")
        conn, _ = sock.accept()
        server.transport = type('TCPTransport', (), {
            'read_message': lambda self: _read_tcp(conn),
            'write_message': lambda self, msg: _write_tcp(conn, msg),
        })()

    server.serve()


def _read_tcp(conn):
    import io
    headers = {}
    buf = b""
    while True:
        byte = conn.recv(1)
        if not byte:
            return None
        buf += byte
        if buf.endswith(b"\r\n\r\n"):
            for line in buf.decode("utf-8").split("\r\n"):
                if ":" in line:
                    k, _, v = line.partition(":")
                    headers[k.strip().lower()] = v.strip()
            break
    length = int(headers.get("content-length", 0))
    body = b""
    while len(body) < length:
        body += conn.recv(length - len(body))
    return json.loads(body)


def _write_tcp(conn, msg):
    body = json.dumps(msg).encode("utf-8")
    header = f"Content-Length: {len(body)}\r\n\r\n".encode("utf-8")
    conn.sendall(header + body)


if __name__ == "__main__":
    main()
