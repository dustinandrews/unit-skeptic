# Tasks — Sprint 7: Repo-Flexible Subjects

**Branch**: `sprint-7-repo-flexibility`
**Date**: 2026-11-18
**Plan**: [3_plan.md](3_plan.md)

## Phase 1: Setup
- [ ] T001 [P] Branch + spec/plan/review docs already landed (gates 1–4). No
  setup tasks pending. (Gate 5 creates this tasks doc; implementation opens
  the real edits.)

## Phase 2: Plumbing (P1, code)
- [ ] T002 [P] runner: add `python=None` to `run_oracle` and `run_mutant`;
  `py = python or sys.executable`; use `[py, -m, pytest, …]` in both subprocess
  builds. Defaults byte-identical.
- [ ] T003 [P] scorer: confirm `run_loop` signature/lambda unchanged (no param
  additions). `cli.run_score` builds the `run_mutant_impl` closure capturing
  effective `tests_rel`/`python`.
- [ ] T004 [P] cli: `--src-rel`/`--tests-rel`/`--python` on `score` +
  `deadtests` subparsers; `--src-rel` on `equiv`. Thread through
  `run_score`/`run_equiv`/`run_deadtests`. **Green-gate seam**: `run_oracle`
  call (cli.py:46) passes effective `tests_rel`/`python`. **Dispatch seam**:
  `main()` `args.* → func(...)` (cli.py:156-165) forwards new attrs.
  `_find_py_module` + both `src_dir = join(subject, src_rel)` interpolate.
  Error strings (cli.py:39, deadtests.py:99) interpolate effective src_rel.
  `attrs.python = basename(python)` when non-default (score only).
- [ ] T005 [P] deadtests: `run_deadtests` accepts/threads `src_rel`/
  `tests_rel`/`python` into its `src_dir`, `run_mutant` calls,
  `_baseline_test_ids`, and the `_baseline_test_ids` hardcoded `"tests"` +
  `sys.executable` subprocess.

## Phase 3: Tests (TDD, P1)
- [ ] T006 [P] SC-002: tmp-dir synthetic subject with tests under `src/tests/`;
  default oracle non-green; `--tests-rel src/tests` → green. Committed unit
  test, deterministic.
- [ ] T007 [P] SC-003: monkeypatch `runner.subprocess.run`(`_pytest`) to
  capture `cmd`, fake rc=0; assert pytest interpreter == `--python` for oracle
  + first mutant. Deterministic.
- [ ] T008 [P] SC-004: `--src-rel src` synthetic `src/<pkg>/...` →
  `_find_py_module` returns py under src; non-empty site list; error string
  shows effective src_rel.
- [ ] T009 [P] SC-005: non-default `--python` → `attrs.python == basename` in
  survivors.json.
- [ ] T010 [P] Regression: existing 92 stay green, 0 failed; full suite grows
  to 92+N (SC-001/SC-006).

## Phase 4: Docs + verify (P2)
- [ ] T011 [P2] README ("Scoring real, non-flat repos", AIEmailSummary example
  anonymized; bump stale "88 tests" → 92), PRODUCT_PLAN.md Sprint 7 Done,
  TECH_STACK.md note. Full suite (92 passed) + a real `score` smoke run with
  the flags.

## Review Result
STATUS: COMPLETE (tasks-review PASS deleg_03201680 2026-11-18; count reworded to 92+N)
