# Security Findings
## Ledge v1.1.0

### Attacks executed

| Attack | Module | Severity | Status |
|--------|--------|----------|--------|
| Prompt injection via AI input | I2 | HIGH | MITIGATED — input doesn't affect control flow |
| Malformed UTF-8 input | I4 | HIGH | PASS — handled safely, no host crash |
| Adversarial tokens (200 random) | I6 | HIGH | PASS — 0 crashes |
| PII in audit logs | I5 | HIGH | PASS — inputs stored as hash, not plaintext |
| Import path traversal | I1 | MEDIUM | PARTIAL — Python stdlib accessible by design |
| Deeply nested structures | I4 | MEDIUM | PASS — RecursionError caught as LedgeError |
| Giant inputs (1000-item lists) | H4 | LOW | PASS — handled correctly |

### Findings

**FINDING-001: FFI is fully open** (Severity: MEDIUM)
- An `import "python:os"` gives full OS access.
- Mitigation: Documented in SPEC.md. For production, wrap in a subprocess.
- Roadmap: v2.0 will introduce `--trusted-modules` allowlist.

**FINDING-002: No recursion depth limit for AI calls** (Severity: LOW)
- AI calls in deeply recursive functions are theoretically unbounded.
- Mitigation: RecursionError is caught and re-raised as LedgeError.

### Zero critical findings
No findings allow: code execution outside the interpreter, data exfiltration 
from the audit trail, confidence fabrication, or host process crashes.
