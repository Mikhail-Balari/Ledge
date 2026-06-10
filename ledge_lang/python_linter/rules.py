"""Rule metadata for the Ledge Python linter."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Rule:
    id: str
    severity: str
    message: str
    suggestion: str


LPY001 = Rule(
    id="LPY001",
    severity="error",
    message="unsafe_unwrap requires a non-empty reason",
    suggestion='Pass reason="..." explaining the manual override.',
)

LPY002 = Rule(
    id="LPY002",
    severity="error",
    message="direct .value access on Uncertain value bypasses decision handling",
    suggestion="Use result.handle(policy=...) and consume DecisionResult after an allow guard.",
)

LPY003 = Rule(
    id="LPY003",
    severity="error",
    message="critical action uses uncertain value without an allow decision",
    suggestion="Call .handle(policy=...) and pass decision.value only inside an allow guard.",
)

LPY004 = Rule(
    id="LPY004",
    severity="error",
    message="DecisionResult.value used outside an allow guard",
    suggestion="Use decision.value only inside if decision.allowed or if decision.action == \"allow\".",
)


RULES = {rule.id: rule for rule in [LPY001, LPY002, LPY003, LPY004]}
