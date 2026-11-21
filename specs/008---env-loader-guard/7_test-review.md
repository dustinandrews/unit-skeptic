# Test-Review: `.env`-Loader Export-Wins Guard (sprint 8)

**Date**: 2026-11-21
**Status**: PASS (independent, deleg_8a95e856)

## Result
Independent cold review confirmed: full suite **107 passed**; export-wins test
genuinely kills the `and`→`or` mutant (verified RED via scratch mutant — both
asserts fail); the two behavior-lock tests (`fills_unset_var`,
`strips_quotes_and_skips_comments`) assert real `os.environ` mutation and
`loaded` membership, are isolated (`tmp_path` `.env` + `monkeypatch` + unique
`S8_` keys), and are NOT dead/tautological. No production source touched.

## Findings
- **MED (applied)** — SC-001 wording said "≥2 tests FAIL under mutant"; only
  the export-wins test can kill. Reworded spec to "≥1 kill test + behavior
  locks" to match the correct scope for a single mutation.
- **LOW (applied)** — plan/tasks hygiene (status stamps).
- **LOW (pre-existing, out of scope)** — `guineapig/tests/test_pricing.py` fails
  collection from repo root (`ModuleNotFoundError: guineapig.pricing`, Sprint 1
  era); unrelated to this sprint and not a regression.

## Gate
PASS — test quality meets spec intent; export-wins contract locked, S6
survivor killed.