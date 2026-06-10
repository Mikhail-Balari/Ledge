"""AST scanner for Python SDK decision-boundary lint rules."""

from __future__ import annotations

import ast
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

from .config import LintConfig
from .report import Diagnostic, display_path
from .rules import LPY001, LPY002, LPY003, LPY004, Rule


IGNORED_DIRS = {".git", ".venv", "venv", "__pycache__", "build", "dist"}


@dataclass
class LintResult:
    diagnostics: list[Diagnostic] = field(default_factory=list)
    files_scanned: int = 0


def lint_paths(paths: Iterable[str | Path], config: LintConfig) -> LintResult:
    result = LintResult()
    for path in _iter_python_files(paths):
        result.files_scanned += 1
        source = path.read_text(encoding="utf-8")
        result.diagnostics.extend(lint_source(source, path, config))
    return result


def lint_source(source: str, path: str | Path, config: LintConfig) -> list[Diagnostic]:
    scanner = _Scanner(str(path), config)
    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError as exc:
        return [
            Diagnostic(
                path=str(path),
                line=exc.lineno or 1,
                column=exc.offset or 0,
                rule_id="LPY000",
                severity="error",
                message=f"Python syntax error: {exc.msg}",
                suggestion="Fix the Python syntax before running Ledge linting.",
            )
        ]
    scanner.scan(tree)
    return scanner.diagnostics


def _iter_python_files(paths: Iterable[str | Path]) -> Iterable[Path]:
    for raw_path in paths:
        path = Path(raw_path)
        if not path.exists():
            raise FileNotFoundError(f"path not found: {path}")
        if path.is_file():
            if path.suffix == ".py":
                yield path
            continue
        for child in sorted(path.rglob("*.py")):
            if _is_ignored(child):
                continue
            yield child


def _is_ignored(path: Path) -> bool:
    for part in path.parts:
        if part in IGNORED_DIRS or part.endswith(".egg-info"):
            return True
    return False


class _Scanner(ast.NodeVisitor):
    def __init__(self, path: str, config: LintConfig) -> None:
        self.path = path
        self.config = config
        self.diagnostics: list[Diagnostic] = []
        self.uncertain_vars: list[set[str]] = [set()]
        self.decision_vars: list[set[str]] = [set()]
        self.client_vars: list[set[str]] = [set()]
        self.allow_guard_stack: list[set[str]] = [set()]
        self.uncertain_constructors: set[str] = {"ledge_lang.sdk.Uncertain"}
        self.validation_factories: set[str] = {"ledge_lang.sdk.uncertain_from_validation"}
        self.client_constructors: set[str] = {
            "ledge_lang.sdk.FakeAIClient",
            "ledge_lang.sdk.DeterministicAIClient",
        }
        self.module_aliases: dict[str, str] = {}
        self.return_uncertain_functions: set[str] = set()

    def scan(self, tree: ast.AST) -> None:
        self._collect_uncertain_return_functions(tree)
        self.visit(tree)

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            local = alias.asname or alias.name
            self.module_aliases[local] = alias.name
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        module = node.module or ""
        if module == "ledge_lang":
            for alias in node.names:
                if alias.name == "sdk":
                    local = alias.asname or alias.name
                    self.module_aliases[local] = "ledge_lang.sdk"
            self.generic_visit(node)
            return

        if module != "ledge_lang.sdk":
            self.generic_visit(node)
            return

        for alias in node.names:
            local = alias.asname or alias.name
            full = f"{module}.{alias.name}"
            if alias.name == "Uncertain":
                self.uncertain_constructors.add(local)
            elif alias.name == "uncertain_from_validation":
                self.validation_factories.add(local)
            elif alias.name in ("FakeAIClient", "DeterministicAIClient"):
                self.client_constructors.add(local)
            else:
                self.module_aliases[local] = full
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._push_scope()
        for statement in node.body:
            self.visit(statement)
        self._pop_scope()

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self.visit_FunctionDef(node)

    def visit_Assign(self, node: ast.Assign) -> None:
        self.visit(node.value)
        target_names = [target.id for target in node.targets if isinstance(target, ast.Name)]
        if not target_names:
            return

        if self._call_returns_uncertain(node.value):
            for name in target_names:
                self._current_uncertain().add(name)
        elif self._call_returns_decision(node.value):
            for name in target_names:
                self._current_decision().add(name)
        elif self._call_returns_client(node.value):
            for name in target_names:
                self._current_clients().add(name)
        else:
            for name in target_names:
                self._current_uncertain().discard(name)
                self._current_decision().discard(name)
                self._current_clients().discard(name)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        self.visit(node.value) if node.value is not None else None
        if not isinstance(node.target, ast.Name):
            return
        name = node.target.id
        if self._annotation_is_uncertain(node.annotation) or self._call_returns_uncertain(node.value):
            self._current_uncertain().add(name)
        elif self._annotation_is_decision(node.annotation) or self._call_returns_decision(node.value):
            self._current_decision().add(name)
        else:
            self._current_uncertain().discard(name)
            self._current_decision().discard(name)

    def visit_If(self, node: ast.If) -> None:
        self.visit(node.test)
        guarded = self._allow_guarded_decisions(node.test)
        self.allow_guard_stack.append(self._current_guarded() | guarded)
        for statement in node.body:
            self.visit(statement)
        self.allow_guard_stack.pop()
        for statement in node.orelse:
            self.visit(statement)

    def visit_Call(self, node: ast.Call) -> None:
        self._check_unsafe_unwrap(node)
        self._check_critical_action(node)
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        if node.attr == "value" and isinstance(node.value, ast.Name):
            name = node.value.id
            if self._is_uncertain(name):
                self._add(node, LPY002)
        self.generic_visit(node)

    def _check_unsafe_unwrap(self, node: ast.Call) -> None:
        if not isinstance(node.func, ast.Attribute) or node.func.attr != "unsafe_unwrap":
            return
        if not self.config.unsafe_unwrap_requires_reason:
            return
        reason = None
        if node.args:
            reason = node.args[0]
        for keyword in node.keywords:
            if keyword.arg == "reason":
                reason = keyword.value
        if reason is None:
            self._add(node, LPY001)
            return
        if isinstance(reason, ast.Constant) and isinstance(reason.value, str):
            if not reason.value.strip():
                self._add(node, LPY001)

    def _check_critical_action(self, node: ast.Call) -> None:
        action = self._call_action_name(node.func)
        if action not in self.config.critical_actions:
            return
        for arg in list(node.args) + [keyword.value for keyword in node.keywords if keyword.arg]:
            if isinstance(arg, ast.Name) and self._is_uncertain(arg.id):
                self._add(arg, LPY003)
            elif (
                isinstance(arg, ast.Attribute)
                and arg.attr == "value"
                and isinstance(arg.value, ast.Name)
            ):
                receiver = arg.value.id
                if self._is_uncertain(receiver):
                    self._add(arg, LPY003)
                elif self._is_decision(receiver) and receiver not in self._current_guarded():
                    self._add(arg, LPY004)

    def _call_returns_uncertain(self, node: ast.AST | None) -> bool:
        if not isinstance(node, ast.Call):
            return False
        name = self._qualified_name(node.func)
        if name in self.uncertain_constructors or name in self.validation_factories:
            return True
        if isinstance(node.func, ast.Name) and node.func.id in self.return_uncertain_functions:
            return True
        if isinstance(node.func, ast.Attribute) and node.func.attr == "predict":
            receiver = node.func.value
            if isinstance(receiver, ast.Name) and self._is_client(receiver.id):
                return True
        return False

    def _call_returns_decision(self, node: ast.AST | None) -> bool:
        if not isinstance(node, ast.Call):
            return False
        if not isinstance(node.func, ast.Attribute) or node.func.attr != "handle":
            return False
        receiver = node.func.value
        return isinstance(receiver, ast.Name) and self._is_uncertain(receiver.id)

    def _call_returns_client(self, node: ast.AST | None) -> bool:
        if not isinstance(node, ast.Call):
            return False
        return self._qualified_name(node.func) in self.client_constructors

    def _call_action_name(self, node: ast.AST) -> str | None:
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            return node.attr
        return None

    def _allow_guarded_decisions(self, node: ast.AST) -> set[str]:
        guarded: set[str] = set()
        if isinstance(node, ast.Attribute) and node.attr == "allowed":
            if isinstance(node.value, ast.Name) and self._is_decision(node.value.id):
                guarded.add(node.value.id)
        elif isinstance(node, ast.Compare):
            guarded |= self._decision_action_allow_guard(node.left, node.comparators)
            for comparator in node.comparators:
                guarded |= self._decision_action_allow_guard(comparator, [node.left])
        elif isinstance(node, ast.BoolOp) and isinstance(node.op, ast.And):
            for value in node.values:
                guarded |= self._allow_guarded_decisions(value)
        return guarded

    def _decision_action_allow_guard(
        self,
        maybe_action: ast.AST,
        comparators: list[ast.AST],
    ) -> set[str]:
        if not (
            isinstance(maybe_action, ast.Attribute)
            and maybe_action.attr == "action"
            and isinstance(maybe_action.value, ast.Name)
            and self._is_decision(maybe_action.value.id)
        ):
            return set()
        for comparator in comparators:
            if isinstance(comparator, ast.Constant) and comparator.value == "allow":
                return {maybe_action.value.id}
        return set()

    def _qualified_name(self, node: ast.AST) -> str | None:
        if isinstance(node, ast.Name):
            return self.module_aliases.get(node.id, node.id)
        if isinstance(node, ast.Attribute):
            base = self._qualified_name(node.value)
            if base is None:
                return node.attr
            return f"{base}.{node.attr}"
        return None

    def _collect_uncertain_return_functions(self, tree: ast.AST) -> None:
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.returns is not None and self._annotation_is_uncertain(node.returns):
                    self.return_uncertain_functions.add(node.name)

    def _annotation_is_uncertain(self, node: ast.AST) -> bool:
        name = self._annotation_name(node)
        return name in ("Uncertain", "ledge_lang.sdk.Uncertain") or name.endswith(".Uncertain")

    def _annotation_is_decision(self, node: ast.AST) -> bool:
        name = self._annotation_name(node)
        return name in ("DecisionResult", "ledge_lang.sdk.DecisionResult") or name.endswith(
            ".DecisionResult"
        )

    def _annotation_name(self, node: ast.AST) -> str:
        if isinstance(node, ast.Subscript):
            return self._annotation_name(node.value)
        if isinstance(node, ast.Name):
            return self.module_aliases.get(node.id, node.id)
        if isinstance(node, ast.Attribute):
            return self._qualified_name(node) or ""
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        return ""

    def _push_scope(self) -> None:
        self.uncertain_vars.append(set())
        self.decision_vars.append(set())
        self.client_vars.append(set())
        self.allow_guard_stack.append(set())

    def _pop_scope(self) -> None:
        self.uncertain_vars.pop()
        self.decision_vars.pop()
        self.client_vars.pop()
        self.allow_guard_stack.pop()

    def _current_uncertain(self) -> set[str]:
        return self.uncertain_vars[-1]

    def _current_decision(self) -> set[str]:
        return self.decision_vars[-1]

    def _current_clients(self) -> set[str]:
        return self.client_vars[-1]

    def _current_guarded(self) -> set[str]:
        return self.allow_guard_stack[-1]

    def _is_uncertain(self, name: str) -> bool:
        return any(name in scope for scope in reversed(self.uncertain_vars))

    def _is_decision(self, name: str) -> bool:
        return any(name in scope for scope in reversed(self.decision_vars))

    def _is_client(self, name: str) -> bool:
        return any(name in scope for scope in reversed(self.client_vars))

    def _add(self, node: ast.AST, rule: Rule) -> None:
        self.diagnostics.append(
            Diagnostic(
                path=self.path,
                line=getattr(node, "lineno", 1),
                column=getattr(node, "col_offset", 0),
                rule_id=rule.id,
                severity=rule.severity,
                message=rule.message,
                suggestion=rule.suggestion,
            )
        )


def display_diagnostic_paths(diagnostics: Iterable[Diagnostic]) -> list[Diagnostic]:
    return [
        Diagnostic(
            path=display_path(Path(diagnostic.path)),
            line=diagnostic.line,
            column=diagnostic.column,
            rule_id=diagnostic.rule_id,
            severity=diagnostic.severity,
            message=diagnostic.message,
            suggestion=diagnostic.suggestion,
        )
        for diagnostic in diagnostics
    ]
