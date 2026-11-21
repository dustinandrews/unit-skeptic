# Implementation Plan: `.env`-Loader Export-Wins Guard (test-side)

**Branch**: `sprint-8-env-loader-guard`
**Created**: 2026-11-18
**Status**: COMPLETE

## Summary
Add 3 focused tests to `adversary/tests/test_andy.py` that exercise
`_load_env_file` directly (via `tmp_path` `.env` + `monkeypatch` env
isolation), proving the export-wins contract and killing the `and`→`or`
mutation at `andy.py:62`. Test-side only; no source changes. Closes the sole
remaining deterministic self-score survivor from Sprint 6.

## Approach
- Add tests in `tests/test_andy.py` (co-located with the existing
  `_load_env_file`-adjacent key tests).
- Each test builds a small `.env` with `tmp_path`, calls `_load_env_file(path)`
  directly with `monkeypatch`-isolated `os.environ`.
- Cover: (FR-001) export wins — already-set var NOT overwritten, absent from
  `loaded`; (FR-002) fill path — unset var IS set + present in `loaded`;
  (FR-003) a whitespace/quoted-value sanity to also lock the trimming behavior.
- TDD: write each test, verify RED under the one-line `or` mutant (scratch copy
  of `andy.py`), then GREEN on correct code.
- Verify the 3 new tests kill the mutation (see SC-001 mechanism); run full
  suite.

## Files
- `adversary/tests/test_andy.py` — add 3 tests (MODIFY, tests only).
- No production code touched (NFR-001 / non-goal honored).

## Verification
- SC-001: RED under `or` mutant, GREEN on correct.
- SC-002: full suite green (`104 + 3 = 107` expected).
- SC-003 (reported): deterministic self-score on `andy.py` has the `.env`
  survivor killed.
- SC-004: TDD RED→GREEN observed for each new test.

## Risks
- None material. The mutant provably escapes today (logic verified); the test
  targets the exact guard. No env pollution risk (monkeypatch isolation).
- Blind spot: if a key already lives in `os.environ` from the real environment
  at test time, the FR-001/FR-002 cases must use a synthetic key name to avoid
  collision — handled by using a unique token (e.g. `S8_<pytest-nodeid>`).

## Review Result
STATUS: Draft