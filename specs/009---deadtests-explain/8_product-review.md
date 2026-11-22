# Product-Review: Dead-Test Explanation (sprint 9)

**Date**: 2026-11-21
**Status**: PASS (independent, deleg_4593d564)

## Outcome check vs spec intent
`adversary deadtests` now explains WHY a test is bad, mechanically: every JSON
entry carries `class` + `reason` (CASE A corpus poverty / CASE B regional
no-op-redundancy / alive confirmation), derived from already-collected
failing-ids and nodeid class-region sibling-kill topology. This distinguishes
corpus-poverty artifacts from genuine test theatre — the point of the feature.

## Verified
- Integration JSON shows all three: CASE A, CASE B (after MED fix), alive conf.
- Exact templates each byte-match spec FR-003; sibling count correctly excludes
  the dead test itself.
- No semantic change to score, verdicts, or `runner.run_mutant` contract;
  dead-first stable ordering and JSON shape preserved.
- stdlib-only (NFR-001), no LLM, deterministic (NFR-003).

## Gate
PASS — feature delivers the decided mechanical-explanation design;
gate-2 FAIL/redesign and gate-7 MED both resolved. LLM prose explainer remains
documented as a separate follow-up.