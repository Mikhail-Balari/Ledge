# Ledge Security Model
## Version 1.1.0

---

## FFI Security Boundary (I1)

Ledge's `import "python:module"` gives access to ANY Python module
available in the host environment. This is **intentional** for the
research phase — it maximizes interoperability.

### What this means in practice

```ledge
import "python:os"      as os_mod    # Full filesystem access
import "python:socket"  as net       # Network access
import "python:subprocess" as proc   # Execute shell commands
```

**This is a feature, not a bug, for trusted environments.**
Ledge is designed for AI workloads where the code author is trusted.

### Threat model

| Scenario | Risk | Mitigation |
|----------|------|------------|
| Developer running own code | None | Full FFI intentional |
| AI-generated code (trusted) | Low | Review before running |
| Untrusted code | HIGH | Use Docker/subprocess isolation |
| Multi-tenant execution | HIGH | NOT supported in v1.1 |

### For restricted deployments

Run Ledge inside a container with restricted filesystem/network:

```bash
# Docker with no network + read-only filesystem
docker run --network=none --read-only ledge-runtime ledge run program.ledge

# Or use Python's restricted exec (limited but available)
ledge run --restrict-ffi program.ledge  # roadmap v2.0
```

### Roadmap: v2.0 `--trusted-modules` allowlist

```bash
# Future: restrict which modules can be imported
ledge run --allow-import math,json program.ledge
# Any other import "python:X" will fail with a clear error
```

---

## Permission Model (I3)

By default, Ledge programs inherit all permissions of the host process.

| Permission | Default | How to restrict |
|------------|---------|-----------------|
| File system read | INHERITED | Run as low-privilege user |
| File system write | INHERITED | Run in read-only container |
| Network access | INHERITED | `--network=none` in Docker |
| Subprocess execution | INHERITED | Block `python:subprocess` |
| Environment variables | INHERITED | Strip env vars before running |

### AI operations

AI operations (`analyze`, `classify`, `generate`) do NOT inherit
any special permissions. Without a backend, they return `confidence=0.0`.
With a backend, the backend's permissions apply.

### Audit trail

Every AI operation is automatically logged to the in-process audit trail.
The log stores input **hashes**, not plaintext — this prevents accidental
PII leakage in log files.

---

## Security invariants (always enforced)

1. **Zero fake AI confidence** — without backend, `confidence=0.0`
2. **No execution injection** — AI inputs don't affect control flow
3. **Audit trail integrity** — every AI call is logged; log is append-only
4. **Type safety** — Uncertain[T] cannot be used as certain without extraction
5. **Safe operations** — divide/index/lookup return `nothing`, never crash

---

## Reporting security issues

Open a GitHub issue labeled `[SECURITY]`. Please include:
- Reproduction case (minimal Ledge program)
- Expected vs actual behavior
- Whether PII could be exposed
