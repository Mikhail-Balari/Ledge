"""
Ledge Debugger v1.0 — ledge debug
====================================
Step-through debugger with AI-native inspection.
Understands Uncertain[T], AuditTrail, Streams, and Contracts.

Commands:
    n / next      — step to next statement
    s / step      — step into function call
    c / continue  — continue to next breakpoint or end
    b N           — set breakpoint at line N
    B             — list all breakpoints
    d N           — delete breakpoint at line N
    p expr        — evaluate and print expression
    v             — show all local variables
    u             — show all Uncertain variables with confidence
    a             — show audit trail (AI decisions so far)
    w expr        — add watch expression
    W             — list watches and their values
    q / quit      — quit debugger
    h / help      — show this help

AI-native commands:
    uncertain     — show all Uncertain values in scope
    audit         — show AI audit trail
    confidence X  — show confidence of variable X
"""

import sys, readline
from .core_types import (
    NOTHING, LedgeList, LedgeMap, LedgeFunction, _repr, _type_of, _truthy
)


class DebugSession:
    def __init__(self, interpreter, source_lines):
        self.interp      = interpreter
        self.source      = source_lines
        self.breakpoints = set()
        self.watches     = []
        self.step_mode   = True   # True = stop at every statement
        self._stopped    = False
        self._history    = []     # execution history for replay
        self._call_depth = 0

    # ── Core hook called before each statement ────────────────────────────────

    def before_stmt(self, node, env):
        """Called by interpreter before executing each statement."""
        line = getattr(node, 'line', 0)
        should_stop = self.step_mode or (line in self.breakpoints)
        if not should_stop:
            self._check_watches(env)
            return
        self._show_context(node, env, line)
        self._check_watches(env)
        self._repl(node, env)

    def _show_context(self, node, env, line):
        """Show current execution context."""
        print()
        print("─" * 60)
        if 0 < line <= len(self.source):
            # Show 2 lines of context
            start = max(0, line - 2)
            for i in range(start, min(line + 1, len(self.source))):
                marker = "►" if i + 1 == line else " "
                print(f"  {marker} {i+1:3d}  {self.source[i]}")
        else:
            print(f"  ► [line {line}] {type(node).__name__}")
        print("─" * 60)

    # ── REPL ──────────────────────────────────────────────────────────────────

    def _repl(self, node, env):
        """Interactive REPL at a breakpoint."""
        while True:
            try:
                cmd = input("(ledge-dbg) ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nQuitting debugger.")
                sys.exit(0)

            if not cmd:
                cmd = "n"

            if cmd in ("n", "next"):
                self.step_mode = True
                return

            elif cmd in ("s", "step"):
                self.step_mode = True
                return

            elif cmd in ("c", "continue"):
                self.step_mode = False
                return

            elif cmd in ("q", "quit", "exit"):
                print("Quitting.")
                sys.exit(0)

            elif cmd in ("v", "vars"):
                self._show_vars(env)

            elif cmd in ("u", "uncertain"):
                self._show_uncertain(env)

            elif cmd in ("a", "audit"):
                self._show_audit()

            elif cmd in ("h", "help", "?"):
                self._show_help()

            elif cmd in ("W", "watches"):
                self._show_watches(env)

            elif cmd in ("B", "breakpoints"):
                if self.breakpoints:
                    print("  Breakpoints: " + ", ".join(f"line {b}" for b in sorted(self.breakpoints)))
                else:
                    print("  No breakpoints set.")

            elif cmd.startswith("b "):
                try:
                    n = int(cmd[2:].strip())
                    self.breakpoints.add(n)
                    print(f"  Breakpoint set at line {n}")
                except ValueError:
                    print("  Usage: b <line_number>")

            elif cmd.startswith("d "):
                try:
                    n = int(cmd[2:].strip())
                    self.breakpoints.discard(n)
                    print(f"  Breakpoint {n} removed")
                except ValueError:
                    print("  Usage: d <line_number>")

            elif cmd.startswith("p "):
                expr_src = cmd[2:].strip()
                self._eval_and_print(expr_src, env)

            elif cmd.startswith("w "):
                expr_src = cmd[2:].strip()
                self.watches.append(expr_src)
                print(f"  Watch added: {expr_src}")

            elif cmd.startswith("confidence "):
                var = cmd[11:].strip()
                self._show_confidence(var, env)

            else:
                # Try to evaluate as expression
                if cmd:
                    self._eval_and_print(cmd, env)

    # ── Display helpers ───────────────────────────────────────────────────────

    def _show_vars(self, env):
        """Show all variables in current scope."""
        if not env._v:
            print("  (no variables in scope)")
            return
        print("\n  Variables in scope:")
        for name, val in sorted(env._v.items()):
            type_str = _type_of(val)
            val_str  = _repr(val)[:50]
            # Special display for AI types
            if type_str.startswith("uncertain"):
                try:
                    conf = val.confidence
                    inner = _repr(val.value)[:30]
                    print(f"    {name}: {type_str} = {inner!r} (confidence: {conf:.2f})")
                except Exception:
                    print(f"    {name}: {type_str} = {val_str}")
            else:
                print(f"    {name}: {type_str} = {val_str}")

    def _show_uncertain(self, env):
        """Show all Uncertain values with confidence levels."""
        uncertain_vars = []
        frame = env
        while frame:
            for name, val in frame._v.items():
                if _type_of(val).startswith("uncertain"):
                    uncertain_vars.append((name, val))
            frame = frame.parent

        if not uncertain_vars:
            print("  No Uncertain values in scope.")
            print("  (Uncertain values come from AI operations: analyze, classify, generate, ask, embed)")
            return

        print(f"\n  Uncertain values ({len(uncertain_vars)}):")
        for name, val in uncertain_vars:
            try:
                conf  = val.confidence
                inner = _repr(val.value)[:40]
                bar   = "█" * int(conf * 10) + "░" * (10 - int(conf * 10))
                safe  = "✓ safe to use" if conf >= 0.8 else "⚠ low confidence"
                print(f"    {name}:")
                print(f"      value:      {inner!r}")
                print(f"      confidence: {bar} {conf:.2f}  {safe}")
                print(f"      source:     {getattr(val, 'source', 'unknown')}")
            except Exception as e:
                print(f"    {name}: {val} (inspect error: {e})")

    def _show_audit(self):
        """Show the AI audit trail accumulated so far."""
        try:
            from .ai_types import GLOBAL_AUDIT
            entries = GLOBAL_AUDIT.query(limit=20)
            if not entries:
                print("  Audit trail: empty (no AI operations executed yet)")
                return
            print(f"\n  AI Audit Trail ({len(entries)} decisions):")
            for entry in entries:
                if isinstance(entry, dict):
                    op   = entry.get("operation", "?")
                    conf = entry.get("confidence", 0)
                    ts   = entry.get("timestamp", "")[:19]
                    print(f"    [{ts}] {op:12s} confidence={conf:.2f}")
                else:
                    print(f"    {entry}")
        except Exception as e:
            print(f"  Could not read audit trail: {e}")

    def _show_confidence(self, var_name, env):
        """Show confidence of a specific Uncertain variable."""
        try:
            val = env.get(var_name)
            t = _type_of(val)
            if t.startswith("uncertain"):
                conf = val.confidence
                bar  = "█" * int(conf * 10) + "░" * (10 - int(conf * 10))
                print(f"  {var_name}: {bar} {conf:.2f}")
                if conf < 0.5:
                    print(f"  ⚠  Low confidence — consider using 'when({var_name}, 0.8, fallback)'")
                elif conf < 0.8:
                    print(f"  ~  Medium confidence — verify before using")
                else:
                    print(f"  ✓  High confidence — safe to use with 'when({var_name}, 0.8, ...)'")
            else:
                print(f"  '{var_name}' is {t}, not Uncertain")
        except Exception as e:
            print(f"  Cannot inspect '{var_name}': {e}")

    def _check_watches(self, env):
        """Evaluate and display watch expressions if they changed."""
        for expr in self.watches:
            try:
                val = self._eval_expr(expr, env)
                print(f"  watch [{expr}] = {_repr(val)[:50]}")
            except Exception:
                pass

    def _show_watches(self, env):
        """Display all watches."""
        if not self.watches:
            print("  No watches. Use 'w expr' to add one.")
            return
        print("  Watches:")
        for expr in self.watches:
            try:
                val = self._eval_expr(expr, env)
                print(f"    {expr} = {_repr(val)[:50]}")
            except Exception as e:
                print(f"    {expr} = <error: {e}>")

    def _eval_and_print(self, expr_src, env):
        """Evaluate an expression and print result."""
        try:
            val = self._eval_expr(expr_src, env)
            t   = _type_of(val)
            if t.startswith("uncertain"):
                conf  = val.confidence
                inner = _repr(val.value)
                print(f"  = {inner!r}  (Uncertain, confidence: {conf:.2f})")
            else:
                print(f"  = {_repr(val)}  [{t}]")
        except Exception as e:
            print(f"  Error: {e}")

    def _eval_expr(self, expr_src, env):
        """Evaluate a Ledge expression string in the current environment."""
        from .lexer import Lexer
        from .parser import Parser
        tokens = Lexer(expr_src + "\n").tokenize()
        ast_node = Parser(tokens).parse()
        # Get the first expression
        if ast_node.stmts:
            stmt = ast_node.stmts[0]
            # Handle show statements (just evaluate the expression)
            if hasattr(stmt, 'expr'):
                return self.interp._eval(stmt.expr, env)
            # Or direct expression statement
            return self.interp._exec(stmt, env)
        return NOTHING

    def _show_help(self):
        print("""
  Debugger commands:
    n / next       Step to next statement
    s / step       Step into function call
    c / continue   Continue to next breakpoint
    b N            Set breakpoint at line N
    d N            Delete breakpoint at line N
    B              List all breakpoints
    p expr         Evaluate and print expression
    v              Show all local variables
    u / uncertain  Show all Uncertain values with confidence
    a / audit      Show AI audit trail
    w expr         Add watch expression
    W              Show all watches
    confidence X   Show confidence of variable X
    q / quit       Quit debugger
""")


# ── Public API ────────────────────────────────────────────────────────────────

def debug_file(path, breakpoints=None):
    """Debug a Ledge file interactively."""
    with open(path, encoding='utf-8') as f:
        source = f.read()
    source_lines = source.split('\n')

    from .lexer import Lexer
    from .parser import Parser
    from .interpreter import Interpreter

    tokens = Lexer(source).tokenize()
    program = Parser(tokens).parse()
    interp = Interpreter()

    session = DebugSession(interp, source_lines)
    if breakpoints:
        session.breakpoints.update(breakpoints)

    # Hook into interpreter
    interp._debug_hook = session.before_stmt

    print(f"Ledge Debugger — {path}")
    print(f"Type 'h' for help, 'n' to step, 'c' to continue, 'q' to quit.")
    if breakpoints:
        print(f"Breakpoints: {sorted(breakpoints)}")
    print()

    try:
        interp.run(program)
        print("\n[Program completed normally]")
    except SystemExit:
        pass
    except Exception as e:
        print(f"\n[Runtime error]: {e}")
