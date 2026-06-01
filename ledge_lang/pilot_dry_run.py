"""Synthetic pilot dry-run runner used by the installed CLI and scripts."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from importlib import resources
from pathlib import Path
from typing import Any, Protocol


APPROVE = "APPROVE_ALLOWED"
REVIEW = "ROUTE_TO_HUMAN_REVIEW"
REJECT = "REJECT_ALLOWED"


class ReadableResource(Protocol):
    def exists(self) -> bool: ...
    def read_text(self, encoding: str = "utf-8") -> str: ...
    def joinpath(self, *descendants: str) -> "ReadableResource": ...


@dataclass
class PilotSource:
    label: str
    root: ReadableResource


@dataclass
class Decision:
    application_id: str
    scenario: str
    deterministic_result: str
    label: str
    confidence: float
    threshold: float
    action: str
    reason: str
    human_review: bool
    deterministic_triggered: bool
    ai_derived_action: bool
    expected_action: str | None


def bundled_pilot_source(name: str) -> PilotSource:
    if name != "loan_approval":
        raise SystemExit(
            f"ERROR: unknown packaged pilot dry run: {name}. "
            "Available: loan_approval"
        )
    root = resources.files("ledge_lang.pilot_templates.loan_approval")
    return PilotSource(label="packaged: loan_approval", root=root)


def path_pilot_source(path: Path) -> PilotSource:
    return PilotSource(label=str(path.resolve()), root=path.resolve())


def resolve_pilot_source(value: str) -> PilotSource:
    path = Path(value)
    if path.exists():
        return path_pilot_source(path)
    return bundled_pilot_source(value)


def load_json(path: ReadableResource) -> dict[str, Any]:
    if not path.exists():
        raise SystemExit(f"ERROR: required file not found: {path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"ERROR: invalid JSON in {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise SystemExit(f"ERROR: expected JSON object in {path}")
    return value


def active_deterministic_flags(case: dict[str, Any]) -> list[str]:
    flags = case.get("deterministic_flags", {})
    if not isinstance(flags, dict):
        raise SystemExit(
            f"ERROR: deterministic_flags must be an object for {case.get('application_id')}"
        )
    return [name for name, enabled in flags.items() if bool(enabled)]


def evaluate_case(case: dict[str, Any], policy: dict[str, Any]) -> Decision:
    application_id = str(case.get("application_id", "<missing>"))
    label = str(case.get("model_label", "unknown"))
    try:
        confidence = float(case.get("model_confidence"))
    except (TypeError, ValueError) as exc:
        raise SystemExit(f"ERROR: model_confidence must be numeric for {application_id}") from exc

    threshold_approve = float(policy.get("threshold_approve", 0.85))
    threshold_review_min = float(policy.get("threshold_review_min", 0.65))
    labels = policy.get("labels", {})
    approve_labels = set(labels.get("approve_labels", ["approve", "low_risk"]))
    reject_labels = set(labels.get("reject_labels", ["reject", "high_risk"]))
    ambiguous_labels = set(labels.get("ambiguous_labels", ["medium_risk", "ambiguous", "unknown"]))

    active_flags = active_deterministic_flags(case)
    deterministic_triggered = bool(active_flags)

    if deterministic_triggered:
        action = REVIEW
        reason = f"deterministic review flag(s): {', '.join(active_flags)}"
        deterministic_result = "REVIEW_REQUIRED"
        human_review = True
        ai_derived_action = False
    elif label in approve_labels and confidence >= threshold_approve:
        action = APPROVE
        reason = f"AI label {label!r} met approve threshold"
        deterministic_result = "PASS"
        human_review = False
        ai_derived_action = True
    elif label in reject_labels and confidence >= threshold_approve:
        action = REJECT
        reason = f"AI label {label!r} met reject threshold"
        deterministic_result = "PASS"
        human_review = False
        ai_derived_action = True
    elif confidence >= threshold_review_min:
        action = REVIEW
        if label in ambiguous_labels:
            reason = f"ambiguous AI label {label!r} requires review"
        else:
            reason = f"confidence {confidence:.2f} below approve/reject threshold"
        deterministic_result = "PASS"
        human_review = True
        ai_derived_action = False
    else:
        action = REVIEW
        reason = f"confidence {confidence:.2f} below review minimum"
        deterministic_result = "PASS"
        human_review = True
        ai_derived_action = False

    return Decision(
        application_id=application_id,
        scenario=str(case.get("scenario", "")),
        deterministic_result=deterministic_result,
        label=label,
        confidence=confidence,
        threshold=threshold_approve,
        action=action,
        reason=reason,
        human_review=human_review,
        deterministic_triggered=deterministic_triggered,
        ai_derived_action=ai_derived_action,
        expected_action=case.get("expected_action"),
    )


def validate_inputs(fixture: dict[str, Any], policy: dict[str, Any]) -> list[dict[str, Any]]:
    cases = fixture.get("cases")
    if not isinstance(cases, list) or not cases:
        raise SystemExit("ERROR: fixture.json must contain a non-empty 'cases' list")

    possible_actions = policy.get("possible_actions")
    if not isinstance(possible_actions, list):
        raise SystemExit("ERROR: policy.json must contain a 'possible_actions' list")
    for action in (APPROVE, REVIEW, REJECT):
        if action not in possible_actions:
            raise SystemExit(f"ERROR: policy.json possible_actions is missing {action}")

    return cases


def print_header(source: PilotSource, fixture: dict[str, Any], policy: dict[str, Any]) -> None:
    print("=== LEDGE PILOT DRY RUN: SYNTHETIC LOAN APPROVAL ===")
    print("SYNTHETIC DEMO ONLY")
    print("NOT A CREDIT MODEL")
    print("NOT A LENDING DECISION SYSTEM")
    print("NOT PRODUCTION OR COMPLIANCE SOFTWARE")
    print("No real data, no API keys, no real AI backend, no production systems touched.")
    print()
    print(f"Pilot source: {source.label}")
    print(f"Fixture: {fixture.get('fixture_name', 'unnamed')}")
    print(f"Policy: {policy.get('policy_name', 'unnamed')}")
    print(f"Approve threshold: {float(policy.get('threshold_approve', 0.85)):.2f}")
    print(f"Review minimum: {float(policy.get('threshold_review_min', 0.65)):.2f}")
    print()


def print_decision(decision: Decision) -> None:
    expected = decision.expected_action or "<none>"
    expected_status = "matches expected" if decision.action == expected else f"expected {expected}"
    print(f"Case: {decision.application_id}")
    print(f"  Scenario: {decision.scenario}")
    print(f"  Deterministic rule result: {decision.deterministic_result}")
    print(f"  AI signal label: {decision.label}")
    print(f"  Confidence: {decision.confidence:.2f}")
    print(f"  Threshold: {decision.threshold:.2f}")
    print(f"  Final dry-run action: {decision.action}")
    print(f"  Reason: {decision.reason}")
    print(f"  Human review/fallback: {'yes' if decision.human_review else 'no'}")
    print(f"  Expected result check: {expected_status}")
    print()


def print_summary(decisions: list[Decision], source: PilotSource) -> None:
    total = len(decisions)
    approve_count = sum(1 for d in decisions if d.action == APPROVE)
    review_count = sum(1 for d in decisions if d.action == REVIEW)
    reject_count = sum(1 for d in decisions if d.action == REJECT)
    deterministic_count = sum(1 for d in decisions if d.deterministic_triggered)
    ai_count = sum(1 for d in decisions if d.ai_derived_action)
    fallback_count = sum(1 for d in decisions if d.human_review)

    print("=== DRY-RUN SUMMARY ===")
    print(f"Total cases: {total}")
    print(f"Approve count: {approve_count}")
    print(f"Review count: {review_count}")
    print(f"Reject count: {reject_count}")
    print(f"Deterministic-rule-triggered count: {deterministic_count}")
    print(f"AI-derived-action count: {ai_count}")
    print(f"Fallback/human-review count: {fallback_count}")
    print()
    if source.label.startswith("packaged:"):
        print("Sample report: packaged loan_approval sample_final_report.md")
    else:
        print("Sample report: pilot_templates/loan_approval/sample_final_report.md")
    print("Report mode: printed summary only; no files were written.")
    print("Use the sample report as a template for a real shadow-mode pilot readout.")


def run(source: PilotSource) -> int:
    fixture = load_json(source.root.joinpath("fixture.json"))
    policy = load_json(source.root.joinpath("policy.json"))
    cases = validate_inputs(fixture, policy)

    print_header(source, fixture, policy)
    decisions = [evaluate_case(case, policy) for case in cases]
    for decision in decisions:
        print_decision(decision)
    print_summary(decisions, source)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run a synthetic pilot dry-run by packaged name or folder path."
    )
    parser.add_argument("pilot", help="Packaged pilot name, e.g. loan_approval, or folder path")
    args = parser.parse_args(argv)
    return run(resolve_pilot_source(args.pilot))


if __name__ == "__main__":
    raise SystemExit(main())
