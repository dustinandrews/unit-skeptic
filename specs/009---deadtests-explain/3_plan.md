# Implementation Plan: Dead-Test Explanation (mechanical)

**Branch**: `sprint-9-deadtests-explain`
**Created**: 2026-11-21
**Status**: COMPLETE

## Summary
Extend `adversary deadtests` so every test in the JSON carries a mechanical
`reason` (CASE A corpus-poverty / CASE B regional no-op / alive confirmation)
derived from already-collected failing-ids + nodeid class-region sibling-kill
topology. Pure fns in `deadtests.py`; no source/semantic change to scoring or
`runner.run_mutant`; no LLM.

## Approach
1. **Pure fns in `deadtests.py`:**
   - `_class_region(test_id)`: nodeid prefix before final `::`; if none, whole
     nodeid. (L1 fallback.)
   - `class_sibling_kills(kill_map)`: dict class → sum of kills of ALL tests in
     that class, so a test's siblings = class_total - own_kills.
   - `reason(test_id, kills, class_totals)`: CASE A if kills==0 and
     class_siblings==0; CASE B if kills==0 and class_siblings>0; else
     `"caught {kills} mutants"`. Pinned templates from spec FR-003.
2. **Add `class` + `reason` to `classify`/`build_output`** per test entry.
3. **Thread wiring** (FR-004): data already flows through `aggregate_kills` →
   `classify` → `build_output`; only the reason/class computation is new. No
   change to `runner.run_mutant`'s return tuple.
4. **CLI**: print line gains `reason` count summary? Keep minimal — the JSON is
   the contract; CLI unchanged except it already prints "bad tests". Optional:
   leave CLI as-is (YAGNI).

## Files
- `adversary/adversary/deadtests.py` — add `_class_region`, `class_sibling_kills`,
  `reason`; extend `classify`/`build_output`, `Frequency` no.
- `adversary/tests/test_deadtests.py` — new pure-fn + integration tests.

## Verification
- SC-001: 3 pure-fn tests (CASE A, CASE B, alive).
- SC-002: integration test monkeypatching `runner.run_mutant`,
  `sites.find_sites`, `DeterministicMutator`, `_baseline_test_ids`
  (subprocess/pytest — not network).
- SC-003: full suite green; synthetic two-class subject shows CASE A, CASE B,
  alive confirmation.
- SC-004: TDD RED→GREEN per new test.

## Review Result
STATUS: COMPLETE