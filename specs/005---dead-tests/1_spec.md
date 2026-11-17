# Feature Specification: Dead-Test Detection

**Branch**: `sprint-5-dead-tests`
**Created**: 2026-11-16
**Status**: Draft

## Purpose
Phase 2 of the project: flag **test theatre** directly. A score (Sprint 2)
tells you the SUITE's catching power; dead-test detection turns the question
around — **which individual tests never kill any fault?** A test that fails on
zero behavior-changing mutants is dead weight: it inflates the green count
without catching regressions.

Guineapig provides ground truth: 4 deliberate weak tests (FR-007,
`tests/test_weak.py`) that never exercise behavior, plus 29 strong contract
tests. The deliverable identifies the weak cohort mechanically.

## Core design

1. **Kill attribution per test.** The runner currently returns a whole-suite
   pass/fail verdict. Dead-test detection needs *which tests failed* per
   mutant. Mechanical, stdlib-only: run pytest with `--junitxml=<scratch>/junit.xml`,
   parse `<testcase>` failure/error nodes via `xml.etree`, collect failing
   test ids.
2. **Dead = kills == 0.** Aggregate per test across the mutant corpus: a test's
   **kill count** = number of KILLED mutants (parseable, behavior-changing
   runs — error/timeout mutants excluded from attribution, same as the score
   denominator) where that test failed. Dead test = kill count 0.
3. **Deterministic corpus only (Sprint 5).** The deterministic mutator is the
   cleanest ground truth for "does this test catch a real fault." LLM/Andy
   integration for dead-tests is out of scope (noisy; Sprint 4's ledger handles
   it later).
4. **Reuse the existing loop and adapter.** A new `deadtests.py` walks the same
   sites → splice → shadow-run pipeline; only the verdict reporter changes (from
   whole-suite to per-test junit attribution).

## User Scenarios *(mandatory)*

### User Story 1 - Engineer finds dead tests (P1)
Given a green codebase, an engineer asks which tests never catch a fault.

**Acceptance Scenarios:**
1. **Given** a suite with some never-failing tests, **When** `adversary
   deadtests --subject <dir>` runs, **Then** it prints a summary
   (`dead tests: N of M`) and writes a machine-readable JSON with
   per-test kill counts.
2. **Given** the weak cohort in guineapig, **When** deadtests runs on it,
   **Then** all 4 weak tests are flagged dead AND every strong contract test
   has kill count ≥ 1 (i.e. alive) — the tool's output matches the known ground
   truth.
3. **Given** `--out <file>`, **When** the command runs, **Then** the JSON is
   written to `<file>`; without `--out`, a default path is used and printed.

### User Story 2 - CI-safe and reproducible (P2)
Dead-test detection must be fully offline and repeatable.

**Acceptance Scenarios:**
1. **Given** the same subject and no code changes, **When** deadtests runs
   twice, **Then** the JSON outputs are identical (reproducible corpus + verdicts).
2. **Given** the run, **Then** the subject source tree is byte-unchanged
   (mutants live only in scratch, as today).

## Functional Requirements
- **FR-001**: `adversary deadtests --subject <dir> [--out <file>]` command.
  Reads the same subject layout as `score` (`<subject>/src/...`, tests under
  `<subject>/tests`).
- **FR-002**: Per-test kill attribution: for each site, each deterministic
  candidate mutant runs the suite with `--junitxml`; failing test ids are
  recorded for mutants with verdict `killed`. Error/timeout mutants contribute
  NO attribution (their failures are parse/timeout noise, not behavior).
- **FR-003**: Output JSON: list of `{test_id, kills, status}` where
  `status = dead | alive`; plus a corpus-qualifying top-level field
  `"corpus": "deterministic"` so consumers know the label's scope — a test
  labeled `dead` here is dead-in-this-corpus (i.e. failed on zero *deterministic*
  mutants); it is NOT a claim it catches no LLM/Andy fault. Sorted with dead
  tests first (or stable deterministic order); total counts included.
- **FR-004**: Reproducible — same subject/committed code + same mutator →
  byte-identical JSON output.
- **FR-005**: Subject read-only; scratch shadow only (reuse `runner.run_mutant`
  machinery — extend, don't fork).
- **FR-006**: CLI reuses the `adversary` CLI framework, flags consistent with
  `score` where applicable (`--subject`, `--out`).

## Non-Functional / Constraints
- **NFR-001**: No new third-party runtime deps: `xml.etree` for junit parsing,
  `argparse` for CLI (both stdlib).
- **NFR-002**: Cost: identical to a deterministic `score` run (one suite run
  per candidate; guineapig ≈ 73 runs ≈ seconds). No LLM, no key, no network —
  offline by nature.
- **NFR-003**: Reuse, don't rewrite: sites/mutator/scorer loop + runner shadow
  are the base; the delta is per-test attribution.

## Success Criteria
- **SC-001**: On guineapig: the 4 deliberate weak tests
  (`test_weak_tautology_always_true`, `test_weak_constant_against_itself`,
  `test_weak_assert_none_is_none`, `test_weak_no_behavior_called`) are
  `dead` with kills == 0, AND the tool is non-trivial — at least one strong
  contract test is `alive` with kills ≥ 1. The KNOWN ground truth is only the
  weak cohort: they are dead in ANY corpus. Strong tests may read `dead` in
  the deterministic corpus when they assert constants or rejection paths the
  operator-only mutator cannot reach (e.g. `tax_rate` rate assertions, guard
  branches) — that is correct corpus-scoped behavior, NOT a false positive,
  and is exactly why FR-003 carries the `"corpus": "deterministic"` qualifier.
  See 7_test-review for the verified strong-test breakdown.
- **SC-002**: JSON is machine-readable per FR-003 shape; `--out` honored.
- **SC-003**: Two identical runs produce byte-identical JSON (diff clean).
- **SC-004**: `git status` clean on the subject after a run (only scratch
  writes; no committed mutation). Runner sets `PYTHONDONTWRITEBYTECODE=1` so
  pytest cannot drop `__pycache__/*.pyc` into the tracked subject — the
  guarantee is robust even if `.gitignore` drifts.

## Reuse contract (extends NFR-003; named per spec-review)
The per-test attribution extension point IS `runner.run_mutant`:
- `run_mutant` gains an optional `junit_path` parameter (absolute path; cwd is
  `subject_dir`, so a relative path would pollute the subject and break
  SC-004). When set, the pytest cmd gains `--junitxml=<junit_path>`.
- `run_mutant` parses the junit failures for `killed` verdicts and returns
  `(verdict, failing_ids)` — the parse MUST happen inside `run_mutant` BEFORE
  its `finally: shutil.rmtree(scratch)` (a post-hoc read of a scratch path is
  already deleted), or the junit file is written outside the scratch dir. The
  default (no junit path) keeps the current `verdict`-string behavior so the
  score loop is untouched.
- Test ids are pytest nodeids from the junit `<testcase name=... classname=...>`
  (stable across shadow runs — subject tests and paths don't move).

## Out of Scope (this sprint)
- LLM/Andy corpus for dead-tests (deterministic only; Andy floods survivors
  which are filtered by JEV triage — a dead-test pass over LTD mutants is a
  later refinement).
- Grouping dead tests by "why" (e.g. tautology vs untested-branch): Sprint 5
  flags; explaining comes later if users need it.
- Coverage-based dead-test heuristics (line coverage ≠ kill power; mutation
  attribution is the mechanism).

## Review Result
COMPLETE. Spec-review PASS (4 warnings applied); plan-review PASS; tasks-review
PASS; genuine test-review PASS + product-review PASS on landed code (88 tests
green; `adversary deadtests` verified end-to-end on guineapig). Merged to main.
