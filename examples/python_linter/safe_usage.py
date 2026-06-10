"""Safe synthetic refund-routing example for `ledge lint-python`."""

from ledge_lang.sdk import DecisionPolicy, Uncertain


def refund_customer(route: str) -> None:
    print(f"refund route: {route}")


def send_email(route: str) -> None:
    print(f"email route: {route}")


policy = DecisionPolicy(min_confidence=0.85, name="refund-routing")
risk = Uncertain(value="standard_refund", confidence=0.91)
decision = risk.handle(policy=policy)

if decision.allowed:
    refund_customer(decision.value)

if decision.action == "allow":
    send_email(decision.value)

manual_value = risk.unsafe_unwrap(reason="manual override approved for demo fixture")
print(manual_value)
