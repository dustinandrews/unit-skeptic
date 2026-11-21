# Retrospective: `.env`-Loader Export-Wins Guard (sprint 8)

**Date**: 2026-11-21
**Status**: COMPLETE

## What shipped
3 tests in `test_andy.py` closing S6's last deterministic survivor: an
export-wins kill test plus fill-path and quote/comment-trim behavior locks.
No source changes. Self-score 0.929 → **1.000 (14 caught / 0 escapes)**;
107 tests green.

## What went well
- Test-first held: RED confirmed against a scratch `and`→`or` mutant before
  GREEN on real code.
- Tiny, single-focus sprint — the right scope for one mutation.
- TPD (tool's own dogfood): self-score 1.000 is the payoff and it's honest
  evidence, not just a green metrics.

## What I'd tweak next time
- **Spec success-criteria realism**: SC-001 originally demanded "≥2 tests FAIL
  under the mutant," but a single operator mutation only strikes one branch.
  The reviewer (correctly) flagged it MED; I reworded to "≥1 kill + behavior
  locks." Lesson: when a mutation touches only one branch, size SC to the
  branch, not a blanket count — it avoids a misleading criterion and a
  reviewer finding.
- **Plan-status hygiene**: `3_plan.md` stayed "Draft" through implementation.
  Mark statuses in the same commit as the task updates they describe.

## Pre-existing debt (not addressed, recorded)
- `guineapig/tests/test_pricing.py` fails collection from repo root
  (`ModuleNotFoundError: guineapig.pricing`) — Sprint 1-era, unrelated. The
  "107 tests" claim is scoped to the `adversary` package and is accurate.

## Follow-ups
- None for this sprint. Backlog still holds: dead-test explanation (design
  decided), LLM/Andy corpus for dead-tests.