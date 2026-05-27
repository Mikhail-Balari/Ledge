# Pilot Templates

These are public operational templates for planning a shadow-mode AI Decision
Boundary Pilot with Ledge.

They are not legal templates, compliance templates, or production deployment
instructions. They are intended to be adapted per workflow, domain, data
sharing constraint, and risk profile.

For a self-contained synthetic dry run, see
[`loan_approval/`](loan_approval/) and run:

```bash
python scripts/run_pilot_dry_run.py pilot_templates/loan_approval
```

Use them to keep a pilot explicit about:

- the decision boundary being evaluated;
- the AI output and possible action;
- confidence thresholds and fallbacks;
- deterministic rules;
- human review;
- audit evidence;
- calibration limits;
- final recommendations and next steps.
