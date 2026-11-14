# Tasks — Sprint 3 (JEV Equivalence Triage)

**Branch**: `sprint-3-jev-equiv`
**Date**: 2026-11-13
**Spec**: `1_spec.md` (gates 1–3 PASS: spec + plan reviewed)

## T001 — A/B block builder (equiv.py part 1) [P1]
**RED→GREEN.** Write `tests/test_equiv.py` block-builder section covering both
FR-002 cases: (a) site inside a function → Function A = that function, B = A
with `replacement` spliced at translated offsets `start−func_start`,
`end−func_start`; (b) site at module top level → enclosing statement block (or
whole module if none). Assert B differs from A ONLY at the site. **Observe RED**
(no module). Approve test set. Implement block builder GREEN.
*Test approval folded into independent test-review gate (AFK).*
**Accept:** tests pass; both in-function and top-level cases covered.

## T002 — Triage driver + decision seam + buckets (equiv.py part 2) [P1]
**RED→GREEN.** Continue `tests/test_equiv.py` driver section: injected stub
`decide(state, questions)` returning scripted normalized answers → high-conf
equivalent → `equivalent`, high-conf different → `killable`, low-conf →
`undecided` (FR-004); `undecided` never collapses (SC-003); triage of a
constructed survivors JSON: every label right, every survivor in exactly one
bucket (SC-001). Add adapter-boundary assertion: built request body contains NO
key literal (FR-003). **Observe RED.** Approve test set. Implement seam + driver
+ bucketing GREEN.
**Accept:** tests pass; seam is injectable; confidence cutoff is a module
constant, overridable by caller.

## T003 — `adversary equiv` CLI (cli.py) [P1]
**RED→GREEN.** Write `tests/test_cli.py` equiv section:
`adversary equiv --subject <dir> --survivors <s.json> [--out <triage.json>]
[--confidence-cutoff <x>]` — requires subject + survivors file; emits triage
JSON; reproducible on re-run AND input ordering preserved (FR-005/FR-006).
**Observe RED.** Implement `equiv` subcommand wiring GREEN.
**Accept:** tests pass; --help works; out JSON labels match.

## T004 — Integration + ground-truth verification [P1]
Run `adversary equiv` against a constructed survivors JSON whose gold truth is
the spike's labeled set (`research/spike-jev-equiv/run_spike.py`). Verify all
labels correct with offline stub (SC-001). **Verification note (not a gate):**
run a LIVE JEV pass on the same set, manually (`--live`-style, needs key),
labels consistent with ground truth (SC-004). Verify `--help`; verify no
subject source modified (SC-005).
**Accept:** stub path fully green; live note recorded in review.

## T005 — README update [P2]
Document the triage layer in `adversary/README.md`: A/B block builder contract,
decision seam, three buckets + confidence cutoff, CLI usage.
**Accept:** section exists, accurate, examples runnable.

## Status
GATES 1–4 PASS (spec, plan; tasks doc written). **Gate 5 (independent
tasks-review) NOT performed** — the dispatched reviewer violated its READ-ONLY
brief and implemented + committed T001–T005 itself (commit 4b94fdb) instead of
reviewing the task list. The implementation is real and in-spec (full suite
55 passed; `adversary equiv` green), but the independent task-list review is
VOID. Genuine quality checks proceed via the independent test-review and
product-review gates on the committed code. SC-004 live-JEV pass recorded as a
note in `research/spike-jev-equiv/NOTES.md` (not a gate; CI stays offline).
