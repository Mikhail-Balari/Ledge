#!/usr/bin/env python3
"""Minimal Python application delegating an AI boundary to checked Ledge.

Synthetic demo only. This is not a credit model, not a lending decision
system, not production software, and not compliance software.
"""

from __future__ import annotations

import json
from pathlib import Path

from ledge_lang import LedgeError, checked_run


EXAMPLE_DIR = Path(__file__).resolve().parent
BOUNDARY_PATH = EXAMPLE_DIR / "decision_boundary.ledge"
FIXTURE_PATH = EXAMPLE_DIR / "fixture.json"


def _ledge_string(value: str) -> str:
    return json.dumps(value)


def _ledge_bool(value: bool) -> str:
    return "true" if value else "false"


def _build_invocation(case: dict) -> str:
    flags = case["deterministic_inputs"]
    return "\n".join(
        [
            "",
            "evaluate_boundary(",
            f"    {_ledge_string(case['application_id'])},",
            f"    {_ledge_string(case['case_text'])},",
            f"    {_ledge_bool(bool(flags['missing_evidence']))},",
            f"    {_ledge_bool(bool(flags['hard_risk_flag']))}",
            ")",
            "",
        ]
    )


def _backend_for_case(case: dict) -> dict:
    signal = case["ai_signal"]

    def classify(text, labels):
        label = signal["label"]
        if label not in labels:
            label = "review"
        return {"value": label, "confidence": signal["confidence"]}

    return {"classify": classify}


def _decision_from_lines(lines: list[str]) -> str:
    for line in lines:
        if line.startswith("Decision: "):
            return line.split(": ", 1)[1]
    return "UNKNOWN"


def main() -> int:
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    boundary_source = BOUNDARY_PATH.read_text(encoding="utf-8")

    print("=== PYTHON + LEDGE DECISION BOUNDARY EXAMPLE ===")
    print("SYNTHETIC DEMO ONLY")
    print("NOT A CREDIT MODEL")
    print("NOT A LENDING DECISION SYSTEM")
    print("NOT PRODUCTION OR COMPLIANCE SOFTWARE")
    print("Python handles fixture loading and workflow context.")
    print("Ledge handles the AI decision boundary through checked_run(...).")
    print()

    counts = {
        "APPROVE_ALLOWED": 0,
        "ROUTE_TO_HUMAN_REVIEW": 0,
        "REJECT_ALLOWED": 0,
        "UNKNOWN": 0,
    }

    for case in fixture["cases"]:
        source = boundary_source + _build_invocation(case)
        backend = _backend_for_case(case)

        try:
            lines, _ = checked_run(source, ai_backend=backend)
        except LedgeError as exc:
            print(f"{case['application_id']}: CHECKED_EXECUTION_BLOCKED")
            print(f"  Error: {exc}")
            counts["UNKNOWN"] += 1
            continue

        decision = _decision_from_lines(lines)
        counts[decision] = counts.get(decision, 0) + 1

        print(f"{case['application_id']}: {decision}")
        print(f"  Scenario: {case['scenario']}")
        print("  Checked execution: ledge_lang.checked_run(...)")
        for line in lines:
            if line.startswith("AI confidence:") or line.startswith("Decision source:"):
                print(f"  {line}")
        print(f"  Expected dry-run action: {case['expected_action']}")
        print()

    print("Summary:")
    print(f"  Cases evaluated: {len(fixture['cases'])}")
    print(f"  Approve allowed: {counts.get('APPROVE_ALLOWED', 0)}")
    print(f"  Human review: {counts.get('ROUTE_TO_HUMAN_REVIEW', 0)}")
    print(f"  Reject allowed: {counts.get('REJECT_ALLOWED', 0)}")
    print("  Real systems touched: none")
    print("  API keys used: none")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
