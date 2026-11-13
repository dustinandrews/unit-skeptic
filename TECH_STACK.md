# Tech Stack — Adversary

## Language
- Python 3.12+ (`requires-python = ">=3.12"`)

## Guinea-pig subject (sprint 1)
- `guineapig/`: pure-Python pricing package (5 functions), stdlib + pytest only.
- Test suite: 33 tests (29 boundary + 4 deliberate weak), 100% line coverage, < 2s.

## Score instrument (planned — sprint 2+)
- Deterministic operator mutator first (zero-LLM), then LLM "Andy" driver (swappable).
- Mechanical verdicts (killed/survived/error/timeout) — no model judgment of pass/fail.
- Scratch-dir mutation isolation; real repo never modified.
- Local pytest subprocess (docker sandbox deferred).

## Dependencies
- Guinea-pig: none beyond stdlib + pytest.
- Instrument: stdlib AST, subprocess, pytest (all stdlib-compatible).

## Process
- Short-sprint method (`~/projects/.SPRINT_METHOD.md`), 10 gates, specs/ artifacts.
