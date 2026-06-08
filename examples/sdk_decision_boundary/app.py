#!/usr/bin/env python3
"""Minimal Ledge SDK decision-boundary example.

Synthetic demo only. This is not a production workflow and does not touch real
systems. It shows SDK-level handling of uncertain AI-like values in normal
Python code.
"""

from __future__ import annotations

from ledge_lang.sdk import (
    ConfidenceEvidence,
    DecisionPolicy,
    FakeAIClient,
    UnsafeUnwrapError,
)


def main() -> int:
    print("=== LEDGE PYTHON SDK CORE EXAMPLE ===")
    print("SYNTHETIC DEMO ONLY")
    print("Domain: customer support refund routing")
    print("Real systems touched: none")
    print("API keys used: none")
    print()

    policy = DecisionPolicy(
        min_confidence=0.80,
        name="refund-routing-demo",
        on_low_confidence="human_review",
        on_missing_value="block",
    )

    client = FakeAIClient(
        responses={
            "refund-clear": {
                "value": "refund_route_allowed",
                "confidence": 0.93,
                "source": "fake_support_classifier",
                "evidence": ConfidenceEvidence(
                    score=0.93,
                    source="deterministic_fixture",
                    signals={"matched_policy": "refund_with_receipt"},
                ),
            },
            "refund-low-confidence": {
                "value": "refund_route_allowed",
                "confidence": 0.52,
                "source": "fake_support_classifier",
                "warnings": ["low confidence fixture"],
                "evidence": ConfidenceEvidence(
                    score=0.52,
                    source="deterministic_fixture",
                    signals={"matched_policy": "weak_match"},
                    warnings=["evidence signal is weak"],
                ),
            },
            "refund-missing": {
                "value": None,
                "confidence": 0.88,
                "source": "fake_support_classifier",
                "warnings": ["missing required refund category"],
                "evidence": ConfidenceEvidence(
                    score=0.88,
                    source="deterministic_fixture",
                    signals={"missing": "refund_category"},
                ),
            },
        }
    )

    high = client.predict("refund-clear").handle(policy)
    print(f"ALLOW_REFUND_ROUTE action={high.action} allowed={high.allowed}")
    print(f"  reason={high.reason}")
    print(f"  value={high.value}")
    print("EVIDENCE_RECORDED")
    print()

    low = client.predict("refund-low-confidence").handle(policy)
    print(f"ROUTE_TO_HUMAN_REVIEW action={low.action} allowed={low.allowed}")
    print(f"  reason={low.reason}")
    print(f"  warnings={low.warnings}")
    print()

    missing = client.predict("refund-missing").handle(policy)
    print(f"BLOCK_MISSING_VALUE action={missing.action} allowed={missing.allowed}")
    print(f"  reason={missing.reason}")
    print(f"  warnings={missing.warnings}")
    print()

    try:
        client.predict("refund-clear").unsafe_unwrap("")
    except UnsafeUnwrapError as exc:
        print("UNSAFE_UNWRAP_REJECTED")
        print(f"  reason={exc}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
