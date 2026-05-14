"""
Ledge is a programming language and governance runtime for auditable, uncertainty-aware AI decisions.

Quick start:
    from ledge_lang import run
    run('show "Hello, Ledge"', output_fn=print)

New in v0.2:
    - Lazy generators: infinite sequences work correctly
    - Python FFI: import "python:numpy" as np
    - Real parallel execution via threading
    - Type enforcement on 'set' (when declared)
    - Error messages with suggestions
    - 0 crashes on adversarial input (fuzzer-verified)
    - 284/284 conformance tests passing (100%)
"""

from .lexer import Lexer, LexError
from .parser import Parser, ParseError
from .interpreter import (
    Interpreter, LedgeError, NOTHING,
    LedgeList, LedgeMap, LedgeFunction, LedgeInstance,
    LedgeLazyGenerator, PythonModule, PythonObject,
    _repr as ledge_repr
)
from .calibration import calibrate, CalibrationReport
from .comparison import compare_models, ModelComparisonReport

try:
    from .audit_store import activate_global_store as _activate_store
    _activate_store()
except Exception:
    pass

__version__ = "1.1.4"
__all__ = [
    "run", "run_file", "compile_ledge", "LedgeREPL",
    "LexError", "ParseError", "LedgeError",
    "NOTHING", "LedgeList", "LedgeMap", "LedgeLazyGenerator",
    "ledge_repr", "__version__",
    "calibrate", "CalibrationReport",
    "compare_models", "ModelComparisonReport",
]


def compile_ledge(source: str):
    """Lex + parse Ledge source. Returns AST Program node."""
    tokens = Lexer(source).tokenize()
    return Parser(tokens).parse()


def run(source: str, output_fn=None, ai_backend=None, env=None, allowed_modules=None, reset_audit=True):
    """
    Run Ledge source code.

    Args:
        source:          Ledge source string
        output_fn:       callable(str) for show output — defaults to silent
        ai_backend:      dict of AI instruction handlers:
                         {"analyze": fn(text, mode), "generate": fn(prompt, mode),
                          "ask": fn(question), "embed": fn(text),
                     "classify": fn(text, labels)}
        env:        optional pre-populated Env

    Returns:
        (output_lines: list[str], final_value)

    Example:
        lines, v = run('show 2 + 2', output_fn=print)
        # prints: 4
        # lines = ['4'], v = NOTHING
    """
    ast = compile_ledge(source)
    # Reset audit trail per run to prevent cross-contamination (H02)
    if reset_audit:
        try:
            from .ai_types import GLOBAL_AUDIT
            GLOBAL_AUDIT.reset()
        except Exception:
            pass
    interp = Interpreter(
        output_fn=output_fn or (lambda x: None),
        ai_backend=ai_backend,
        source=source
    )
    if allowed_modules is not None:
        interp._allowed_modules = set(allowed_modules)
    result = interp.run(ast, env)
    return interp.output_lines, result


def run_file(path: str, output_fn=None, ai_backend=None):
    """Run a .ledge file. output_fn defaults to print."""
    with open(path, encoding="utf-8") as f:
        source = f.read()
    return run(source, output_fn=output_fn or print, ai_backend=ai_backend)


class LedgeREPL:
    """Interactive Read-Eval-Print Loop for Ledge."""

    def __init__(self, ai_backend=None):
        self.interp = Interpreter(ai_backend=ai_backend)
        self.env = self.interp._globals

    def eval_line(self, source: str):
        """Evaluate source. Returns (output_lines, value, error_or_None)."""
        try:
            ast = compile_ledge(source)
            self.interp.output_lines = []
            result = self.interp.run(ast, self.env)
            return self.interp.output_lines, result, None
        except (LexError, ParseError, LedgeError) as e:
            return [], NOTHING, str(e)

    def run(self):
        """Start the interactive REPL."""
        print(f"Ledge {__version__}  —  Type 'stop' to exit, 'help' for help")
        print(f"Tip: import \"python:numpy\" as np  — full Python ecosystem available\n")
        buf = []

        while True:
            try:
                line = input("... " if buf else ">>> ")
            except (EOFError, KeyboardInterrupt):
                print("\nGoodbye.")
                break

            if line.strip() == "stop":
                print("Goodbye."); break

            if line.strip() == "help":
                print("""
Ledge REPL help:
  stop               Exit
  help               This message
  show expr          Print value
  define x as val    Create variable
  import "math" as m Use stdlib
  import "python:numpy" as np  Use Python packages

Keywords: define, set, if, else, for, while, match, check, recover,
          return, yield, parallel, given, type, import, show, pass
""")
                continue

            buf.append(line)
            source = "\n".join(buf)

            try:
                ast = compile_ledge(source)
                self.interp.output_lines = []
                result = self.interp.run(ast, self.env)
                if result is not NOTHING and not self.interp.output_lines:
                    print(ledge_repr(result))
                buf = []
            except ParseError as e:
                msg = str(e)
                if "Expected indented block" in msg:
                    pass  # keep buffering
                else:
                    print(f"  {e}"); buf = []
            except (LexError, LedgeError) as e:
                print(f"  {e}"); buf = []

# Optional: AI backends (require pip install openai / pip install anthropic)
def get_backend(provider: str = "auto", api_key: str = None):
    """
    Get an AI backend for Ledge.
    
    Args:
        provider: "openai", "anthropic", or "auto" (default)
        api_key: API key (or use OPENAI_API_KEY / ANTHROPIC_API_KEY env vars)
    
    Returns:
        Backend dict for use with run(..., ai_backend=backend)
        Returns None if no provider is available.
    
    Example:
        backend = get_backend()  # auto-detect from environment
        if backend:
            lines, _ = run(source, ai_backend=backend)
    """
    from .backends import auto_backend, openai_backend, anthropic_backend
    if provider == "auto":
        return auto_backend()
    elif provider == "openai":
        return openai_backend(api_key=api_key)
    elif provider == "anthropic":
        return anthropic_backend(api_key=api_key)
    else:
        raise ValueError(f"Unknown provider: {provider}. Use: auto, openai, anthropic")
