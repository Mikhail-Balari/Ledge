"""Installed Python integration demo using checked_run(...)."""

from __future__ import annotations

import json
from importlib import resources

from ledge_lang import LedgeError, checked_run


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


def load_fixture_and_boundary() -> tuple[dict, str]:
    package = resources.files("ledge_lang.python_integration")
    fixture = json.loads(package.joinpath("fixture.json").read_text(encoding="utf-8"))
    boundary_source = package.joinpath("decision_boundary.ledge").read_text(encoding="utf-8")
    return fixture, boundary_source


def main(argv: list[str] | None = None) -> int:
    if argv:
        raise SystemExit("Usage: ledge python-integration-demo")

    fixture, boundary_source = load_fixture_and_boundary()

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
