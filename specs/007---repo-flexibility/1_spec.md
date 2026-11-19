# Feature Specification: Repo-Flexible Subjects

**Branch**: `sprint-7-repo-flexibility`
**Created**: 2026-11-18
**Status**: Draft

## Background / Motivation
The Sprint 6 GA, unit-skeptic (`adversary score`), was validated by a
real-repo pilot against `~/projects/AIEmailSummary` (2026-11-18, user-suggested
subject). The pilot's verdict: the full suite is **303 green**, but the tool
cannot score the repo because it makes three rigid assumptions that fit only
self-contained `src/`+`tests/` toy subjects:

| # | Hardcoded assumption | Where | Pilot failure |
|---|----------------------|-------|---------------|
| G1 | tests live at `<subject>/tests` | `runner.run_oracle/run_mutant(test_rel="tests")`, `scorer` | AIEmailSummary nests tests at `src/tests/` → green gate passes pytest to a nonexistent `tests` path → collection error |
| G2 | pytest runs under the tool's own `sys.executable` | `runner._pytest -> [sys.executable, -m pytest, ...]` (both oracle + mutant) | subject deps (`pydantic_core`) compiled for the subject's 3.12 venv; tool's default interpreter is 3.14 → `ModuleNotFoundError: pydantic_core._pydantic_core` at collection |
| G3 | source is the first `.py` under `<subject>/src` | `cli._find_py_module(src_rel="src")`, `run_equiv`/`deadtests` | AIEmailSummary's packages (`llm_bridge`, `email_router`, ...) live at `src/<pkg>/`, so `_find_py_module` only ever scores the *first* module (`llm_bridge/config.py`) — the suite spans many packages, and there is no way to pick the module of interest |

Goal: make the subject layout + interpreter **configurable via CLI flags** (with
the current behavior as defaults) so real, single-owner repos with non-trivial
layouts and their own venvs are scoreable. **No change to the mutation/
scoring semantics itself** (score formula, equiv JEV triage, deadtests
aggregation all stay as-built).

## Non-Goals
- No auto-detection heuristics (no trying to "guess" the layout/interpreter;
  explicit flags only, per YAGNI). The user opts in with flags.
- No support for multi-module scoring in one run (this sprint only lets the
  user *name which single module/package tree* to score). Scoring every module
  in a repo in one invocation stays out of scope.
- No change to the shadow-mutation mechanism, verdict semantics, or score
  formula.
- No moving/deleting anything in the tested subjects; subjects remain
  read-only.

## Functional Requirements

**Common plumbing (used by FR-001..003).** `runner.run_oracle` and
`runner.run_mutant` already accept `tests_rel="tests"`; extend both with a
`python=None` keyword (None → `sys.executable`) and thread both into the pytest
subprocess (`[<python>, -m, pytest, ...]`; `python` may be a path or an
executable basename, resolved as `subprocess` resolves it). Responsibility for
forwarding `tests_rel`/`python` sits **100% with the callers**: `cli.run_score`
builds and passes to `scorer.run_loop` a `run_mutant_impl` closure that
captures the effective values (compatible with the existing injection seam —
`run_loop` always uses the injected impl when provided and yields to it for
extra kwargs). `scorer.run_loop`'s signature is NOT changed and its default
lambda stays as-is (bare defaults, no flags). No `tests_rel`/`python` become
`run_loop` parameters.
**Changed CLI surface.** `cli.run_score(subject_dir, src_rel="src",
tests_rel="tests", python=None, ...)` and `cli.run_deadtests(subject_dir,
src_rel="src", tests_rel="tests", python=None, out_path=None, ...)` thread the
three values into their inner calls and the corresponding `argparse`
subparsers (`score` 134-144, `deadtests` 153-155, `equiv` 146-152 for
`--src-rel` only) gain the new `--src-rel`/`--tests-rel`/`--python` args.
`cli._find_py_module` and both `src_dir = subject/src` sites (cli.run_equiv 93,
deadtests.run_deadtests 88) interpolate the effective `src_rel`. The error
strings that currently hardcode `"src"` (cli.py:39, deadtests.py:99) interpolate
the effective `src_rel` so `--src-rel` runs report the real path.
**SC-003 test seam.** No production code records `sys.executable`; SC-003 is
proved by a unit test that monkeypatches `runner.subprocess.run` (or
`runner._pytest`) to capture the `cmd` list and return a fake rc=0 result, then
asserts the pytest subprocess's interpreter equals the supplied `--python`
path — capturing both the oracle and first-mutant invocations.

- **FR-001 (`--src-rel`)**: `score`, `equiv`, and `deadtests` accept
  `--src-rel <path>` (default `"src"`). `cli._find_py_module(subject_dir,
  src_rel)`, `run_equiv`'s `src_dir = subject/src`, and `deadtests`' inline
  `src_dir = subject/src` all use it. A relative path resolves against
  `--subject`; an absolute path is accepted as-is. This lets AIEmailSummary
  stay as-is (source at `src/email_router/` etc.) while the user points at a
  specific package via `--src-rel src/email_router`.
- **FR-002 (`--tests-rel`)**: `score` **and** `deadtests` accept
  `--tests-rel <path>` (default `"tests"`). Threaded through `runner.run_oracle`
  and `runner.run_mutant` (score + deadtests both run the suite). In
  `deadtests`, this also covers `_baseline_test_ids`, whose hardcoded
  `"tests"` + `sys.executable` arguments must accept the supplied
  `tests_rel`/`python`. Resolved against `--subject`; an absolute path is
  accepted. Lets AIEmailSummary pass `--tests-rel src/tests`.
- **FR-003 (`--python`)**: `score` and `deadtests` accept `--python
  <interpreter>` (default `sys.executable`). Every pytest subprocess in the
  run (oracle + per-mutant + baseline id enumeration) uses it, so the subject's
  compiled deps load. The user points it at the subject's own venv python.
- **FR-004 (explicit-only, no inference)**: absent a flag, every behavior is
  byte-for-byte what it was before (defaults preserve the `src/`+`tests/`
  contract; all existing tests stay green). No error is raised for
  non-canonical layout under explicit flags — the flags are the mechanism, not
  a guardrail. Mark non-default `--python` in `survivors.json`
  `record_attrs` as `python=<basename>` alongside `mutator`/`model`, for
  reproducibility (score only; deadtests has no survivors file).
- **FR-005**: docs — `adversary/README.md` gains a short "Scoring real,
  non-flat repos" section (the three flags, the AIEmailSummary example
  anonymized), and `PRODUCT_PLAN.md` Sprint 7 "Done" + `TECH_STACK.md` note.

## Acceptance Criteria
- **SC-001 (defaults unchanged)**: With no flags, `score/equiv/deadtests`
  against the existing guineapig subject produce the same verdicts as before
  (regression guard: `test_score_loop_*` and `test_cli_*` still green; the
  existing 92 tests remain green, and the suite grows to 92+N with the new
  flag unit tests).
- **SC-002 (tests-rel)**: With `--tests-rel src/tests`, a SYNTHETIC subject
  whose tests live under `src/tests/` (not root `tests/`) reaches a **green**
  oracle — where the root `tests/` default produces a non-green/collection
  failure. Proved by a committed unit test with a tmp-dir synthetic subject
  (no external repo dependency; deterministic).
- **SC-003 (python)**: With `--python <venv python>`, the oracle + first
  mutation pytest subprocess runs under that interpreter. Proved by a unit test
  that monkeypatches `runner.subprocess.run`/`runner._pytest` to capture each
  `cmd` list and return a fake rc=0 result, then asserts the pytest
  subprocess interpreter equals the given `--python` path. Deterministic.
- **SC-004 (src-rel)**: With `--src-rel src`, `_find_py_module` returns a py
  file under `src/` for a `src/<pkg>/...` synthetic subject, and `score`'s
  site enumeration emits a non-empty site list (no "no python module under
  <subject>/src" error).
- **SC-005 (record attrs)**: a non-default `--python` value is captured in
  `survivors.json` record `attrs.python` (reproducibility).
- **SC-006 (regression green)**: the existing 92 unit-skeptic tests stay
  passed, 0 failed; the full suite grows to 92+N with the new flag unit
  tests.

## Review Result
STATUS: COMPLETE (spec-review PASS deleg_a7e0dd5b; plan-review PASS
deleg_207e6710; tasks-review PASS deleg_03201680; test-review + product-review
PASS deleg_11db05f4 on landed code with the deadtests-threading gap closed;
101 tests green, defaults byte-identical)
