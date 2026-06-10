"""Unsafe synthetic refund-routing example for `ledge lint-python`."""

from ledge_lang.sdk import DecisionPolicy, Uncertain


def refund_customer(route: str) -> None:
    print(f"refund route: {route}")


policy = DecisionPolicy(min_confidence=0.85, name="refund-routing")
risk = Uncertain(value="standard_refund", confidence=0.76)

risk.unsafe_unwrap()
risk.unsafe_unwrap(reason="   ")

print(risk.value)
refund_customer(risk)
refund_customer(risk.value)

decision = risk.handle(policy=policy)
refund_customer(decision.value)
