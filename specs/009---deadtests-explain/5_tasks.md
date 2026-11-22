# Task Plan: Dead-Test Explanation (mechanical)

**Branch**: `sprint-9-deadtests-explain`

## Task 1 — Pure fns + classify/build_output extension (TDD)
In `deadtests.py` add:
- `_class_region(test_id)` — prefix before final `::`; fallback whole nodeid.
- `class_sibling_kills(kill_map)` — class → (sum of kills in class minus own) OR
  return total + derive sibling in reason. Keep it simple: return per-class
  totals; reason computes `sibling = class_total - own_kills`.
- `reason(test_id, kills, class_totals)` — per spec FR-003 pinned templates.
Extend `classify` to emit `class` + `reason` per entry; `build_output` wires
sibling-kill totals. All pure; write RED tests first for each of:
  CASE A dead, CASE B dead, alive, empty-`::` fallback.

## Task 2 — Integration test (SC-002)
Wrote RED test that `run_deadtests` JSON carries `reason` + `class`, with
`runner.run_mutant`, `sites.find_sites`, `DeterministicMutator`,
`deadtests._baseline_test_ids` monkeypatched (real non-pure deps are
subprocess/pytest). Synthetic two-class subject ⇒ CASE A / CASE B / alive.

## Task 3 — Full suite + evidence
- Full suite green (107 + new). Record RED→GREEN evidence in this file.
- Confirm `reason` string determinism (same runs → same strings).

## Task 4 — Reviews + merge (gates 6–10)
- Gates 6–8 cold reviews (tasks/test/product); fix findings; record.
- Gate 9 retrospective; gate 10 merge to main + docs (README/TECH_STACK counts).