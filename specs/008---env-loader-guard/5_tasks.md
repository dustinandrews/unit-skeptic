# Task Plan: `.env`-Loader Export-Wins Guard (test-side)

**Branch**: `sprint-8-env-loader-guard`

## Task 1 — Write 3 `_load_env_file` tests (TDD RED)
In `adversary/tests/test_andy.py`, add:
1. `test_load_env_file_export_wins_over_dotenv` (FR-001): pre-set
   `S8_EXPORTED_VAR=exported` in env via monkeypatch; write `.env` with
   `S8_EXPORTED_VAR=file`; call `_load_env_file`; assert env still `exported`
   AND key absent from returned `loaded`.
2. `test_load_env_file_fills_unset_var` (FR-002): key not in env; `.env` sets
   `S8_FILL_VAR=file`; call; assert `os.environ[S8_FILL_VAR]=="file"` AND key
   present in `loaded`.
3. `test_load_env_file_strips_value_quotes` (FR-003 sanity): `.env` line
   `S8_Q_VAR="quoted"` fills with `quoted` (quote-stripped); also lock that
   comments/blank lines are ignored.

Use unique `S8_` key names + `tmp_path` `.env` + `monkeypatch` isolation.
Write RED first (mutate `and`→`or` in a scratch copy), verify the tests fail,
then confirm GREEN on correct code.

**Output**: 3 tests; RED→GREEN verified (state evidence in 5_tasks.md).

## Task 2 — Verify mutation killed + full suite green
- Apply the one-line `or` mutant to a scratch `andy.py`; confirm the 3 new
  tests FAIL (at least FR-001/FR-002), proving the S6 survivor is killed.
- Run full suite: expect **107 passed** (104 + 3).
- Record evidence (test names, counts, RED targets) in 5_tasks.md.

## Task 3 — Report self-score + docs
- Re-run (or report) deterministic self-score on `andy.py` — the `.env`
  survivor should no longer be present (reported, non-gating per SC-003).
- Update test-count references (README Dev line, TECH_STACK) to 107.
- Commit the sprint onto the branch.

## Task 4 — Reviews (gates 6–8)
- Gate 6 tasks-review + gate 7 test-review + gate 8 product-review via cold
  reviewers; fix LOW/MED traps; record verdicts.
- Gate 9 retrospective; gate 10 merge to main + docs.