# Implementation Plan: Repo-Flexible Subjects

**Branch**: `sprint-7-repo-flexibility`
**Date**: 2026-11-18
**Spec**: [1_spec.md](1_spec.md)

## Summary
Add `--src-rel`, `--tests-rel`, `--python` CLI flags (defaults preserve the
current `src/`+`tests/` + `sys.executable` behavior) so real repos with
non-flat layouts and their own venvs are scoreable. Pure plumbing; mutation/
scoring/equiv semantics unchanged.

## Technical Context
- **Language**: Python 3.12 (suite); stdlib only (NFR-001) — no new deps.
- **Project Type**: library + CLI (`adversary` package).
- **Key files**: `runner.py`, `scorer.py`, `cli.py`, `deadtests.py`.
- **Design invariants**:
  - `runner.run_oracle`/`run_mutant` gain `python=None` (None → `sys.executable`);
    `tests_rel` already exists.
  - `scorer.run_loop` signature UNCHANGED; flag forwarding lives 100% in a
    caller-built `run_mutant_impl` closure passed by `cli.run_score`.
  - Error strings interpolate the effective `src_rel`.
  - `record_attrs["python"] = basename(python)` when non-default (score only).

## Project Structure (no new files)
```
adversary/adversary/runner.py    # python=None on run_oracle/run_mutant
adversary/adversary/scorer.py    # unchanged signature (closure from caller)
adversary/adversary/cli.py       # 3 flags on score/deadtests, --src-rel on equiv
adversary/adversary/deadtests.py # src_rel/tests_rel/python threaded; err msg
adversary/tests/test_runner.py   # + python threading, cmd capture
adversary/tests/test_cli.py      # + flag parsing, src-rel site listing, attrs
adversary/tests/test_deadtests.py# + tests-rel/python threading
```

## Task List
1. **T001 — runner python kwarg** [P1] Add `python=None` to
   `runner.run_oracle` and `runner.run_mutant`; set `py = python or
   sys.executable` and use `[py, -m, pytest, ...]` in both subprocess builds.
   Defaults byte-identical to today.
2. **T002 — scorer caller-ownership** [P1] Verify `run_loop` signature/lambda
   unchanged (no params added). `cli.run_score` builds a `run_mutant_impl`
   closure capturing the effective `tests_rel`/`python` and passes it to
   `run_loop`. No test needs changing if the existing injection seam holds.
3. **T003 — cli flags** [P1] Add `--src-rel`/`--tests-rel`/`--python` to the
   `score` and `deadtests` subparsers; `--src-rel` to `equiv`. Thread through
   `run_score(subject_dir, src_rel="src", tests_rel="tests", python=None)`,
   `run_equiv(subject_dir, src_rel="src")`, and
   `run_deadtests(subject_dir, src_rel="src", tests_rel="tests", python=None,
   out_path=None)`. **Green gate seam**: `cli.run_score`'s call to
   `runner.run_oracle(subject_dir, src_dir)` (cli.py:46) must pass the
   effective `tests_rel` and `python` so the oracle honors the flags. **Dispatch
   seam**: `main()`'s `args.* → func(...)` calls (cli.py:156-165) must forward
   the new argparse attributes to `run_score`/`run_equiv`/`run_deadtests`.
   `_find_py_module`/both `src_dir = join(subject, src_rel)` interpolate the
   effective src_rel. Update the hardcoded `"src"` error strings
   (cli.py:39, deadtests.py:99) to interpolate. Record
   `attrs.python = basename(python)` in `record_attrs` when non-default (score).
4. **T004 — deadtests threading** [P1] `deadtests.run_deadtests` accepts and
   threads `src_rel`/`tests_rel`/`python` into its `src_dir`, `run_mutant`
   calls, `_baseline_test_ids`, and the `_baseline_test_ids` hardcoded
   `"tests"` + `sys.executable` subprocess.
5. **T005 — tests (TDD)** [P1]
   - RED (SC-002): tmp-dir synthetic subject with tests under `src/tests/`;
     default oracle non-green; `--tests-rel src/tests` → green.
   - SC-003: monkeypatch `runner.subprocess.run` (or `_pytest`) to capture each
     `cmd` and fake rc=0; assert the pytest interpreter == given `--python` for
     oracle + first mutant.
   - SC-004: `--src-rel src` synthetic `src/<pkg>/...` → `_find_py_module`
     returns a py under src, non-empty site list, error string shows effective
     src_rel.
   - SC-005: non-default `--python` → `attrs.python == basename` in survivors.
   - Regression: existing 92 stay green, 0 failed; suite grows to 92+N
     (SC-001/SC-006).
6. **T006 — docs** [P2] `adversary/README.md` "Scoring real, non-flat repos"
   section (three flags, AIEmailSummary example anonymized); `PRODUCT_PLAN.md`
   Sprint 7 Done; `TECH_STACK.md` note.

## Review Result
STATUS: COMPLETE (plan-review PASS deleg_207e6710 2026-11-18; green-gate run_oracle seam + main() dispatch seam named in T003)
