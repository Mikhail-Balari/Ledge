# Ledge Changelog

## [1.7.0] - Alpha

### Added

- Adds `ledge_lang.ledger.DecisionEvent` for semantic AI
  decision-boundary events.
- Adds canonical event serialization and SHA-256 event hashing.
- Adds previous-hash linking for tamper-evident local event chains.
- Adds `DecisionLedger` append-oriented JSONL storage.
- Adds `LedgerManifest` build/read/write support.
- Adds `LedgerVerifier` with structured findings.
- Adds human-readable and machine-readable verification results.
- Adds ledger CLI commands:
  - `ledge ledger-init`
  - `ledge ledger-append`
  - `ledge ledger-manifest`
  - `ledge ledger-verify`
  - `ledge ledger-export`
  - `ledge ledger-review-pack`
- Adds a local audit review export package.
- Adds an AI-readable ledger review pack.
- Adds SDK-facing `LedgerRecorder`.
- Adds `record_decision_event(...)`.
- Adds safe `record_decision_result(...)` adapter.
- Adds an end-to-end low-stakes ledger example under `examples/ledger/`.

### Notes and limitations

- Alpha release.
- Not production-ready or enterprise-ready.
- Not legal compliance certification.
- The decision ledger is tamper-evident, not tamper-proof.
- Uses local append-oriented records plus verification, not immutable storage,
  blockchain, remote attestation, or secure storage by itself.
- Does not guarantee truth and does not prevent hallucinations.

## [1.6.0] - Alpha

### Added

- Adds audit-ready `ledge_lang.confidence.ConfidenceEvidence`.
- Adds `EvidenceSource` and canonical evidence serialization.
- Adds evidence hashing and redaction helpers.
- Adds schema validation, ensemble agreement, logprob signal, conservative
  scoring, and calibration report support.
- Adds redaction-safe confidence and calibration report rendering.
- Adds CLI commands:
  - `ledge confidence-eval`
  - `ledge calibration-report`
- Adds low-stakes examples under `examples/confidence/`.
- Adds an SDK evidence interoperability layer for legacy and audit-ready
  evidence objects.

### Changed

- `Uncertain(..., evidence=...)` now normalizes legacy, audit-ready, unknown,
  and malformed evidence through a private SDK interoperability layer.
- Legacy regulatory/compliance-shaped wording is corrected to
  evidence-field wording.

### Notes

- Alpha release.
- Not production-ready.
- Not legal compliance certification.
- Does not guarantee truth or prevent hallucinations.
- Tamper-evident decision ledger remains future Phase 4.

## [1.5.0] - Alpha

- Adds `ledge lint-python <paths...>` for AST-based Python decision-boundary
  linting.
- Adds the Python linter package under `ledge_lang/python_linter`.
- Adds rules:
  - `LPY001`: `unsafe_unwrap` requires a non-empty reason.
  - `LPY002`: direct `.value` access on tracked `Uncertain`.
  - `LPY003`: configured critical action receives an unhandled uncertain value.
  - `LPY004`: `DecisionResult.value` is used in a configured critical action
    outside an allow guard.
- Adds `ledge.toml` support for configured critical actions.
- Adds text and JSON linter output.
- Adds low-stakes safe and unsafe Python linter examples.
- Adds a GitHub composite action for CI usage.
- Adds unit and integration tests for Python linter behavior.
- Tracks `from ledge_lang import sdk` for straightforward SDK constructor use.
- Validates configured `ledge.min_confidence` when present.
- Notes realistic AST limitations for dynamic Python flows, cross-function
  aliasing, and framework-specific behavior.
- Does not add provider integrations.
- Does not add a mypy or Pyright plugin.
- Makes no production-readiness, enterprise-readiness, compliance-readiness, or
  formal-verification claims.

## [1.4.1] - Alpha

Docs-only patch.

- Clarifies README positioning now that Ledge includes both the DSL and the
  Python SDK Core.
- Replaces outdated "DSL instead of Python library" framing with "DSL plus SDK"
  framing.
- Keeps the honest trade-off: SDK improves adoption/integration, while the DSL
  remains the stricter boundary layer.
- No SDK behavior changes.
- No CLI changes.
- No DSL/runtime changes.
- No new features.
- No production-readiness, enterprise-readiness, compliance-readiness, or
  model-correctness claims.

## [1.4.0] - Alpha

- Adds Python SDK Core under `ledge_lang.sdk`.
- Adds `Uncertain[T]`, `DecisionPolicy`, `DecisionResult[T]`, and minimal
  `ConfidenceEvidence`.
- Adds SDK exceptions and validation helpers.
- Adds deterministic fake client utilities for examples and tests only.
- Adds a low-stakes customer-support refund-routing SDK example.
- Adds SDK unit and integration tests.
- Keeps SDK enforcement API/runtime-level only.
- Does not add Python static linting or CI enforcement yet.
- Does not add a calibrated Confidence Evidence Engine yet.
- Does not add provider integrations or real LLM clients.
- Makes no production-readiness, enterprise-readiness, compliance-readiness, or
  model-correctness claims.

## [1.3.1] - Alpha patch

Documentation and release-metadata cleanup after the 1.3.0 publication.

- Bumps package metadata to `1.3.1`.
- Clarifies that the installed package exposes:
  `ledge demo loan_approval`, `ledge pilot-dry-run loan_approval`,
  `ledge python-integration-demo`, and `ledge ci-check <paths...>`.
- Removes stale "candidate", "unreleased", and "not yet published" wording
  left over from the 1.3.0 release-readiness phase.
- Keeps source-checkout wrapper commands documented separately from installed
  package commands.
- Adds no new runtime features.
- Makes no production-readiness, enterprise-readiness, compliance-readiness, or
  model-correctness claims.

## [1.3.0] - Alpha pre-release

Release status:

- PyPI: published.
- Git tag: `v1.3.0` created and pushed.
- GitHub Release: `Ledge 1.3.0` created as a pre-release.

Installed package / CLI changes:

- Bundled synthetic `loan_approval` demo for `ledge demo loan_approval`.
- Existing bundled `medical_triage` demo remains available through
  `ledge demo medical_triage`.
- Packaged synthetic pilot dry-run command:
  `ledge pilot-dry-run loan_approval`.
- Packaged Python integration demo command:
  `ledge python-integration-demo`.
- Packaged CI/static checker command:
  `ledge ci-check <paths...>`.
- Version metadata prepared for `1.3.0`.

Source-checkout materials preserved:

- Public demo and pilot planning docs: `DEMO.md`, `COMMERCIAL.md`,
  `PILOT_PACK.md`.
- Pilot templates under `pilot_templates/`.
- Synthetic pilot dry-run harness:
  `python scripts/run_pilot_dry_run.py pilot_templates/loan_approval`.
- Minimal Python integration example:
  `python examples/python_integration/app.py`.
- CI/static checker helper:
  `python scripts/ledge_check_ci.py ledge_lang/demos examples/python_integration`.

Notes:

- The wheel exposes installable commands for the pilot dry run,
  Python integration demo, and CI/static checker.
- The root-level `pilot_templates/`, `examples/python_integration/`, and
  `scripts/` wrappers remain source-checkout materials for review and
  adaptation.
- This remains alpha software. This release does not claim
  production readiness, enterprise readiness, compliance certification, model
  correctness, or calibrated confidence.

---

All changes follow semantic versioning.
Breaking changes only occur on MAJOR version bumps.

---

## [1.1.1] — 2026-05-14

### Bug fixes

- **PyPI metadata** — `[project.urls]` in `pyproject.toml` pointed at the
  placeholder `github.com/ledge-lang/ledge` repository, which does not exist.
  All three URLs (`Homepage`, `Documentation`, `Issue Tracker`) now point at
  the real repository `github.com/Mikhail-Balari/Ledge`.
- **Author metadata** — `authors` updated from the generic
  "Ledge Language Project" placeholder to `Mikhail Balari`.

---

## [1.1.0] — 2025

### New features

- **Linter** (`ledge_lang/linter.py`) — separate from typechecker
  - `E001`: unsafe use of AI result without confidence guard
  - `W011`: function with AI operations but no `requires:` contract
  - `S020/S021/S022`: style rules (function length, nesting, unused vars)
  - CLI: `ledge check --lint file.ledge`
- **Flow typing** — typechecker narrows `Uncertain[T]` to `T` inside
  `if is_confident(r):` and `if confidence_of(r) >= 0.8:` blocks
- **VM: FOR loop** — `for each x in list:` now compiles to bytecode VM
  (was tree-walker only). VM now handles 20/20 language constructs.
- **Comparative positioning material** - side-by-side examples explaining
  tradeoffs between Ledge and ordinary Python patterns
- **Formatter** — `WhenStmt` and `AgentDef` now format idempotently

### Bug fixes

- **FOR loop in VM** used `Op.LEN`/`Op.INDEX` which didn't exist.
  Now uses `len()` builtin call + `LOAD_INDEX` opcode.
- **AgentDef formatter** referenced `node.body` (doesn't exist).
  Now uses correct attributes: `tools`, `model_name`, `behavior`.
- **mcp_agent.ledge** crashed with "nothing is not callable" because
  MCP tool calls return `nothing` without a real MCP server.
  Rewritten with proper `or` fallbacks.
- **Postcondition error** showed AST repr (`BinOp(op='>', ...)`)
  instead of readable condition. Now shows `result > 100`.
- **Index error** missing `Fix:` suggestion — added.
- **Test helper functions** `test_fmt`, `test_tc`, `test_stdlib`, `test_vm`
  were being collected by test runner with wrong arity. Renamed to `_test_*`.

### Tests

- Conformance: 284/284
- Unit tests: 324/326 (2 fallas de encoding en Windows — pre-existentes)
- Differential: 47/47
- Fuzz: 10/10

---

## [1.0.0] — 2025

Initial AI-native release. The project aims to preserve backward compatibility
within major version 1 where practical, but no formal compatibility guarantee is
offered while Ledge remains alpha software.

### AI-Native Features (new in 1.0)

- **`Uncertain[T]`** — first-class type for all AI operation results
- **Zero confidence without backend** — `analyze/classify/generate/ask/embed`
  return `confidence=0.0` and `value=nothing` when no AI backend is connected.
  Runtime fail-safe default; the language never returns a non-zero
  confidence in the absence of a connected backend.
- **Automatic audit trail** — every AI call is automatically logged with
  input hash, confidence, model, and timestamp. `audit_query()` and
  `audit_export()` produce supporting evidence for governance review;
  not by themselves a GDPR/HIPAA/regulatory compliance claim.
- **Typechecker enforcement** — using `Uncertain[T]` without extracting the value
  is a type ERROR (not warning). Safe extraction: `when(r, 0.8, fallback)`.
- **Contracts** — `requires:` / `ensures:` blocks in function definitions.
  Preconditions fire before the body. Postconditions fire after. Both raise
  `LedgeError` on violation with the failing condition shown.
- **`stream_of` / `stream_where` / `stream_map`** — lazy stream primitives.
  Streams from lists are re-iterable. Infinite generators work correctly.
- **`when stream has new item as x:`** — reactive iteration over streams.
- **`parallel [e1, e2, ...]`** — true concurrent execution via threading.
  Results returned in declaration order regardless of completion order.

### Architecture (new in 1.0)

- **`core_types.py`** — all base types (`NOTHING`, `LedgeList`, `LedgeMap`,
  `LedgeError`, `Env`, `LedgeFunction`) live in a single module with no
  internal dependencies. Eliminates circular import between `interpreter.py`
  and `ai_types.py`.
- **Python FFI** — `import "python:numpy" as np` — full Python ecosystem
  available in one line. Zero rewrite cost for existing Python users.
- **Type enforcement on `set`** — `set x to value` enforces the type annotation
  declared at `define` time.

### Test suite (new in 1.0)

- **143 unit tests** in pytest-compatible format (`tests/unit/`)
- **284 conformance tests** at 100% pass rate (`tests/conformance.py`)
- **40 differential tests** proving tree-walker and VM produce identical
  output for the official VM-supported subset (`tests/differential/`)
- **10 fuzzer tests** — deterministic, seeded, reproducible. 0 crashes
  on adversarial inputs including null bytes, Unicode, infinite recursion,
  and deeply nested structures.
- **6 example tests** — all official examples verified to run without
  fake AI confidence or misleading output.
- **21 typechecker tests** — verifying AI-native safety enforcement.

### Documentation (new in 1.0)

- `docs/SEMANTICS.md` — implementation-oriented semantics (reference for implementors)
- `docs/FEATURE_MATRIX.md` — honest shipped/experimental/roadmap status
- `docs/GOVERNANCE.md` — versioning policy, proposal process, bus factor plan
- `docs/RED_TEAM.md` — live list of strongest criticisms with resolution status
- `docs/COMPARATIVE_POSITIONING.md` — honest comparison with Python/Go/others

### Bug fixes

- **Critical: fake AI confidence** — `analyze()` without backend previously
  returned `confidence=1.0`. Now returns `confidence=0.0`. This was a fundamental
  correctness issue.
- **Critical: `classify()` picking first label** — without a backend, classify
  previously returned the first label silently. Now returns `value=nothing`.
- **`AuditTrail` falsy when empty** — `bool(empty_audit)` was `False` due to
  `__len__` returning 0. Added `__bool__ = True`. Fixes `if self._audit:` check.
- **Generators re-iteration** — `stream_where` and `stream_map` were consuming
  the source iterator once. Now use parent-chain architecture for re-iteration.
- **`stream_where` calling convention** — fixed mismatch between how lambdas
  were registered as filters and how `_chain_iter` called them.
- **VM `True==1` collision** — constants `True` and `1` were interned to the
  same slot. Fixed by type-strict deduplication in `add_const`.
- **`classify` / `analyze` as user function names** — keywords now allow
  lookahead to distinguish AI instructions from user-defined functions.

---

## [0.2.0] — 2025

### New features

- Lazy generators via thread+queue — infinite sequences work correctly
- Python FFI: `import "python:module" as alias`
- Real parallel execution via `threading.Thread`
- Type enforcement on `set` when variable has annotation
- Error messages with edit-distance suggestions ("did you mean X?")
- `group_by`, `take_while`, `drop_while`, `zip_with` as HOF builtins
- `stream_of`, `stream_where`, `stream_map`, `stream_take`, `stream_collect`
- `when` reactive blocks
- `requires:` / `ensures:` contract syntax (basic version)

### Bug fixes

- `yield` outside function: unhandled `_Yield` exception → now `LedgeError`
- `break` outside loop: unhandled `_Break` exception → now `LedgeError`
- VM `JUMP_IF_FALSE` left condition on stack → now pops correctly
- VM `True==1` in constant pool → type-strict deduplication
- Repeat loop unimplemented in VM → now compiles correctly

---

## [0.1.0] — 2025

Initial release. Core language, basic tooling.
Not covered by any stability guarantee.
