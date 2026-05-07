# Calibration Guide

## How outcomes work

record_outcome() records whether an AI decision was 
correct after the fact. This requires:

1. A system that checks results later
   Example: loan repaid or defaulted 6 months later
   Example: diagnosis confirmed by specialist
   Example: email confirmed spam by user report

2. A definition of "correct" for your domain
   This is your responsibility — Ledge does not define
   what correct means. You define it by calling:
   ledge audit --record-outcome DECISION_ID --correct true

3. Patience
   Some domains have delayed ground truth.
   Medical outcomes may take weeks.
   Loan outcomes may take months.
   Ledge stores decisions indefinitely.

## Limitations of self-reported outcomes

- If outcomes are biased (only recording easy cases),
  calibration will be biased
- If ground truth is ambiguous, ECE will be noisy
- Recommended minimum: 30 outcomes per domain before
  trusting calibrated thresholds

## What is drift and how Ledge handles it

Drift means the real-world distribution changes over 
time. Examples:
- New phishing patterns not seen during calibration
- Model updated by provider without notice
- Population of applicants shifts

Ledge does not automatically detect drift.
What you can do:
- Run --calibration-metrics regularly and compare
- Set a recalibration schedule (e.g., monthly)
- Use --compare to detect when a model's behavior changes

Example: check calibration quality monthly
    ledge audit --calibration-metrics gpt-4 medical

If ECE increases significantly month over month,
your calibration data may be outdated.

## Domain separation

Each (model, domain) pair has independent calibration.
gpt-4/medical and gpt-4/legal never mix data.
The domain string is set by the program_id parameter
in the audit trail.

## Recommended minimum data before trusting calibration
- 30 outcomes for initial threshold
- 100 outcomes for reliable ECE and false rates
- Recalibrate when you have 50+ new outcomes
