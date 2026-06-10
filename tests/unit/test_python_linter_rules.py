from ledge_lang.python_linter.config import LintConfig
from ledge_lang.python_linter.scanner import lint_source


def rule_ids(source, critical_actions=None):
    config = LintConfig(critical_actions=set(critical_actions or []))
    return [diagnostic.rule_id for diagnostic in lint_source(source, "example.py", config)]


def test_lpy001_detects_unsafe_unwrap_without_reason():
    ids = rule_ids(
        """
from ledge_lang.sdk import Uncertain
risk = Uncertain(value="x", confidence=0.9)
risk.unsafe_unwrap()
"""
    )

    assert "LPY001" in ids


def test_lpy001_detects_empty_and_whitespace_reason():
    ids = rule_ids(
        """
from ledge_lang.sdk import Uncertain
risk = Uncertain(value="x", confidence=0.9)
risk.unsafe_unwrap("")
risk.unsafe_unwrap(reason="   ")
"""
    )

    assert ids.count("LPY001") == 2


def test_lpy001_allows_non_empty_reason():
    ids = rule_ids(
        """
from ledge_lang.sdk import Uncertain
risk = Uncertain(value="x", confidence=0.9)
risk.unsafe_unwrap(reason="reviewed manual override")
"""
    )

    assert "LPY001" not in ids


def test_lpy002_detects_value_access_on_tracked_uncertain():
    ids = rule_ids(
        """
from ledge_lang.sdk import Uncertain
risk = Uncertain(value="x", confidence=0.9)
print(risk.value)
"""
    )

    assert "LPY002" in ids


def test_lpy002_does_not_flag_unrelated_value_access():
    ids = rule_ids(
        """
class Color:
    value = "red"
color = Color()
print(color.value)
"""
    )

    assert "LPY002" not in ids


def test_lpy003_detects_critical_action_with_uncertain_argument():
    ids = rule_ids(
        """
from ledge_lang.sdk import Uncertain
def refund_customer(route): pass
risk = Uncertain(value="refund", confidence=0.7)
refund_customer(risk)
""",
        critical_actions={"refund_customer"},
    )

    assert "LPY003" in ids


def test_lpy003_detects_critical_action_with_uncertain_value_argument():
    ids = rule_ids(
        """
from ledge_lang.sdk import Uncertain
def refund_customer(route): pass
risk = Uncertain(value="refund", confidence=0.7)
refund_customer(risk.value)
""",
        critical_actions={"refund_customer"},
    )

    assert "LPY003" in ids


def test_lpy003_allows_decision_value_inside_allowed_guard():
    ids = rule_ids(
        """
from ledge_lang.sdk import DecisionPolicy, Uncertain
def refund_customer(route): pass
risk = Uncertain(value="refund", confidence=0.9)
decision = risk.handle(policy=DecisionPolicy(min_confidence=0.8))
if decision.allowed:
    refund_customer(decision.value)
""",
        critical_actions={"refund_customer"},
    )

    assert "LPY003" not in ids
    assert "LPY004" not in ids


def test_lpy003_allows_decision_value_inside_action_allow_guard():
    ids = rule_ids(
        """
from ledge_lang.sdk import DecisionPolicy, Uncertain
def refund_customer(route): pass
risk = Uncertain(value="refund", confidence=0.9)
decision = risk.handle(policy=DecisionPolicy(min_confidence=0.8))
if decision.action == "allow":
    refund_customer(decision.value)
""",
        critical_actions={"refund_customer"},
    )

    assert "LPY003" not in ids
    assert "LPY004" not in ids


def test_lpy004_detects_decision_value_outside_allow_guard():
    ids = rule_ids(
        """
from ledge_lang.sdk import DecisionPolicy, Uncertain
def refund_customer(route): pass
risk = Uncertain(value="refund", confidence=0.9)
decision = risk.handle(policy=DecisionPolicy(min_confidence=0.8))
refund_customer(decision.value)
""",
        critical_actions={"refund_customer"},
    )

    assert "LPY004" in ids


def test_lpy004_detects_decision_value_inside_allowed_or_guard():
    ids = rule_ids(
        """
from ledge_lang.sdk import DecisionPolicy, Uncertain
def refund_customer(route): pass
risk = Uncertain(value="refund", confidence=0.7)
decision = risk.handle(policy=DecisionPolicy(min_confidence=0.8))
emergency_override = True
if decision.allowed or emergency_override:
    refund_customer(decision.value)
""",
        critical_actions={"refund_customer"},
    )

    assert "LPY004" in ids


def test_lpy004_allows_decision_value_inside_allowed_and_guard():
    ids = rule_ids(
        """
from ledge_lang.sdk import DecisionPolicy, Uncertain
def refund_customer(route): pass
risk = Uncertain(value="refund", confidence=0.9)
decision = risk.handle(policy=DecisionPolicy(min_confidence=0.8))
audit_log_ready = True
if decision.allowed and audit_log_ready:
    refund_customer(decision.value)
""",
        critical_actions={"refund_customer"},
    )

    assert "LPY004" not in ids


def test_lpy004_detects_decision_value_inside_action_allow_or_guard():
    ids = rule_ids(
        """
from ledge_lang.sdk import DecisionPolicy, Uncertain
def refund_customer(route): pass
risk = Uncertain(value="refund", confidence=0.7)
decision = risk.handle(policy=DecisionPolicy(min_confidence=0.8))
emergency_override = True
if decision.action == "allow" or emergency_override:
    refund_customer(decision.value)
""",
        critical_actions={"refund_customer"},
    )

    assert "LPY004" in ids


def test_lpy004_allows_decision_value_inside_action_allow_and_guard():
    ids = rule_ids(
        """
from ledge_lang.sdk import DecisionPolicy, Uncertain
def refund_customer(route): pass
risk = Uncertain(value="refund", confidence=0.9)
decision = risk.handle(policy=DecisionPolicy(min_confidence=0.8))
audit_log_ready = True
if decision.action == "allow" and audit_log_ready:
    refund_customer(decision.value)
""",
        critical_actions={"refund_customer"},
    )

    assert "LPY004" not in ids


def test_lpy004_allow_guard_does_not_leak_after_if_block():
    ids = rule_ids(
        """
from ledge_lang.sdk import DecisionPolicy, Uncertain
def refund_customer(route): pass
risk = Uncertain(value="refund", confidence=0.9)
decision = risk.handle(policy=DecisionPolicy(min_confidence=0.8))
if decision.allowed:
    refund_customer(decision.value)
refund_customer(decision.value)
""",
        critical_actions={"refund_customer"},
    )

    assert ids.count("LPY004") == 1


def test_lpy004_allows_decision_value_inside_nested_allowed_guard():
    ids = rule_ids(
        """
from ledge_lang.sdk import DecisionPolicy, Uncertain
def refund_customer(route): pass
risk = Uncertain(value="refund", confidence=0.9)
decision = risk.handle(policy=DecisionPolicy(min_confidence=0.8))
audit_log_ready = True
if decision.allowed:
    if audit_log_ready:
        refund_customer(decision.value)
""",
        critical_actions={"refund_customer"},
    )

    assert "LPY004" not in ids


def test_lpy004_detects_decision_value_inside_unrelated_nested_guard():
    ids = rule_ids(
        """
from ledge_lang.sdk import DecisionPolicy, Uncertain
def refund_customer(route): pass
risk = Uncertain(value="refund", confidence=0.9)
decision = risk.handle(policy=DecisionPolicy(min_confidence=0.8))
audit_log_ready = True
if audit_log_ready:
    refund_customer(decision.value)
""",
        critical_actions={"refund_customer"},
    )

    assert "LPY004" in ids
