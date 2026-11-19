# Plan Review — Sprint 7: Repo-Flexible Subjects

**Branch**: `sprint-7-repo-flexibility`
**Date**: 2026-11-18
**Delegation**: deleg_207e6710

## Result
**STATUS: PASS** (92 passed on main; plan fully grounded in real code).

## Findings acted on
| # | Sev | Issue | Action in plan |
|---|-----|-------|----------------|
| 1 | LOW | Green-gate threading not enumerated — `cli.run_score` calls `run_oracle(subject_dir, src_dir)` at cli.py:46 without tests_rel/python | T003 now names the green-gate run_oracle call as a site needing the effective flags |
| 2 | LOW | `main()` argparse→func dispatch (cli.py:156-165) not named as a forwarding seam | T003 now names the dispatch seam |

## Consistent / confirmed (INFO)
- Only three pytest subprocess-build sites exist package-wide (runner.py:66, runner.py:133, deadtests.py:149-150); T001 + T004 cover them all — G2 fully covered, `_pytest` needs no change.
- `scorer.run_loop` signature/lambda unchanged; default lambda fires only `if run_mutant_impl is None`, so the caller closure never collides.
- Added kwargs break no existing callers (all keyword-based); `deadtests.run_deadtests` driver not directly unit-tested, so its signature change is safe.
- T005 scenarios deterministic (tmp_path + monkeypatch; no flaky timing, no real repo).
- Docs at correct paths (README in `adversary/`, PRODUCT_PLAN + TECH_STACK at repo root).
- YAGNI clean: no run_loop param change, no auto-detect, no multi-module.
