# Implementation Plan

**Branch**: `sprint-2-score-instrument`
**Date**: 2026-11-12
**Spec**: `specs/002---score-instrument/1_spec.md`

## Summary
Build the score instrument: a CLI that green-gates a subject, enumerates mutation
sites via AST, mutates behind a `Mutator` adapter (deterministic driver first),
runs the subject suite per mutant in a scratch dir, records mechanical verdicts,
and emits score = killed/(killed+survived) + survivors JSON.

## Technical Context
- **Language**: Python 3.12+
- **Dependencies**: stdlib (ast, subprocess, argparse, json, tempfile, decimal) +
  pytest to run the subject suite. No new runtime deps.
- **Storage**: scratch dir + results JSON on disk.
- **Project Type**: CLI library.

## Project Structure
```
adversary/
  adversary/
    __init__.py
    cli.py            # argv parsing: `adversary score --subject <dir>`
    scorer.py         # orchestrates A->C loop, computes score, writes results
    sites.py          # AST site enumeration -> Site (module, start, end, text, kind)
    mutators.py       # Mutator protocol + DeterministicMutator
    runner.py         # scratch-dir shadowing + pytest subprocess per mutant
  tests/
    test_sites.py
    test_mutators.py
    test_scorer.py
    test_runner.py
  pyproject.toml
  README.md
```

## Task List
1. Project scaffold: pyproject.toml, `adversary/` package, tests/ [T001 — P1]
2. `sites.py` — AST walker producing `Site` (module, char start/end, text, kind) for
   Compare/BoolOp/call-arg/constant nodes [T002 — P1]
3. `mutators.py` — `Mutator` Protocol (`mutate(site) -> list[str]`) + documented
   site/replacement primitives + `DeterministicMutator` (operator flips) [T003 — P1]
4. `runner.py` — green-gate + per-mutant scratch-dir shadowed pytest run → verdict
   (killed/survived/error/timeout) [T004 — P1]
5. `scorer.py` — drive loop over sites/mutants, collect verdicts, compute
   score = killed/(killed+survived), write survivors JSON [T005 — P1]
6. `cli.py` — `adversary score --subject <dir>` wiring [T006 — P1]
7. Tests across all units (TDD) incl. a known strong-suite score >= 0.8 on guineapig
   and error/timeout exclusion [T007 — P1]
8. README documenting Mutator interface + site/replacement units (SC-003) [T008 — P2]

## Reuse
- `research/v0-prototype/` already contains a working (throwaway) loop: green gate,
  AST sites, deterministic mutations, scratch-dir pytest, verdicts. Restructure its
  proven logic into the adapter-shaped package here — do not reimplement from scratch.
  Its hard-won lesson: disable pyproject `pythonpath` when shadowing (mutants must
  actually load).

## Handling FAILs
- Reviews by independent sub-agents per method.

## Review Result
STATUS: draft — pending plan-review.
