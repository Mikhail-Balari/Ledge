# Pilot Runbook

This runbook assumes a 10-day shadow-mode pilot. Adjust the schedule for the
workflow, reviewer availability, and data constraints.

## Day 0: Preparation

- Inputs: repository access, pilot owner, workflow candidate, data constraints.
- Activities: confirm scope, install Ledge, review disclaimers, assign reviewers.
- Outputs: pilot workspace and named contacts.
- Done criteria: everyone agrees this is shadow mode and not production use.

## Day 1: Kickoff

- Inputs: workflow description, current AI use or proposed AI use.
- Activities: identify the decision boundary and the possible downstream action.
- Outputs: initial boundary statement.
- Done criteria: one specific boundary is selected.

## Day 2: Decision Boundary Selection

- Inputs: current process, action list, escalation rules.
- Activities: map AI output, deterministic rules, action, fallback, and reviewer.
- Outputs: draft decision boundary map.
- Done criteria: the boundary can be expressed in one page.

## Day 3-4: Fixture

- Inputs: synthetic or approved historical examples.
- Activities: create safe, low-confidence, high-risk, ambiguous, and missing-evidence cases.
- Outputs: fixture file and expected outcomes.
- Done criteria: every fixture has an expected action and reason.

## Day 5-6: Policy

- Inputs: confidence signal, threshold preference, fallback requirements.
- Activities: define threshold, human review path, deterministic blocks, and unsafe cases.
- Outputs: policy definition and Ledge demo sketch.
- Done criteria: confidence handling and fallback are visible.

## Day 7-8: Shadow/Simulation Run

- Inputs: fixture and policy.
- Activities: run the Ledge representation, verify unsafe cases fail, inspect output.
- Outputs: executable demo result and audit sample.
- Done criteria: the demo runs without affecting production.

## Day 9: Audit/Calibration Review

- Inputs: audit output, chain verification, any available outcome data.
- Activities: review audit entries, note calibration availability, identify gaps.
- Outputs: audit sample and calibration note.
- Done criteria: evidence and limitations are documented.

## Day 10: Final Readout

- Inputs: boundary map, fixture, policy, outputs, audit sample, limitations.
- Activities: summarize findings and decide next steps.
- Outputs: final report.
- Done criteria: stakeholders understand what Ledge demonstrated and what it did not.
