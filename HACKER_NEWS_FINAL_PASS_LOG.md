# Hacker News Final Pass — Working Log

Started: 2026-05-14

This is the running working log for the autonomous pre-HN hardening pass.
Detailed output for each phase is written to its own file; this log only
records intent, decisions, failures, and fixes.

## Status checkpoint (2026-05-14)

- **Phase 1 — risky-phrase audit:** COMPLETE. Output in `hn_risky_phrases.txt`.
- **Phase 2 — patch risky doc language:** COMPLETE. 20 files patched.
- **Phase 3 and later:** NOT STARTED.
- **Release:** Do NOT publish to PyPI yet. Version stays at 1.2.0 in the
  source tree; the 1.2.0 wheel was built earlier in the session but has
  NOT been uploaded.
- **Next step on resume:** continue from Phase 3 — typecheck all official
  `.ledge` examples (`examples/*.ledge`, `examples/showcase/*.ledge`,
  `ledge_lang/demos/*.ledge`) under the strengthened 1.2.0 checker, and
  decide per-example whether to refactor to a recognized guard pattern
  or use `unsafe_value_of`.

## Current task

## Phase 1 results

- Risky lines found: **254**
- Output saved to: `hn_risky_phrases.txt`
- Regex used (case-insensitive): `formal|soundness|proof|verified|guaranteed|guarantees|IMPOSSIBLE BY DESIGN|impossible in Python|first language|first programming language|tamper-proof|tamper-evident|compliance-ready|compliant|no other language|\bunique\b|only way|revolutionary`
- Scope: all files under repo root (default ripgrep ignores).

Many matches are unavoidable / harmless (e.g. `audit_verify()` API name,
test names containing "verified", historical CHANGELOG entries). Phase 2
triaged per file.

## Phase 2 — files changed

20 files patched. Edits were targeted (per-section, no broad rewrites)
to preserve technical content while removing or softening claims of
formal verification, soundness, legal compliance, tamper-proofness,
uniqueness, or first-language status.

1. `vscode-ledge/package.json` — description string: "first programming language" → "experimental DSL".
2. `docs/TYPE_SYSTEM.md` — title "Formal Specification" → "Static Analysis Rules"; new framing paragraph; renamed Section 5 from "Soundness Property (Partial)" to "Intended static-analysis property (informal)"; "Theorem (Informal)" → "Informal claim"; the prohibition rule's whitelist updated to use `unsafe_value_of` instead of `value_of` to match the strict checker.
3. `docs/SEMANTICS.md` — title "Formal Operational Semantics" → "Implementation-Oriented Semantics"; "normative reference" framing softened.
4. `docs/GRAMMAR.md` — title "EBNF Formal Specification" → "EBNF Reference"; "normative" framing softened.
5. `docs/AI_SAFETY_STUDY.md` — both "IMPOSSIBLE BY DESIGN" headings replaced with "rejected by the static checker under the documented checker rules"; conclusion section "structurally impossible" softened to "rejected under documented rules", with explicit reference to `unsafe_value_of` escape hatch.
6. `docs/SPEC.md` — "Ledge is the first language" → "Ledge is an experimental DSL"; "complete formal grammar" → "complete grammar"; "compatibility is guaranteed" softened to "intends to preserve compatibility, no formal guarantee while pre-1.x-stable".
7. `docs/LAUNCH.md` — "first programming language" → "experimental DSL".
8. `docs/RED_TEAM.md` — "impossible in Python" → "not enforced by ordinary Python runtime semantics without additional tooling (a mypy plugin, a Pyright plugin, or a custom linter could approximate this)".
9. `docs/QUICKSTART.md` — "formal operational semantics" reference → "implementation-oriented semantics"; "safety guarantee" → "runtime fail-safe default".
10. `docs/PUBLIC_STATEMENT.md` — "production-quality... with a formal specification" softened; recommended public framing rewritten to drop "formal semantics" and "AI-native programming language" framing.
11. `docs/LEDGE_V1_VISION.md` — "exist in no other language" → softer "Ledge makes language-level" framing acknowledging analogues; "compiler guarantees" → runtime/static distinction.
12. `docs/SCORECARD.md` — "Rigor formal" row reframed as "Reference completeness"; "Innovación real ... unique" softened to acknowledge analogues.
13. `TECHNICAL_REPORT.md` — abstract reframed (no longer claims "first-class type ... enforced by the type system"; states checker is not a formal type system); "Four verifiable runtime guarantees" → "Four verifiable runtime properties" in §1 contributions, §5 heading, and individual property descriptions; §4 "Formal Grammar" → "Grammar"; §9 limitations rephrased; future-work line "Formal type system specification and mechanized proofs" softened to "more formal type-rules document ... paper-and-pencil or mechanized proof"; "Distributed audit trail with cryptographic guarantees across nodes" → "with cross-node hash chaining".
14. `RESPONDING_TO_EXPERTS.md` — "EU AI Act Article 12/13 compliant" → "structured against EU AI Act Article 12/13 evidence schema" with explicit "supporting evidence, not certification" caveat; stale "338 unit tests + 284 conformance" replaced with "see CI/test suite" framing and pointer to GUARANTEES.md.
15. `examples/medical_triage.ledge` — "HIPAA compliant by design" → "useful as supporting evidence; not by itself a HIPAA compliance claim"; "compiler guarantees these invariants" → "runtime checks these invariants; the static checker does not prove them"; "tamper-evident and reproducible" → "hash-chained audit log (limited threat model — see GUARANTEES.md)".
16. `examples/showcase/medical_record.ledge` — "tamper-evident audit trail" comment softened; final "tamper-evident log — every diagnosis is permanently traceable" → "hash-chained audit log (limited threat model)".
17. `examples/showcase/legal_contracts.ledge` — "The system guarantees that NO low-confidence clause passes without review" → narrower description of the program's escalation pattern.
18. `GUARANTEES.md` — all four "Proof you can run yourself" headings replaced with "Verify it yourself" (the runnable demos remain unchanged; only the framing word).
19. `ledge_lang/audit_store.py` — docstring "Persistent, tamper-evident SQLite audit store" softened to "hash-chained log" with an explicit threat-model paragraph naming the attacker-controls-both-store-and-anchor case as out of scope.
20. `CHANGELOG.md` — "Backwards compatibility is guaranteed within major version 1" softened; "hard safety guarantee" → "runtime fail-safe default"; "GDPR/HIPAA/regulatory compliance" → "supporting evidence for governance review; not by themselves a compliance claim"; "formal operational semantics" → "implementation-oriented semantics".

## Risky claims removed

- "Formal Specification" (titles of TYPE_SYSTEM, GRAMMAR, SEMANTICS)
- "Formal Operational Semantics" (title + references)
- "Soundness Property (Partial)" + "Theorem (Informal)" header structure
- "IMPOSSIBLE BY DESIGN" (×2 in AI_SAFETY_STUDY)
- "structurally impossible" (AI_SAFETY_STUDY conclusion)
- "impossible in Python" (RED_TEAM)
- "the first language" / "the first programming language" (SPEC, LAUNCH, vscode-ledge, DEPLOY — already fixed in prior pass)
- "compiler guarantees" (LEDGE_V1_VISION, examples/medical_triage)
- "tamper-evident" (audit_store, examples/medical_triage, examples/showcase/medical_record)
- "EU AI Act Article 12/13 compliant" → "structured against ... evidence schema" (RESPONDING_TO_EXPERTS)
- "HIPAA compliant by design" (examples/medical_triage)
- "no other language" / "= unique" / "exist in no other language" (LEDGE_V1_VISION, SCORECARD)
- "production-quality ... with a formal specification" (PUBLIC_STATEMENT)
- "formal type system specification and mechanized proofs" (TECHNICAL_REPORT future work — softened to "paper-and-pencil or mechanized")
- "with cryptographic guarantees across nodes" (TECHNICAL_REPORT)
- "Proof you can run yourself" (×4 in GUARANTEES.md → "Verify it yourself")

## Risky language intentionally KEPT, and why

**API names / identifiers — keep:**
- `audit_verify()` / `audit_verify` (function name)
- `verify()` method on `AuditTrail` (API surface)
- `unique` in `ledge_lang/stdlib.py`, `packages/ledge_collections/__init__.py`,
  `ledge_lang/lsp.py` completion list (a stdlib collection function name)
- `article12_compliant` and `eu_ai_act:article12_compliant` JSON-LD field
  names in `ledge_lang/audit_store.py` and CLI output — these are
  vocabulary terms from the EU AI Act JSON-LD context, not project claims
- Validation output "VALIDATION PASSED — EU AI Act Article 12/13 compliant"
  emitted by `ledge audit --validate-regulatory` — this validates the
  JSON-LD structure, which is what the message asserts. (RESPONDING_TO_EXPERTS
  now contextualizes it.)
- `unique` in `core_types.py` ("the unique bottom value") and `vm.py`
  ("AST objects are unique per parse") — technical English usage
- `tests/conformance.py` and `tests/test_ledge.py` references to
  `c["unique"]` — API call

**Test code — keep:**
- `tests/unit/test_typechecker.py` test names — they describe behavior
- `tests/unit/test_showcases.py` docstrings containing "LEDGE GUARANTEE:" —
  these are inline scenario descriptions; the docstrings could be
  reworded but the test bodies are correct and not user-facing
- `tests/unit/test_showcases.py::test_audit_chain_is_verified` — test name
- `tests/conformance.py` collections-unique test

**Error messages — keep:**
- `ledge_lang/typechecker.py` — "confidence was never verified" appears
  in several error suggestions. This is factually what happened
  (the checker has no record of a confidence check at this point) and
  is the precise statement of the rejection. The README and GUARANTEES
  contextualize the rule.
- `ledge_lang/typechecker.py` module docstring "formal type system, not
  a dependent type system, and not an effect system" — this is the
  disclaimer; the word "formal" appears as part of a negation.
- `ledge_lang/typechecker.py` module docstring "soundness-proved type
  system" — same negation; "this is an AST-walking analysis, not a
  soundness-proved type system".

**Demo scripts — keep (low-priority, mostly print output):**
- `demo_guarantee[1-4].py` and `demo_chain.py` — these print
  "Guarantee verified: ..." as their pass message. The README/GUARANTEES
  have been reframed, but the demos' own output strings are unchanged.
  Cost of changing them is low but they are also not HN-facing first
  impressions (they appear when someone explicitly runs the demo).
  Marked for follow-up in Phase 3+ if Phase 3 includes demo-script
  rewriting; not a Phase-2 priority.
- `experiments/safety_proof.py` — filename and headers still say
  "Ledge Safety Proof — Runnable". This is an empirical script, not a
  proof; renaming would require updating any references and is out of
  scope for the targeted-edit Phase 2 brief. Marked for follow-up.

**Internal audit artifacts — keep:**
- `audit/ai_calibration_report.md`, `audit/audit_manifest.md`,
  `audit/audit_status.json`, `audit/docs_truth_matrix.md`,
  `audit/failing_tests.csv`, `audit/PROTOCOL_REPORT_FINAL.md`,
  `audit/release_readiness.md`, `audit/score_public_release.json` —
  these are internal pre-launch artifacts, not user-facing. Many use
  "VERIFIED" as a binary label for individual tests; that usage is
  internal-style and not a marketing claim. Out of scope.

**README.md / EXECUTIVE_SUMMARY.md / CURRENT_STATUS.md / HACKER_NEWS_READINESS.md
disclaimers — keep:**
- All grep matches in these files appear inside negative statements
  ("not a formal proof system", "not tamper-proof against...", "no
  mechanized soundness theorem", "Mechanized proofs of the static
  rules" listed under "what doesn't yet exist"). These are the correct
  framing. The HACKER_NEWS_READINESS.md references "formal" because it
  describes what was removed/softened in the Phase-1-to-2 transition.

**Other harmless matches — keep:**
- `examples/ai_pipeline_demo.ledge` line 9: "Buy followers NOW cheap
  prices guaranteed!!!" — quoted spam content used as input to a
  classification demo.
- `examples/tour.ledge` line 411: "automatic, tamper-evident" comment
  on the audit-trail tour section. Marked for follow-up in Phase 3 if
  tour rewrites are in scope.
- `ledge_lang/studio/templates/studio.html` — "Guarantees" bar in the
  Studio web UI. Internal product chrome, only seen by `ledge studio`
  users. Lower priority for HN audience.
- `docs/CLAIM_REGISTRY.md` — explicit registry of "claim → test that
  verifies it", with `✓ VERIFIED` as a status flag. This is an
  internal traceability artifact and its "VERIFIED" usage is
  test-linked, not marketing. Out of scope.
- `docs/CAPABILITY_MATRIX.json` — internal capability table; "(verified)"
  appears as a test-linked flag.
- `docs/COMPARATIVE_POSITIONING.md` line 49 "the only way to get the
  value" — this is now narrowly false under the strict 1.2.0 checker
  (`when` and `unsafe_value_of` are also options). Marked for
  follow-up; the file is a comparative-positioning doc, less HN-prominent.

## Failures

(none during Phase 2.)

## Fixes applied

20 documentation patches, all preserving structural and runnable content.
No code-behavior changes in Phase 2; the only source file touched is
`ledge_lang/audit_store.py` and the change is a docstring only.

## Remaining risks

For Phase 3+:
- `experiments/safety_proof.py` filename and header strings still
  contain "proof".
- `examples/tour.ledge` tour comment mentions "tamper-evident".
- `docs/COMPARATIVE_POSITIONING.md` "the only way" is now narrowly
  inaccurate under the strict checker.
- `docs/CAPABILITY_MATRIX.json` and `docs/CLAIM_REGISTRY.md` still use
  "VERIFIED" labels — internal traceability convention, not marketing,
  but a HN reader who navigates there will see the word repeatedly.
- The Studio UI's "Guarantees" bar in `ledge_lang/studio/templates/studio.html`.
- Demo scripts' print output ("Guarantee verified: ...").

## Files inspected

(Phase 1 is search-only; nothing edited yet.)

## Commands run

- Grep across the repo for the risky-phrase regex (Phase 1).

## Failures

(none yet)

## Fixes applied

(none yet — Phase 1 is read-only.)

## Remaining risks

To be assessed after Phase 1 results are tabulated.
