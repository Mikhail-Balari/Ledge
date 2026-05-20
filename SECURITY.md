# Security Policy

Ledge is alpha software. It is useful for experimenting with uncertainty-aware
AI decision boundaries, but it is not a security boundary for running untrusted
code and it is not production-critical infrastructure.

## Reporting a Vulnerability

Please report security issues responsibly. Prefer GitHub private vulnerability
reporting or a GitHub Security Advisory for this repository if that option is
available to you. If a private reporting channel is not available, avoid posting
exploit details publicly; open a minimal GitHub issue asking the maintainer to
coordinate a private channel.

Do not include secrets, API keys, private data, or exploit payloads in public
issues.

## In Scope

Reports that are especially useful include:

- Static checker bypasses that allow unchecked `Uncertain[T]` values to execute
  through the checked CLI or `checked_run(...)`.
- Surprising behavior around `ledge run --unsafe` or other explicit bypasses.
- Package or supply-chain issues affecting installation or execution.
- Audit trail integrity issues within the documented threat model.
- Sensitive-data leakage in logs, audit records, diagnostics, or exports.

## Out of Scope

Ledge does not currently provide:

- A sandbox for untrusted Ledge programs.
- A security boundary against malicious local operators.
- Legal, regulatory, or security certification.
- Protection for host Python code that intentionally bypasses checked entry
  points or imports unsafe modules.

For deployment assumptions and non-goals, see
[`docs/THREAT_MODEL.md`](docs/THREAT_MODEL.md).
For package dependency and supply-chain visibility, see
[`docs/SUPPLY_CHAIN.md`](docs/SUPPLY_CHAIN.md).
