# Task Plan: Dead-Test Explanation (mechanical)

**Branch**: `sprint-9-deadtests-explain`

## EXECUTION STATUS (2026-11-21)

### Task 1 — Done ✓ (pure fns, TDD)
Added to `deadtests.py`: `_class_region` (prefix before final `::`, fallback
whole nodeid), `class_kill_totals`, `reason` (CASE A / CASE B / alive), and
extended `classify` to emit `class` + `reason`. Wrote 6 new pure tests first
(RED via Pyright: fns absent) then GREEN. All 10 deadtests tests pass.

### Task 2 — Done ✓ (SC-002 integration)
`test_run_deadtests_emits_mechanical_reasons`: patches `runner.run_mutant`,
`sites.find_sites`, `DeterministicMutator.mutate`, `_baseline_test_ids`
(real non-pure deps = subprocess/pytest). Two-class synthetic subject verifies
CASE A (TestLone::test_c corpus poverty), CASE B (TestStrong::test_weak,
dead in a class whose siblings killed), alive confirmation (TestStrong a/b),
and that every entry has `class` + `reason`.

### Review finding (deleg_4593d564, MED) — applied
Gate-7 noted CASE B was only covered at unit level. Extended the integration
fixture with `TestStrong::test_weak` (0 kills, class siblings 3) and asserted
its CASE B reason in the JSON, so SC-003 (CASE A + CASE B + alive end-to-end)
is now fully met. 114 green.

### Task 3 — Done ✓ (full suite)
- **114 passed** (107 + 7 new: 6 pure + 1 integration).
- Reason determinism: pure fns, byte-identical templates (NFR-003).

### Task 4 — Pending (gates 6–10)
Gates 6–8 cold reviews (tasks/test/product); fix findings; record. Gate 9
retrospective; gate 10 merge to main + docs.