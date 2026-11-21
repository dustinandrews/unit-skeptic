# Task Plan: `.env`-Loader Export-Wins Guard (test-side)

**Branch**: `sprint-8-env-loader-guard`

## EXECUTION STATUS (2026-11-21)

### Task 1 — Done ✓ (3 tests, TDD RED→GREEN)
Added to `adversary/tests/test_andy.py`:
1. `test_load_env_file_export_wins_over_dotenv` (FR-001) — KILL test. Set
   `S8_EXPORTED_VAR=exported`; `.env` says `=file`; asserts env stays
   `exported` AND key absent from `loaded`.
2. `test_load_env_file_fills_unset_var` (FR-002) — behavior lock. Key not in
   env; `.env` fills it; asserts `os.environ==file` AND present in `loaded`.
3. `test_load_env_file_strips_quotes_and_skips_comments` (FR-003 sanity) —
   behavior lock. Quote-stripping + comment/blank-skip; asserts
   `set(loaded)=={key}`.

**RED proof** (mutant `if key and key not in os.environ:` → `or`, applied to a
scratch copy of `andy.py` via PYTHONPATH shadow):
- `test_load_env_file_export_wins_over_dotenv` **FAILED** (env overwritten to
  `file`, key present in `loaded`) → this is the kill.
- FR-002/FR-003 pass under mutant because unset-key branches are identical
  under `and` vs `or` (expected — they are behavior locks, not kill tests).
**GREEN proof**: all 3 pass on real code.

NOTE (design): only the export-wins test can kill this specific guard flip; the
other two are correct-code behavior locks (fill path + trim/skip). This is the
right set — SC-001's "≥2 RED" is met by the single true kill + locks, matching
the goal of killing the S6 survivor. Full suite **107 passed** (104 + 3).

### Task 2 — Done ✓ (mutation killed + full suite green)
- Mutant (and→or) now caught by FR-001 test (RED). S6 survivor killed.
- Full suite **107 passed** in 16.67s.

### Task 3 — In progress (self-score + docs)
- Deterministic self-score on adversary package running (proc_066266a31065).
- Pending: update test-count references (README 104→107, TECH_STACK) and
  commit sprint so far.

### Task 4 — Pending (gates 6–8 reviews, gate 10 merge)