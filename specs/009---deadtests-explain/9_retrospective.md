# Retrospective: Dead-Test Explanation (sprint 9)

**Date**: 2026-11-21
**Status**: COMPLETE

## What shipped
Mechanical one-line `reason` (+ `class`) for every test in `deadtests` output:
CASE A corpus-poverty vs CASE B regional no-op vs alive confirmation, derived
from class-region sibling-kill topology on already-collected data. No LLM, no
source/score/verdict change. 114 tests green (107 + 7).

## What went well
- **Gate-2 review caught a genuine design flaw** (HIGH-2) and the redesign
  round-2 PASS vindicated the investment: the naive "missed operators at
  lines A–B" reason was data-ungrounded because error/timeout failing-sets are
  always empty. The class-region topology reason IS grounded. Review worked.
- Gate-7 MED (CASE B not exercised end-to-end) closed cleanly.
- Integration test correctly patches the true non-pure deps (subprocess/pytest
  via 4 monkeypatches), not a misleading "network" blocker.

## What I'd tweak next time
- **RED evidence should be an pytest assertion-failure, not just Pyright
  import-error.** Cheap to add: run the new test before writing the impl and
  record the failing output. Keeps the TDD record honest for reviewers.
- **Write integration fixtures to exercise EVERY FR branch from the start.**
  The CASE B miss was because I built a fixture around the statuses I cared
  about, not the reason-selection branches. Enumerate branches first.
- Round-trip spec-review after a FAIL is worth it (round 2 found nothing new).

## Follow-ups
- LLM prose explainer for ambiguous reasons (documented follow-up, out of scope
  here). Backlog also holds the LLM/Andy corpus for dead-tests.