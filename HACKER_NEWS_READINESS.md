# Hacker News readiness audit — Ledge 1.2.0

This document records the audit and changes made before a Hacker News
launch. It is written for two audiences: the maintainer (so the decisions
are explicit and reversible) and a hostile reviewer (so they can verify
that the README claims match the implementation).

## TL;DR

The central language-level contract was strengthened, not weakened. The
documentation was narrowed to match what the code actually does. A new
escape hatch (`unsafe_value_of`) makes the unsafe path visible. The
quickstart now works after a plain `pip install` with no clone.

## Claims that were removed or softened

These phrases were either deleted, replaced, or qualified across the
docs (chiefly README.md, GUARANTEES.md, CURRENT_STATUS.md,
EXECUTIVE_SUMMARY.md, DEPLOY.md, and source-file docstrings in
`ledge_lang/typechecker.py` and `ledge_lang/ai_types.py`):

- "dependent types or effect systems that Python does not have. Ledge
  has them" — removed. The static analyzer is an AST walker, not a
  dependent type system or an effect system. It is now described
  accurately as "a single-file, flow-sensitive AST walker with documented
  limitations."
- "owns the type system entirely" — removed.
- "the only way to use the result is to handle uncertainty explicitly" —
  removed. There is no "only way"; there are recognized patterns and an
  explicit escape hatch.
- "Four verifiable guarantees" — softened to "Four properties you can
  verify in your terminal." The word "guarantee" is now reserved for the
  precise one-paragraph statement in the README.
- "tamper-proof" / "tamper-evident" framing in the audit-trail
  description — replaced with a threat model that explicitly names the
  attacker who controls both the SQLite store and the anchor file as
  beyond the scope of detection.
- "No other language has this" / "introduces types no other language
  has" in `ai_types.py` — removed. The Uncertain/Stream/Pipeline runtime
  primitives have well-known analogues in other ecosystems; the
  Ledge-specific part is the static-checker contract, not the runtime
  shape.
- "Compliance-ready" / strong compliance verbs — replaced with
  "compliance-supporting" and "supporting evidence" with explicit
  pointers to the necessary-but-not-sufficient caveat.
- "first programming language designed for AI-first software" — removed
  from DEPLOY.md and EXECUTIVE_SUMMARY.md.
- "Verified lemmas" / "Formal type system" / "Executable formal proof"
  in EXECUTIVE_SUMMARY.md — removed. The empirical demo scripts remain,
  framed as "demos exercising one runtime behavior" rather than as proofs.
- "Audit score 970/1000" — removed. It was an internal scoring artifact
  with no external meaning.

## Code changes (the implementation that backs the new claims)

### 1. Strengthened static contract for `value_of`

Files: [`ledge_lang/typechecker.py`](ledge_lang/typechecker.py),
[`ledge_lang/ai_types.py`](ledge_lang/ai_types.py).

Before 1.2.0:

```ledge
define r as classify(symptoms) using ["urgent", "routine"]
show value_of(r)                          # ACCEPTED — checker silently OK'd it
```

This contradicted the README's claim that "the only way to use the
result is to handle uncertainty explicitly." Explicit extraction
without a confidence check was passing the checker.

After 1.2.0:

```ledge
define r as classify(symptoms) using ["urgent", "routine"]
show value_of(r)                          # ERROR — value_of outside a guard
if confidence_of(r) >= 0.85:
    show value_of(r)                      # OK — narrowed inside guard
show when(r, 0.85, "fallback")            # OK — runtime-checked extraction
show unsafe_value_of(r)                   # OK — explicit escape hatch
```

The change is purely in the static checker. The runtime behavior of
`value_of` is unchanged. Specifically:

- Removed `value_of` from `UNCERTAIN_SAFE_BUILTINS` and from the
  `("when", "value_of")` short-circuit in call inference.
- Added `unsafe_value_of` to both, registered as a new runtime builtin
  in `ai_types.py` with the same body as `value_of`.
- Updated the error-message suggestions so the recommended fix is a
  confidence guard, not "use `value_of(r)` instead of `show r`."

### 2. New tests for the strict contract

File: [`tests/unit/test_typechecker.py`](tests/unit/test_typechecker.py).

- Removed `test_value_of_is_safe` (it encoded the weak contract).
- Removed `test_map_classify_value_of_is_safe`.
- Added `test_value_of_without_guard_is_error` (`value_of` on a bare
  Uncertain is now rejected).
- Added `test_value_of_inside_confidence_guard_is_safe` (`value_of`
  inside `if confidence_of(r) >= t:` is accepted).
- Added `test_value_of_inside_is_confident_guard_is_safe`.
- Added `test_unsafe_value_of_is_allowed_outside_guard`.
- Added `test_map_classify_value_of_without_guard_is_error`.
- Added `test_map_classify_unsafe_value_of_is_allowed`.

Full suite: 343 passing (up from 339). Conformance: 284/284.

### 3. Packaging — the broken pip-install quickstart

Before 1.2.0:

- README told users to `pip install ledge-lang && ledge run examples/showcase/medical_triage.ledge`.
- `examples/` was not bundled in the wheel or sdist, so the second
  command failed with file-not-found.

After 1.2.0:

- Added `ledge demo <name>` CLI subcommand in
  [`ledge_lang/cli.py`](ledge_lang/cli.py).
- Bundled a curated demo in
  [`ledge_lang/demos/medical_triage.ledge`](ledge_lang/demos/medical_triage.ledge)
  that passes the strict typechecker.
- Added `[tool.setuptools.package-data]` to
  [`pyproject.toml`](pyproject.toml) so the `.ledge` files ship in the
  wheel.
- README quickstart now reads `pip install ledge-lang && ledge demo
  medical_triage`. Verified to work end-to-end.
- Full showcase examples (financial, legal, hiring, etc.) still require
  cloning the repo — the README now says so explicitly.

### 4. Source-file docstrings

The inflated framing in
[`ledge_lang/ai_types.py`](ledge_lang/ai_types.py) ("Introduces types
that no other language has", "tamper-evident", "required by GDPR,
HIPAA", "No other language provides this automatically") was a
liability for a Hacker News reader who clicks into the source. Replaced
with accurate, scoped descriptions.

The
[`ledge_lang/typechecker.py`](ledge_lang/typechecker.py) module
docstring now lists the recognized handling constructs and the
documented limitations explicitly.

## Guarantees that remain (precise)

These are stated narrowly enough to be checkable:

1. **Static rejection of direct Uncertain[T] use.** Programs that use a
   value typed `Uncertain[T]` without going through a recognized
   handling construct (confidence guard, `when`, `unsafe_value_of`) are
   rejected by `ledge check --types` before any code runs. The set of
   recognized constructs is the small list in
   [README.md](README.md#the-checkers-contract-precisely) and tested by
   `tests/unit/test_typechecker.py`.

2. **Zero confidence without a backend.** Without a connected AI
   backend, every AI primitive returns `confidence = 0.0`. Verified by
   `demo_guarantee1.py`.

3. **Detection of audit-log modification by an actor without anchor-file
   access.** Modifying any field of any audit entry causes
   `audit_verify()` to return `false`; deleting and rebuilding the
   SQLite store leaves the anchors inconsistent. Verified by
   `demo_guarantee3.py` and `ledge audit --verify-anchors`. Limited
   threat model — does NOT protect against an attacker with read/write
   access to both the database AND the anchor file.

4. **Fail-safe default when no backend.** A consequence of (2). Programs
   whose decision threshold is above 0.0 take the low-confidence branch.
   This is a property of escalation-pattern programs, not of the runtime
   itself.

## Limitations now made explicit (in README, GUARANTEES, source)

- Intraprocedural checker only. Uncertain is not tracked across
  function call boundaries beyond annotated signatures.
- Early-return guards (`if confidence_of(x) < t: return; use(x)`) are
  NOT recognized. The if/else form must be used, or `unsafe_value_of`.
- `not is_uncertain(x)` is NOT a recognized narrowing form.
- Only one hop of confidence-alias narrowing (`define c as
  confidence_of(x)` → `if c >= t:`).
- No lambda-internal narrowing.
- Calibration is empirical, not a proof of model correctness.
- OpenAI logprobs are token-probability-derived signals, sensitive to
  first-token classification, multi-token labels, top-logprob
  truncation, prompt phrasing, and provider-side model drift. NOT
  calibrated correctness probabilities.
- Anthropic confidence is structured self-assessment — self-reported,
  not derived from model weights.
- The regulatory export is a structurally valid evidence schema, not a
  compliance product. Legal compliance in any jurisdiction requires
  counsel.
- Audit trail does NOT protect against an attacker who controls both
  the SQLite store and the anchor file, or against an attacker with
  access to the in-memory `AuditTrail` object.
- Zero known production deployments.

## What did NOT get done in this pass

These are scoped for follow-up rather than included now, in the
interest of keeping the change reviewable:

- The `docs/` directory still contains documents titled "Formal
  Specification" (TYPE_SYSTEM.md, SEMANTICS.md, GRAMMAR.md). The
  inference rules in TYPE_SYSTEM.md are accurate as a description of
  the checker but should be retitled "Static analysis rules
  (informal)" or similar — the word "formal" reads as a soundness claim
  that the file does not make. SEMANTICS.md has an "Theorem (Informal)"
  marker which is honest, but the file title should follow.
- `docs/AI_SAFETY_STUDY.md` uses "IMPOSSIBLE BY DESIGN" twice — should
  read "rejected by the static analysis pass."
- `docs/SPEC.md` has "Ledge is the first language designed for the
  inverse order of priority" — remove "first."
- `docs/LAUNCH.md` and `docs/RED_TEAM.md` contain residual "impossible
  in Python" framing that should be narrowed to specific operations.
- The other showcase examples (`examples/showcase/*.ledge`) still use
  the early-return-on-low-confidence pattern that the strict checker
  doesn't recognize. They run fine via `ledge run` (which doesn't
  typecheck) but `ledge check --types examples/showcase/<file>.ledge`
  will report errors. Two options: extend the checker to recognize
  early-return narrowing, or refactor each showcase to the if/else
  form.
- Adding `ledge check --types` to a CI gate would prevent regressions
  in claim/code alignment. Worth doing before a major release.

## What would be required to make a stronger PL claim

If the project wants to make a serious "type system" claim later,
these are the missing pieces:

- A formal grammar separate from the implementation (the grammar in
  `docs/GRAMMAR.md` is a description, not a normative spec).
- A formal type rules document with judgment-style notation and at
  least one paper-and-pencil soundness argument.
- Either a mechanized proof (Lean/Coq/Agda) or a property-based test
  suite that approximates the soundness property by random testing
  rather than by example.
- Interprocedural Uncertain tracking, since intraprocedural-only is a
  meaningful gap for production code.
- Independent third-party review of the type rules and threat model.

## Files changed in this pass

Code:

- `ledge_lang/typechecker.py` — strict `value_of` contract, docstring
  rewrite, suggestion-text updates.
- `ledge_lang/ai_types.py` — registered `unsafe_value_of` runtime
  builtin, softened class docstrings.
- `ledge_lang/cli.py` — added `ledge demo` subcommand.
- `ledge_lang/demos/__init__.py` — new module exposing
  `list_demos()` and `demo_path()`.
- `ledge_lang/demos/medical_triage.ledge` — new bundled demo that
  passes the strict checker.
- `pyproject.toml` — `[tool.setuptools.package-data]` entry for
  `*.ledge`; version bumped to 1.2.0.
- `ledge_lang/__init__.py` — `__version__` bumped to 1.2.0.
- `vscode-ledge/package.json` — version bumped to 1.2.0.

Tests:

- `tests/unit/test_typechecker.py` — six tests added/inverted for the
  new contract.

Docs:

- `README.md` — substantial rewrite per the brief.
- `GUARANTEES.md` — wording softened, threat model added, G2 limitations
  list updated to match checker docstring.
- `CURRENT_STATUS.md` — brought current with 1.2.0; PyPI status corrected.
- `EXECUTIVE_SUMMARY.md` — rewritten to remove formally-verified claims.
- `DEPLOY.md` — removed "first programming language" framing; PyPI
  status corrected; release notes updated.
- `HACKER_NEWS_READINESS.md` — this file.

## Verification commands

```
py -m pytest tests/unit/                   # 343 passing
py tests/conformance.py                    # 284 / 284
py -m ledge_lang.cli check --types ledge_lang/demos/medical_triage.ledge
py -m ledge_lang.cli demo medical_triage
py demo_guarantee1.py && py demo_guarantee2.py && py demo_guarantee3.py && py demo_guarantee4.py
py -m build && unzip -l dist/ledge_lang-1.2.0-py3-none-any.whl | grep demos
```
