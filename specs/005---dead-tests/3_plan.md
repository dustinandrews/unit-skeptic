# Implementation Plan — Dead-Test Detection

**Branch**: `sprint-5-dead-tests`
**Phase**: RED-before-GREEN enforced per task (Constitution §V).

## Approach
Add `adversary deadtests --subject <dir> [--out <file>]`. Reuse the existing
pipeline (sites → mutator → splice → shadow-run) exactly; the delta is
**per-test kill attribution** instead of whole-suite verdict. The extension
point is `runner.run_mutant`: optional `junit_path` param, parse failures
BEFORE the rmtree cleanup, return `(verdict, failing_ids)`; default behavior
(no junit) stays the current verdict-string so the `score` loop is untouched.
Stdlib only: `xml.etree` for junit, `argparse` for CLI.

## Tasks

### T001 — RED: runner per-test attribution contract
Write `tests/test_runner.py` additions:
- `test_run_mutant_with_junit_returns_failing_ids`: with `junit_path`
  pointing at an absolute scratch path, a behavior-changing mutant returns
  `("killed", [nodeid...])` and the junit file exists; a surviving mutant
  returns `("survived", [])`.
- `test_run_mutant_without_junit_keeps_string_verdict`: no junit_path →
  returns plain verdict string (backward compat, score loop untouched).
- `test_run_mutant_junit_path_absolute_required`: relative path raises or is
  normalized to absolute (no file pollution in subject cwd).
Observe RED (no junit_path param yet).

### T001 — GREEN
Extend `runner.run_mutant(subject_dir, module_rel, mutated_source, src_dir=...,
tests_rel="tests", timeout_s=..., junit_path=None)`: when junit_path set, add
`--junitxml=<abs(junit_path)>` to the pytest cmd; on `killed`, parse the junit
with `xml.etree.ElementTree`, collect failing `<testcase>` nodeids
(name="nodeid") under `<failure>`/`<error>`; return `(verdict, ids)`; parse
happens BEFORE `finally: shutil.rmtree`. Set `PYTHONDONTWRITEBYTECODE=1` in
the env (all runs). Confirm RED→GREEN.

### T002 — RED: deadtest aggregation (pure fn)
Write `tests/test_deadtests.py`:
- `test_aggregate_kills_counts_per_test`: given fake `(verdict, ids)` runs
  (killed: [t1], killed: [t1,t2], survived: [], error: [t9] — error must NOT
  attribute), aggregate → {t1: 2, t2: 1, t3: 0}.
- `test_classify_dead_by_zero_kills`: {t1:2, t2:0} → t2 `dead`, t1 `alive`.
- `test_output_json_shape`: classify → list of {test_id, kills, status} with
  dead-first stable order + top-level `"corpus": "deterministic"` + totals.
Observe RED.

### T002 — GREEN
`adversary/deadtests.py`: pure `aggregate_kills(runs)`, `classify(kill_map)`,
`build_output(kill_map)` per FR-003 (corpus-qualified, dead-first, stable
order, totals). Confirm RED→GREEN.

### T003 — RED: deadtests driver + CLI end-to-end (offline, real files)
Write `tests/test_cli.py` additions + `tests/test_deadtests_integration.py`:
- CLI: `deadtests` requires `--subject`; `--out` honored (file written with
  FR-003 shape); no `--out` → default path printed and written.
- Integration on the real guineapig subject via CLI: run completes; SC-001
  check — the 4 known weak tests are `dead`, and ≥1 strong test is `alive`;
  JSON has `"corpus": "deterministic"`.
- Reproducibility (SC-003): run twice, byte-identical JSON.
- Subject unmodified (SC-004): verify subject source bytes unchanged after a
  run (and `__pycache__` absent / build env var exercised).
Observe RED (deadtests subcommand not wired).

### T003 — GREEN
`adversary/deadtests.py` driver: `run_deadtests(subject_dir, out_path=None)`
walks sites via `sites.find_sites` + `DeterministicMutator`, calls
`runner.run_mutant(..., junit_path=abs_scratch_junit)`, aggregates only
`killed` verdict attribution, writes JSON. `cli.py`: add `deadtests`
subcommand with `--subject`, `--out` (consistent flags with `score`).
Confirm RED→GREEN; full suite green.

### T004 — Verify + docs
- Full suite: `.venv/bin/python -m pytest -q -p no:cacheprovider` (expect
  prior 77 + net-new).
- Real CLI run on guineapig: capture the dead list — MUST be exactly the 4
  weak tests (SC-001), strong tests alive; record output in this doc's review
  evidence.
- README: deadtests section (what it flags, corpus qualifier, example output).
- PRODUCT_PLAN.md + TECH_STACK.md updated (Sprint 5 section).
- Commit on `sprint-5-dead-tests`.

## Risks / notes
- junit nodeid format: pytest junit has `<testcase name=... classname=...>`;
  reconstruct nodeid as `classname::name` — verify against real output on
  guineapig during T001.
- cwd during shadow run is `subject_dir` (runner contract) — junit path MUST
  be absolute or pollutes the subject (SC-004); T001 RED pins this.
- Error/timeout mutants contribute no attribution (FR-002) — matches score
  denominator; T002 RED pins this.

## Review Result
STATUS: Draft — pending plan review.
