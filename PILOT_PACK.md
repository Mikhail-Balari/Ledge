# AI Decision Boundary Pilot Pack

This pack describes a sober, public template for evaluating Ledge in a scoped
shadow-mode pilot. It is not a production deployment plan and not a compliance
template.

## What Is The AI Decision Boundary Pilot?

An AI Decision Boundary Pilot is a short technical exercise focused on one
place where AI output may influence an action. The pilot represents that
boundary in Ledge, runs it on synthetic or approved fixtures, checks unsafe
paths, records audit evidence, and documents what remains unresolved.

## What Problem It Tests

The pilot tests whether a team can make the following explicit:

- the AI output being used;
- the action that might follow;
- the confidence threshold;
- deterministic rules that must apply first;
- fallback or human-review behavior;
- audit evidence;
- outcome data that could support future calibration.

## What Is Included

- Decision boundary map.
- Intake review.
- Synthetic or approved fixture set.
- Policy definition for thresholds and fallbacks.
- Small executable Ledge demo.
- Checked unsafe-path demonstration.
- Audit sample.
- Calibration sample if outcome data is available.
- Final report with limitations and next steps.

## What Is Not Included

- Production deployment.
- Legal or compliance certification.
- Security certification.
- A guarantee that AI outputs are correct.
- A guarantee that confidence is calibrated.
- Replacement of monitoring, evals, human review, or incident response.
- Integration with live systems unless separately scoped.

## What The Client Needs To Provide

- A candidate AI-assisted workflow.
- The action or decision affected by AI output.
- A description of current human review and fallback behavior.
- Any available confidence or score signal.
- Any outcome data available after the decision.
- Data-sharing constraints.
- A named reviewer for policy and limitations.

## If Real Data Cannot Be Shared

Real data is not required for a first pilot. The team can use synthetic fixtures
that preserve the shape of the decision boundary without exposing sensitive
records. Synthetic fixtures do not prove production performance; they are used
to evaluate workflow clarity, checker behavior, fallback design, and audit
shape.

## How Synthetic Fixtures Are Used

Synthetic fixtures should include:

- a clear safe case;
- a low-confidence case;
- a high-risk case;
- an ambiguous case;
- a missing-evidence case.

Each fixture should state the expected action and the reason.

## Deliverables

The templates in [`pilot_templates/`](pilot_templates/) provide a starting
point:

- decision boundary map;
- fixture file;
- policy file;
- executable demo;
- audit sample;
- calibration note;
- final report;
- limitations and next steps.

## What Success Looks Like

A successful pilot does not mean Ledge is production-ready. It means:

- the demo runs;
- unchecked AI use is blocked or explicitly marked unsafe;
- thresholds and fallbacks are visible;
- human review behavior is explicit;
- audit evidence is produced;
- calibration status is either sampled or documented as unavailable;
- stakeholders understand where Ledge fits and where it does not.

## What Ledge Demonstrates

- Unchecked `Uncertain[T]` use becomes a static error in checked execution.
- Unsafe bypass is explicit.
- Confidence gates and fallbacks are visible in source.
- Deterministic rules can be separated from AI-derived decisions.
- Audit entries and chain verification can be inspected.

## What Ledge Does Not Demonstrate

- Model truth.
- Calibrated correctness by default.
- Production-critical readiness.
- Compliance certification.
- Security against a malicious local operator.
- Complete governance for an AI system.

## Limitations

Ledge is alpha software. A pilot should run in shadow mode unless additional
review and controls are explicitly added. Confidence can be wrong or poorly
calibrated. Synthetic fixtures are useful for boundary design but do not prove
real-world performance.

## Contact

Use the GitHub repository for technical review and issues:
<https://github.com/Mikhail-Balari/Ledge>
