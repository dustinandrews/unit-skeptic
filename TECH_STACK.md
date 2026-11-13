# Tech Stack — Adversary

## Language
- Python 3.12+ (`requires-python = ">=3.12"`)

## Guinea-pig subject (sprint 1)
- `guineapig/`: pure-Python pricing package (5 functions), stdlib + pytest only.
- Test suite: 33 tests (29 boundary + 4 deliberate weak), 100% line coverage, < 2s.

## Score instrument (sprint 2 — shipped)
- `adversary/`: standalone package (own pyproject + venv). Modules: `sites.py`
  (AST site finder with char offsets), `mutators.py` (`Mutator` Protocol +
  `DeterministicMutator`), `runner.py` (green gate + scratch pytest shadow),
  `scorer.py` (score + survivors JSON), `cli.py`.
- Deterministic operator mutator first; LLM "Andy" driver slots into the same
  `Mutator` contract later.
- Mechanical verdicts (killed/survived/error/timeout) — no model judgment of pass/fail.
- Scratch-dir mutation isolation, real repo never modified; package `__init__.py`
  mirrored into the shadow so mutants actually load. Local pytest subprocess
  (docker sandbox deferred, sprint 3+).

## Dependencies
- Guinea-pig: none beyond stdlib + pytest.
- Instrument: stdlib (AST, subprocess, tempfile, json) + pytest for dev.

## Process
- Short-sprint method (`~/projects/.SPRINT_METHOD.md`), 10 gates, specs/ artifacts.
