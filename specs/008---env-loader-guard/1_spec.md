# Feature Specification: `.env`-Loader Export-Wins Guard (test-side)

**Branch**: `sprint-8-env-loader-guard`
**Created**: 2026-11-18
**Status**: Draft

## Background / Motivation
Sprint-6 Andy dogfooding surfaced a deterministic self-score survivor in
`adversary/andy.py` `_load_env_file`: the line

```python
if key and key not in os.environ:
```

flipped to `or` (i.e. `if key or key not in os.environ:`) escapes the suite.
Under the current tests, that mutant survives. The contract it guards matters:
`.env` must fill variables that are NOT already set, so a real exported
`OPENROUTER_API_KEY` (set in the shell / CI) wins over a `.env` file. Under the
`or` mutant, a `.env` value silently **overwrites** an exported var — a real
security/correctness bug (wrong key used, `.env` gains precedence over the
environment).

Empirically verified (logic-level):
- `and` (correct): env `DATAGOG=exported-wins` + `.env` `DATAGOG=file-value`
  → stays `exported-wins`, loaded={}.
- `or` (mutant): env `DATAGOG=exported-wins` + `.env` `DATAGOG=file-value`
  → becomes `file-value` (file overwrites export). Loaded={DATAGOG}.

ROOT CAUSE (test gap): no test ever exercises `_load_env_file`'s "skip if
already in os.environ" branch. `test_real_complete_requires_key` pops the key
and checks an error path; nothing asserts export-wins behavior.

Goal: a test (or tests) that genuinely fail when the `and`→`or` mutant is
present, i.e. kill the escape, closing the one remaining deterministic
self-score survivor from S6.

## Non-goals (YAGNI)
- NOT changing `andy.py` source — it is correct; the test must prove it.
- NOT a source fix / logic rewrite of `_load_env_file`.
- NO new third-party deps (python-dotenv is forbidden; NFR-001 stdlib only).
- NOT touching the module-level `_load_env_file(_ENV_PATH)` import-time load,
  live-Andy behavior, or the key-hygiene / JEV / transport seams.

## User Scenarios

### User Story 1 - Export wins over `.env` (P1)
An engineer leaks a shell/CI export of `OPENROUTER_API_KEY` (or any var) and a
repo-local `.env` sets the same key. The loaded value MUST be the exported one;
the `.env` must not clobber it. A regression that lets `.env` win must be
caught.

**Acceptance Scenarios:**
1. **Given** `os.environ` already contains `KEY=exported`, **When**
   `_load_env_file` reads a `.env` containing `KEY=file`, **Then** `os.environ`
   still holds `exported` (the `.env` line is skipped) and the file value is NOT
   in the returned `loaded` dict.
2. **Given** `KEY` is NOT in `os.environ`, **When** `_load_env_file` reads a
   `.env` containing `KEY=file`, **Then** `os.environ["KEY"] == "file"` and
   `KEY` IS in the returned `loaded` dict (the fill path still works).
3. **Given** a mutant flipping the guard `and`→`or`, **When** the suite runs,
   **Then** ≥1 test fails (scenario 1 turns red).

## Requirements

### Functional Requirements
- **FR-001**: `_load_env_file` MUST have a test asserting an already-set env var
  is NOT overwritten by a `.env` value and does NOT appear in the returned
  `loaded` map.
- **FR-002**: `_load_env_file` MUST have a test asserting a NOT-yet-set env var
  IS filled with the `.env` value and DOES appear in `loaded`.
- **FR-003**: The new tests MUST be arranged so they run `_load_env_file`
  directly with a temp `.env` and no persistent side effects: use pytest's
  `tmp_path` fixture to write the `.env` file, and `monkeypatch` (setitem /
  setenv / delitem on `os.environ`, or a saved+restored dict) to isolate env
  state so the tests don't pollute others or the import-time load.

### NFRs
- **NFR-001** (`adversary` package): stdlib-only imports preserved; temp `.env`
  via `tmp_path` fixture, no third-party dep.
- **NFR-002**: All existing tests still green; test count increases by ≥2.

## Success Criteria
- **SC-001**: ≥1 genuine kill test (the export-wins test) that FAILS (RED) when
  the `and`→`or` mutant is present — verified by applying the one-line `or`
  edit to a scratch copy of `andy.py` and running the suite against it (or via
  the tool's own mutation runner) — PLUS behavior-lock tests covering the
  fill path and quote/comment trim (FR-002/FR-003), which pass under BOTH
  variants (they lock correct behavior, not the guard flip). RED-to-GREEN is
  proved at implementation time. Only the export-wins branch is mutated by
  `and`→`or`, so exactly one kill test is the correct scope.
- **SC-002**: Full suite green on `main` baseline + new tests.
- **SC-003** (reported, not gating): re-run deterministic self-score on
  `andy.py`; expect the `.env` survivor no longer present. This is the payoff —
  reported, since re-running the full score is heavier.
- **SC-004**: TDD observed — each new test written RED (fails for the expected
  reason under the mutant), then GREEN.

## Review Result
STATUS: COMPLETE (spec-review PASS deleg_29f2b261 2026-11-21; 3 Minor
findings — FR-003 fixture split, SC-001 RED mechanism, SC-003 wording — all
applied; no blockers, no scope creep)