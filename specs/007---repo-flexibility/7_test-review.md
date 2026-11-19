# Test Review — Sprint 7: Repo-Flexible Subjects

**Branch**: `sprint-7-repo-flexibility`
**Date**: 2026-11-18
**Delegation**: deleg_11db05f4 (task 1)

## Result
**STATUS: PASS** (no blockers). Static review of all 8 new tests + plumbing;
each SC is test-proven and non-vacuous. Note: reviewer ran static-only; the
full suite was verified separately (101 passed).

## Findings
| # | Sev | Area | Status |
|---|-----|------|--------|
| 1 | OK | SC-002 | Genuine RED/GREEN: default `tests_rel="tests"` misses nested subject (rc≠0); `src/tests` reaches green. Deterministic. |
| 2 | OK | SC-003 | Both capture tests monkeypatch `runner.subprocess.run`; assert `cmd[0]==/venv/bin/python` (oracle + mutant). Sound, not flaky. |
| 3 | OK | SC-004 | `_find_py_module` src_rel + default covered; error-string interpolation covered. |
| 4 | LOW | SC-005 | attrs.python proven non-vacuously; cleanup of survivors.json only on success (fragile but not a correctness bug). |
| 5 | OK | SC-001/006 | Defaults byte-identical (`python=None→sys.executable`, src/test defaults); `scorer.run_loop` signature unchanged. |
| 6 | MED→RESOLVED | deadtests threading | Implemented but untested at review time — closed post-review with a capture test (`test_run_deadtests_threads_src_rel_tests_rel_python`) asserting tests_rel/python reach run_mutant + _baseline_test_ids. Suite now 101. |
| 7 | OK | NFR-001 | stdlib only. |
| 8 | OK | Quality | No tautology; each fails if feature regresses. |

## Verified
- `scorer.py` run_loop signature unchanged (no tests_rel/python params).
- No leftover artifacts in repo.
