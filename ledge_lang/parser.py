"""
Ledge Language — Parser
Recursive descent. One canonical parse per construct.
"""

from typing import List, Optional, Tuple
from .lexer import Token, TT
from .ast_nodes import *


class ParseError(Exception):
    def __init__(self, msg, line=0):
        super().__init__(f"[Line {line}] Parse error: {msg}" if line else f"Parse error: {msg}")
        self.line = line


class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = [t for t in tokens if t.type != TT.NEWLINE]
        self.pos = 0

    def current(self) -> Token:
        return self.tokens[self.pos] if self.pos < len(self.tokens) else Token(TT.EOF, None, 0, 0)

    def peek(self, offset=1) -> Token:
        p = self.pos + offset
        return self.tokens[p] if p < len(self.tokens) else Token(TT.EOF, None, 0, 0)

    def check(self, *types) -> bool:
        return self.current().type in types

    def match(self, *types) -> bool:
        if self.check(*types):
            self.pos += 1
            return True
        return False

    def consume(self, tt, msg=None) -> Token:
        if self.current().type == tt:
            t = self.current()
            self.pos += 1
            return t
        got = self.current()
        raise ParseError(msg or f"Expected {tt.name}, got {got.type.name} ({got.value!r})", got.line)

    def error(self, msg):
        raise ParseError(msg, self.current().line)

    # ── Entry ──────────────────────────────────────────────────────────────────

    def parse(self) -> Program:
        stmts = []
        while not self.check(TT.EOF):
            stmts.append(self.parse_stmt())
        return Program(stmts=stmts)

    def parse_expr_entry(self) -> Node:
        """Parse a single expression (used by REPL and string interpolation)."""
        return self.parse_expr()

    # ── Statements ─────────────────────────────────────────────────────────────

    def parse_stmt(self) -> Node:
        t = self.current().type
        if t == TT.DEFINE:   return self.parse_define()
        if t == TT.SET:      return self.parse_assign()
        if t == TT.SHOW:     return self.parse_show()
        if t == TT.IF:       return self.parse_if()
        if t == TT.FOR:      return self.parse_for()
        if t == TT.WHILE:    return self.parse_while()
        if t == TT.REPEAT:   return self.parse_repeat()
        if t == TT.MATCH:    return self.parse_match()
        if t == TT.CHECK:    return self.parse_check()
        if t == TT.RETURN:   return self.parse_return()
        if t == TT.BREAK:    self.pos += 1; return Break()
        if t == TT.CONTINUE: self.pos += 1; return Continue()
        if t == TT.PASS:     self.pos += 1; return Pass()
        if t == TT.YIELD:    return self.parse_yield()
        if t == TT.RUN:      return self.parse_run()
        if t == TT.WHEN:     return self._parse_when_stmt()
        if t == TT.EMIT:     return self._parse_emit_stmt()
        if t == TT.SUBSCRIBE: return self._parse_subscribe_stmt()
        if t == TT.AGENT:    return self._parse_agent_def()
        if t == TT.IMPORT:   return self.parse_import()
        if t == TT.FROM:     return self.parse_from_import()
        if t == TT.TYPE:     return self.parse_type_def()
        return ExprStmt(expr=self.parse_expr())

    def parse_define(self) -> Define:
        self.consume(TT.DEFINE)
        # Allow keywords as function/variable names after 'define'
        tok = self.current()
        if tok.type == TT.IDENT:
            name = tok.value
            self.pos += 1
        elif tok.value is not None:
            # keyword used as name (e.g., define classify(...))
            name = tok.value
            self.pos += 1
        else:
            # keyword with no value - use its name as identifier
            name = tok.type.name.lower()
            self.pos += 1
        if not name:
            self.error("Expected name after 'define'")

        # Function: define name(params): [requires:] [ensures:]
        if self.check(TT.LPAREN):
            self.pos += 1
            params = self.parse_params()
            self.consume(TT.RPAREN)
            self.consume(TT.COLON)
            # Parse the block, extracting contract clauses from the front
            body, contract = self._parse_block_with_contracts()
            is_gen = self._has_yield(body)
            fn = FuncDef(params=params, body=body, is_generator=is_gen, contract=contract)
            return Define(name=name, type_hint=None, value=fn)

        # Optional type hint
        hint = None
        if self.check(TT.COLON):
            self.pos += 1
            hint = self.parse_type_hint()

        self.consume(TT.AS, "Expected 'as' after variable name in 'define'")
        value = self.parse_fallback_expr()
        return Define(name=name, type_hint=hint, value=value)

    def _has_yield(self, node) -> bool:
        if isinstance(node, Yield): return True
        for v in vars(node).values():
            if isinstance(v, Node) and self._has_yield(v): return True
            if isinstance(v, list):
                for item in v:
                    if isinstance(item, Node) and self._has_yield(item): return True
                    if isinstance(item, tuple):
                        for x in item:
                            if isinstance(x, Node) and self._has_yield(x): return True
        return False

    def parse_type_hint(self) -> str:
        if self.current().type == TT.LIST: self.pos += 1; return "list"
        if self.current().type == TT.MAP:  self.pos += 1; return "map"
        if self.current().type == TT.IDENT:
            v = self.current().value; self.pos += 1; return v
        self.error("Expected type hint (text, number, truth, list, map, any, or type name)")

    def parse_params(self) -> List[Tuple[str, Optional[str]]]:
        params = []
        if not self.check(TT.RPAREN):
            while True:
                name = self.consume(TT.IDENT, "Expected parameter name").value
                hint = None
                if self.check(TT.COLON):
                    self.pos += 1
                    hint = self.parse_type_hint()
                params.append((name, hint))
                if not self.match(TT.COMMA): break
        return params

    def parse_assign(self) -> Assign:
        self.consume(TT.SET)
        name = self.consume(TT.IDENT, "Expected variable name after 'set'").value
        self.consume(TT.TO, "Expected 'to' after variable name")
        return Assign(name=name, value=self.parse_fallback_expr())

    def parse_show(self) -> Show:
        self.consume(TT.SHOW)
        expr = self.parse_expr()
        fmt = None
        if self.match(TT.AS):
            if self.check(TT.TABLE):   fmt = "table"; self.pos += 1
            elif self.check(TT.JSON):  fmt = "json";  self.pos += 1
            elif self.check(TT.RAW):   fmt = "raw";   self.pos += 1
            elif self.check(TT.IDENT): fmt = self.current().value; self.pos += 1
        return Show(expr=expr, format=fmt)

    def parse_if(self) -> If:
        self.consume(TT.IF)
        cond = self.parse_condition()
        self.consume(TT.COLON)
        body = self.parse_block()
        branches = [(cond, body)]

        while self.check(TT.ELSE) and self.peek().type == TT.IF:
            self.pos += 2
            c = self.parse_condition()
            self.consume(TT.COLON)
            b = self.parse_block()
            branches.append((c, b))

        else_block = None
        if self.check(TT.ELSE):
            self.pos += 1
            self.consume(TT.COLON)
            else_block = self.parse_block()

        return If(branches=branches, else_block=else_block)

    def parse_for(self) -> For:
        self.consume(TT.FOR)
        self.consume(TT.EACH, "Expected 'each' after 'for'")
        var = self.consume(TT.IDENT, "Expected variable name").value
        var2 = None
        if self.match(TT.COMMA):
            var2 = self.consume(TT.IDENT, "Expected second variable").value
        self.consume(TT.IN, "Expected 'in'")
        iterable = self.parse_expr()
        self.consume(TT.COLON)
        return For(var=var, var2=var2, iterable=iterable, body=self.parse_block())

    def parse_while(self) -> While:
        self.consume(TT.WHILE)
        cond = self.parse_condition()
        self.consume(TT.COLON)
        return While(condition=cond, body=self.parse_block())

    def parse_repeat(self) -> Repeat:
        self.consume(TT.REPEAT)
        if self.check(TT.UNTIL):
            self.pos += 1
            cond = self.parse_condition()
            self.consume(TT.COLON)
            return Repeat(count=None, condition=cond, body=self.parse_block())
        count = self.parse_expr()
        self.consume(TT.TIMES, "Expected 'times'")
        self.consume(TT.COLON)
        return Repeat(count=count, condition=None, body=self.parse_block())

    def parse_match(self) -> Match:
        self.consume(TT.MATCH)
        subject = self.parse_expr()
        self.consume(TT.COLON)
        self.consume(TT.INDENT)
        cases, otherwise = [], None
        while not self.check(TT.DEDENT) and not self.check(TT.EOF):
            if self.check(TT.CASE):
                self.pos += 1
                val = self.parse_expr()
                self.consume(TT.COLON)
                cases.append((val, self.parse_block()))
            elif self.check(TT.OTHERWISE):
                self.pos += 1
                self.consume(TT.COLON)
                otherwise = self.parse_block()
            else:
                self.error("Expected 'case' or 'otherwise'")
        self.consume(TT.DEDENT)
        return Match(subject=subject, cases=cases, otherwise=otherwise)

    def parse_check(self) -> Check:
        self.consume(TT.CHECK)
        self.consume(TT.COLON)
        body = self.parse_block()
        rv, rb, ab = None, None, None
        if self.check(TT.RECOVER):
            self.pos += 1
            if self.check(TT.IDENT): rv = self.current().value; self.pos += 1
            self.consume(TT.COLON)
            rb = self.parse_block()
        if self.check(TT.ALWAYS):
            self.pos += 1
            self.consume(TT.COLON)
            ab = self.parse_block()
        return Check(body=body, recover_var=rv, recover_block=rb, always_block=ab)

    def parse_return(self) -> Return:
        self.consume(TT.RETURN)
        if self.check(TT.DEDENT) or self.check(TT.EOF) or self.check(TT.INDENT):
            return Return(value=None)
        # Check if next token starts a new statement
        stmt_starters = {TT.DEFINE, TT.SET, TT.SHOW, TT.IF, TT.FOR, TT.WHILE,
                         TT.REPEAT, TT.MATCH, TT.CHECK, TT.RETURN, TT.BREAK,
                         TT.CONTINUE, TT.PASS, TT.YIELD, TT.RUN}
        if self.current().type in stmt_starters:
            return Return(value=None)
        return Return(value=self.parse_expr())

    def parse_yield(self) -> Yield:
        self.consume(TT.YIELD)
        return Yield(value=self.parse_expr())

    def parse_run(self) -> RunStmt:
        self.consume(TT.RUN)
        expr = self.parse_expr()
        wait = False
        if self.check(TT.AND):
            self.pos += 1
            self.consume(TT.WAIT, "Expected 'wait' after 'and'")
            wait = True
        return RunStmt(expr=expr, wait=wait)

    def parse_import(self) -> Import:
        self.consume(TT.IMPORT)
        path = self.consume(TT.STRING, "Expected module path").value
        self.consume(TT.AS, "Expected 'as'")
        alias = self.consume(TT.IDENT, "Expected alias").value
        return Import(path=path, alias=alias, names=[])

    def parse_from_import(self) -> Import:
        self.consume(TT.FROM)
        path = self.consume(TT.STRING, "Expected module path").value
        self.consume(TT.IMPORT)
        names = []
        while True:
            names.append(self.consume(TT.IDENT, "Expected name").value)
            if not self.match(TT.COMMA): break
        return Import(path=path, alias=None, names=names)

    def parse_type_def(self) -> TypeDef:
        self.consume(TT.TYPE)
        name = self.consume(TT.IDENT, "Expected type name").value
        self.consume(TT.HAS, "Expected 'has'")
        self.consume(TT.COLON)
        self.consume(TT.INDENT)
        fields = []
        while not self.check(TT.DEDENT) and not self.check(TT.EOF):
            fname = self.consume(TT.IDENT, "Expected field name").value
            ftype = None
            fdefault = None
            if self.check(TT.COLON):
                self.pos += 1
                ftype = self.parse_type_hint()
            if self.match(TT.EQ):
                fdefault = self.parse_expr()
            fields.append((fname, ftype, fdefault))
        self.consume(TT.DEDENT)
        return TypeDef(name=name, fields=fields)

    # ── Block ──────────────────────────────────────────────────────────────────

    def parse_block(self) -> Block:
        self.consume(TT.INDENT, "Expected indented block (4 spaces)")
        stmts = []
        while not self.check(TT.DEDENT) and not self.check(TT.EOF):
            stmts.append(self.parse_stmt())
        self.consume(TT.DEDENT)
        if not stmts:
            self.error("Empty block — use 'pass' for an intentionally empty block")
        return Block(stmts=stmts)

    # ── Expressions ────────────────────────────────────────────────────────────

    def parse_fallback_expr(self) -> Node:
        """Parse expr with optional 'or default' fallback."""
        expr = self.parse_expr()
        if self.check(TT.OR):
            self.pos += 1
            default = self.parse_expr()
            return Fallback(expr=expr, default=default)
        return expr

    def parse_condition(self) -> Node:
        return self.parse_or_cond()

    def parse_or_cond(self) -> Node:
        left = self.parse_and_cond()
        while self.check(TT.OR):
            self.pos += 1
            left = LogicalOp(op="or", left=left, right=self.parse_and_cond())
        return left

    def parse_and_cond(self) -> Node:
        left = self.parse_not_cond()
        while self.check(TT.AND):
            self.pos += 1
            left = LogicalOp(op="and", left=left, right=self.parse_not_cond())
        return left

    def parse_not_cond(self) -> Node:
        if self.check(TT.NOT):
            self.pos += 1
            return UnaryOp(op="not", operand=self.parse_not_cond())
        return self.parse_comparison()

    def parse_expr(self) -> Node:
        return self.parse_or_expr()

    def parse_or_expr(self) -> Node:
        left = self.parse_and_expr()
        while self.check(TT.OR):
            self.pos += 1
            left = LogicalOp(op="or", left=left, right=self.parse_and_expr())
        return left

    def parse_and_expr(self) -> Node:
        left = self.parse_not_expr()
        while self.check(TT.AND):
            self.pos += 1
            left = LogicalOp(op="and", left=left, right=self.parse_not_expr())
        return left

    def parse_not_expr(self) -> Node:
        if self.check(TT.NOT):
            self.pos += 1
            return UnaryOp(op="not", operand=self.parse_not_expr())
        return self.parse_comparison()

    def parse_comparison(self) -> Node:
        left = self.parse_arithmetic()
        if self.check(TT.IS):
            self.pos += 1
            negated = False
            if self.check(TT.NOT):
                self.pos += 1
                negated = True
            return IsOp(negated=negated, left=left, right=self.parse_arithmetic())
        op_map = {TT.EQ:"=", TT.NEQ:"!=", TT.LT:"<", TT.GT:">", TT.LTE:"<=", TT.GTE:">="}
        if self.current().type in op_map:
            op = op_map[self.current().type]; self.pos += 1
            return BinOp(op=op, left=left, right=self.parse_arithmetic())
        return left

    def parse_arithmetic(self) -> Node:
        left = self.parse_term()
        while self.check(TT.PLUS, TT.MINUS):
            op = "+" if self.current().type == TT.PLUS else "-"
            self.pos += 1
            left = BinOp(op=op, left=left, right=self.parse_term())
        return left

    def parse_term(self) -> Node:
        left = self.parse_unary()
        while self.check(TT.STAR, TT.SLASH):
            op = "*" if self.current().type == TT.STAR else "/"
            self.pos += 1
            left = BinOp(op=op, left=left, right=self.parse_unary())
        return left

    def parse_unary(self) -> Node:
        if self.check(TT.MINUS):
            self.pos += 1
            return UnaryOp(op="-", operand=self.parse_postfix())
        return self.parse_postfix()

    def parse_postfix(self) -> Node:
        node = self.parse_primary()
        while True:
            if self.check(TT.LPAREN):
                node = self._parse_call(node)
            elif self.check(TT.LBRACKET):
                self.pos += 1
                key = self.parse_expr()
                self.consume(TT.RBRACKET)
                node = Index(obj=node, key=key)
            elif self.check(TT.DOT):
                self.pos += 1
                name = self.consume(TT.IDENT, "Expected field name after '.'").value
                node = Field(obj=node, name=name)
            elif self.check(TT.PIPE):
                node = self._parse_pipe_chain(node)
            else:
                break
        return node

    def _parse_call(self, callee: Node) -> Call:
        self.consume(TT.LPAREN)
        args, kwargs = [], {}
        if not self.check(TT.RPAREN):
            while True:
                if self.check(TT.IDENT) and self.peek().type == TT.EQ:
                    k = self.current().value; self.pos += 2
                    kwargs[k] = self.parse_expr()
                else:
                    args.append(self.parse_expr())
                if not self.match(TT.COMMA): break
        self.consume(TT.RPAREN)
        using = None
        if self.check(TT.USING):
            self.pos += 1
            if self.check(TT.IDENT):
                using = self.current().value; self.pos += 1
            # else: using something else (handled by ClassifyExpr directly)
        return Call(callee=callee, args=args, kwargs=kwargs, using=using)


    def _is_ai_call(self, keyword_type) -> bool:
        """Check if a keyword token is being used as an AI instruction (has 'using').
        Returns True if this looks like: KEYWORD LPAREN ... RPAREN USING
        Returns False if it's a user-defined function call."""
        # Look ahead for 'using' after the matching closing paren
        depth = 0
        for i in range(self.pos + 1, min(self.pos + 80, len(self.tokens))):
            tt = self.tokens[i].type
            if tt in (TT.LPAREN, TT.LBRACKET, TT.LBRACE): depth += 1
            elif tt in (TT.RPAREN, TT.RBRACKET, TT.RBRACE):
                depth -= 1
                if depth == 0:
                    # This is the closing paren matching the first open
                    next_i = i + 1
                    if next_i < len(self.tokens) and self.tokens[next_i].type == TT.USING:
                        return True
                    return False
            elif tt in (TT.DEDENT, TT.EOF, TT.NEWLINE):
                return False
        return False


    def _parse_stream_expr(self) -> Node:
        """stream from "url" | where cond | transform x: expr"""
        self.consume(TT.STREAM)
        source = None
        source_type = "list"
        filters = []
        transforms = []
        window_size = None
        window_unit = "items"

        if self.check(TT.FROM):
            self.pos += 1
            source = self.parse_expr()
            source_type = "url"
        elif self.check(TT.LBRACKET):
            # stream [1, 2, 3] — inline list stream
            source = self.parse_primary()
            source_type = "list"
        else:
            # stream of — just a stream type
            source_type = "empty"

        # Parse pipe chain
        while self.check(TT.PIPE):
            self.pos += 1
            if self.check(TT.WHERE):
                self.pos += 1
                var = None
                if self.check(TT.IDENT) and self.peek().type == TT.COLON:
                    var = self.current().value; self.pos += 2
                filters.append(self.parse_expr())
            elif self.check(TT.WINDOW):
                self.pos += 1
                window_size = self.parse_expr()
                if self.check(TT.SECONDS):
                    window_unit = "seconds"; self.pos += 1
                elif self.check(TT.MINUTES):
                    window_unit = "minutes"; self.pos += 1
            elif self.check(TT.IDENT) and self.current().value == "transform":
                self.pos += 1
                var = None
                if self.check(TT.IDENT) and self.peek().type == TT.COLON:
                    var = self.current().value; self.pos += 2
                transforms.append(self.parse_expr())
            else:
                break

        return StreamExpr(
            source=source, source_type=source_type,
            filters=filters, transforms=transforms,
            window_size=window_size, window_unit=window_unit
        )

    def _parse_pipe_chain(self, left: Node) -> Node:
        """Handle | operator for stream chaining: stream | where | transform"""
        from .ast_nodes import StreamExpr
        self.consume(TT.PIPE)
        # Build a pipe operation: left | right
        # Represented as a Call to a builtin pipe function
        if self.check(TT.WHERE):
            self.pos += 1
            cond = self.parse_expr()
            # stream_where(left, given item: cond)
            return Call(
                callee=Identifier(name="stream_where"),
                args=[left, Lambda(params=["_item"], body=cond)],
                kwargs={}, using=None
            )
        elif self.check(TT.IDENT) and self.current().value in ("transform", "map_stream"):
            self.pos += 1
            if self.check(TT.IDENT) and self.peek().type == TT.COLON:
                var = self.current().value; self.pos += 2
                expr = self.parse_expr()
                return Call(
                    callee=Identifier(name="stream_map"),
                    args=[left, Lambda(params=[var], body=expr)],
                    kwargs={}, using=None
                )
            fn = self.parse_expr()
            return Call(callee=Identifier(name="stream_map"), args=[left, fn], kwargs={}, using=None)
        elif self.check(TT.IDENT) and self.current().value == "take":
            self.pos += 1
            n = self.parse_expr()
            return Call(callee=Identifier(name="stream_take"), args=[left, n], kwargs={}, using=None)
        elif self.check(TT.IDENT) and self.current().value == "collect":
            self.pos += 1
            return Call(callee=Identifier(name="stream_collect"), args=[left], kwargs={}, using=None)
        else:
            # Generic pipe: passes left as first arg to next call
            fn = self.parse_postfix()
            if isinstance(fn, Call):
                fn.args.insert(0, left)
                return fn
            return Call(callee=fn, args=[left], kwargs={}, using=None)

    def _parse_when_stmt(self) -> Node:
        """when stream has new item as name: block
           when condition: block"""
        self.consume(TT.WHEN)
        source = self.parse_expr()
        item_name = None
        trigger = "condition"

        if self.check(TT.HAS):
            self.pos += 1
            # "has new item as name"
            if self.check(TT.IDENT) and self.current().value == "new":
                self.pos += 1  # skip "new"
            if self.check(TT.IDENT) and self.current().value == "item":
                self.pos += 1  # skip "item"
            trigger = "has_new_item"
            if self.check(TT.AS):
                self.pos += 1
                item_name = self.consume(TT.IDENT, "Expected item name after 'as'").value

        self.consume(TT.COLON)
        body = self.parse_block()
        return WhenStmt(source=source, trigger=trigger, item_name=item_name, body=body)

    def _parse_emit_stmt(self) -> Node:
        """emit value [to stream]"""
        self.consume(TT.EMIT)
        value = self.parse_expr()
        target = None
        if self.check(TT.TO):
            self.pos += 1
            target = self.parse_expr()
        return EmitStmt(value=value, target=target)

    def _parse_subscribe_stmt(self) -> Node:
        """subscribe to stream as name: block"""
        self.consume(TT.SUBSCRIBE)
        if self.check(TT.TO):
            self.pos += 1
        source = self.parse_expr()
        item_name = "_item"
        if self.check(TT.AS):
            self.pos += 1
            item_name = self.consume(TT.IDENT).value
        self.consume(TT.COLON)
        body = self.parse_block()
        return SubscribeStmt(source=source, item_name=item_name, body=body)

    def _parse_mcp_expr(self) -> Node:
        """mcp "server" [at "url"]"""
        self.consume(TT.MCP)
        server = self.parse_expr()
        url = None
        if self.check(TT.AT) if hasattr(TT, 'AT') else False:
            self.pos += 1
            url = self.parse_expr()
        return MCPExpr(server=server, url=url)

    def _parse_block_with_contracts(self):
        """Parse a function body, extracting requires:/ensures: from the front."""
        self.consume(TT.INDENT, "Expected indented block (4 spaces)")
        requires = []
        ensures = []
        req_descs = []
        ens_descs = []
        stmts = []
        
        # Extract contract clauses at start
        while not self.check(TT.DEDENT) and not self.check(TT.EOF):
            if self.check(TT.REQUIRES):
                self.pos += 1
                self.consume(TT.COLON)
                self.consume(TT.INDENT)
                while not self.check(TT.DEDENT) and not self.check(TT.EOF):
                    expr = self.parse_expr()
                    requires.append(expr)
                    req_descs.append(getattr(expr, '__repr__', lambda: "condition")())
                self.consume(TT.DEDENT)
            elif self.check(TT.ENSURES):
                self.pos += 1
                self.consume(TT.COLON)
                self.consume(TT.INDENT)
                while not self.check(TT.DEDENT) and not self.check(TT.EOF):
                    expr = self.parse_expr()
                    ensures.append(expr)
                    ens_descs.append(getattr(expr, '__repr__', lambda: "condition")())
                self.consume(TT.DEDENT)
            else:
                stmts.append(self.parse_stmt())
        
        self.consume(TT.DEDENT)
        
        if not stmts:
            self.error("Empty function body — use 'pass' for intentionally empty function")
        
        body = Block(stmts=stmts)
        contract = None
        if requires or ensures:
            contract = FuncContract(
                requires=requires, ensures=ensures,
                require_descs=req_descs, ensure_descs=ens_descs
            )
        return body, contract

    def _parse_contract(self):
        """Parse optional requires: and ensures: blocks (legacy, kept for compatibility)."""

    def _parse_contract(self):
        """Parse optional requires: and ensures: blocks after function signature."""
        requires = []
        ensures = []
        req_descs = []
        ens_descs = []

        while self.check(TT.REQUIRES) or self.check(TT.ENSURES):
            is_requires = self.check(TT.REQUIRES)
            self.pos += 1
            self.consume(TT.COLON)
            self.consume(TT.INDENT)
            while not self.check(TT.DEDENT) and not self.check(TT.EOF):
                expr = self.parse_expr()
                desc = getattr(expr, '_desc', repr(expr))
                if is_requires:
                    requires.append(expr)
                    req_descs.append(desc)
                else:
                    ensures.append(expr)
                    ens_descs.append(desc)
            self.consume(TT.DEDENT)

        if requires or ensures:
            return FuncContract(
                requires=requires, ensures=ensures,
                require_descs=req_descs, ensure_descs=ens_descs
            )
        return None

    def _parse_agent_def(self) -> Node:
        """agent name: tools: ... model: ... behavior: ..."""
        self.consume(TT.AGENT)
        name = self.consume(TT.IDENT, "Expected agent name").value
        self.consume(TT.COLON)
        self.consume(TT.INDENT)
        tools = []
        model_expr = None
        behavior_block = None

        while not self.check(TT.DEDENT) and not self.check(TT.EOF):
            if self.check(TT.TOOLS):
                self.pos += 1
                self.consume(TT.COLON)
                self.consume(TT.INDENT)
                while not self.check(TT.DEDENT):
                    tool_name = self.consume(TT.IDENT).value
                    self.consume(TT.FROM)
                    self.consume(TT.MCP)
                    source = self.parse_expr()
                    tools.append((tool_name, source))
                self.consume(TT.DEDENT)
            elif self.check(TT.MODEL):
                self.pos += 1
                self.consume(TT.COLON)
                model_expr = self.parse_expr()
            elif self.check(TT.BEHAVIOR):
                self.pos += 1
                self.consume(TT.COLON)
                behavior_block = self.parse_block()
            else:
                self.parse_stmt()  # skip unknown

        self.consume(TT.DEDENT)
        return AgentDef(
            name=name,
            tools=tools,
            model_name=model_expr or StringLit(value="claude-sonnet-4-6"),
            behavior=behavior_block or Block(stmts=[Pass()])
        )

    def parse_primary(self) -> Node:
        t = self.current()

        if t.type == TT.NUMBER:    self.pos += 1; return NumberLit(value=t.value)
        if t.type == TT.BOOL:      self.pos += 1; return BoolLit(value=t.value)
        if t.type == TT.NOTHING:   self.pos += 1; return NothingLit()
        if t.type == TT.STRING:    self.pos += 1; return StringLit(value=t.value)

        if t.type == TT.LIST:
            # If followed by LPAREN, treat as function call (list() cast)
            if self.peek().type == TT.LPAREN:
                self.pos += 1
                node = Identifier(name="list")
                return node
            self.pos += 1
            self.consume(TT.LBRACKET)
            elems = []
            if not self.check(TT.RBRACKET):
                while True:
                    elems.append(self.parse_expr())
                    if not self.match(TT.COMMA): break
            self.consume(TT.RBRACKET)
            return ListLit(elements=elems)

        if t.type == TT.MAP:
            # If followed by LPAREN, treat as function call (map builtin)
            if self.peek().type == TT.LPAREN:
                self.pos += 1
                node = Identifier(name="map")
                return node
            self.pos += 1
            self.consume(TT.LBRACE)
            pairs = []
            if not self.check(TT.RBRACE):
                while True:
                    k = self.parse_expr()
                    self.consume(TT.COLON)
                    v = self.parse_expr()
                    pairs.append((k, v))
                    if not self.match(TT.COMMA): break
            self.consume(TT.RBRACE)
            return MapLit(pairs=pairs)

        if t.type == TT.LPAREN:
            self.pos += 1
            expr = self.parse_expr()
            self.consume(TT.RPAREN)
            return expr

        if t.type == TT.PARALLEL:
            self.pos += 1
            self.consume(TT.LBRACKET)
            exprs = []
            if not self.check(TT.RBRACKET):
                while True:
                    exprs.append(self.parse_expr())
                    if not self.match(TT.COMMA): break
            self.consume(TT.RBRACKET)
            return ParallelExpr(exprs=exprs)

        if t.type == TT.STREAM:
            return self._parse_stream_expr()

        if t.type == TT.PIPE:
            self.error("'|' must follow a stream expression")

        if t.type == TT.MCP:
            return self._parse_mcp_expr()

        if t.type == TT.GIVEN:
            self.pos += 1
            if self.check(TT.LPAREN):
                self.pos += 1
                params = [p[0] for p in self.parse_params()]
                self.consume(TT.RPAREN)
            else:
                params = [self.consume(TT.IDENT).value]
            self.consume(TT.COLON)
            return Lambda(params=params, body=self.parse_expr())

        if t.type == TT.ANALYZE:
            if self._is_ai_call(TT.ANALYZE):
                self.pos += 1; self.consume(TT.LPAREN)
                text = self.parse_expr(); self.consume(TT.RPAREN)
                self.consume(TT.USING)
                mode = self.consume(TT.IDENT).value
                return AnalyzeExpr(text=text, mode=mode)
            else:
                self.pos += 1; return Identifier(name="analyze")

        if t.type == TT.GENERATE:
            if self._is_ai_call(TT.GENERATE):
                self.pos += 1; self.consume(TT.LPAREN)
                prompt = self.parse_expr(); self.consume(TT.RPAREN)
                self.consume(TT.USING)
                mode = self.consume(TT.IDENT).value
                return GenerateExpr(prompt=prompt, mode=mode)
            else:
                self.pos += 1; return Identifier(name="generate")

        if t.type == TT.ASK:
            self.pos += 1; self.consume(TT.LPAREN)
            q = self.parse_expr(); self.consume(TT.RPAREN)
            return AskExpr(question=q)

        if t.type == TT.EMBED:
            self.pos += 1; self.consume(TT.LPAREN)
            text = self.parse_expr(); self.consume(TT.RPAREN)
            return EmbedExpr(text=text)

        if t.type == TT.CLASSIFY:
            # If followed by ( ... ) using [...], it's an AI classify instruction
            # Otherwise treat as a user-defined function call named 'classify'
            if self._is_ai_call(TT.CLASSIFY):
                self.pos += 1; self.consume(TT.LPAREN)
                text = self.parse_expr(); self.consume(TT.RPAREN)
                self.consume(TT.USING)
                self.consume(TT.LBRACKET)
                labels = []
                while not self.check(TT.RBRACKET):
                    labels.append(self.parse_expr())
                    if not self.match(TT.COMMA): break
                self.consume(TT.RBRACKET)
                return ClassifyExpr(text=text, labels=labels)
            else:
                self.pos += 1
                return Identifier(name="classify")

        # Keywords that can also be used as function calls
        keyword_as_fn = {
            TT.HAS: "has", TT.TYPE: "type", TT.COLLECT: "collect",
            TT.WHEN: "when", TT.AGENT: "agent",
        }
        if t.type in keyword_as_fn and self.peek().type == TT.LPAREN:
            self.pos += 1
            return Identifier(name=keyword_as_fn[t.type])

        if t.type == TT.IDENT:
            self.pos += 1
            return Identifier(name=t.value)

        self.error(f"Unexpected token: {t.type.name} ({t.value!r})")
