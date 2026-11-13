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

## Task List (TDD: RED test first, observe failure, then GREEN implement)

### Phase 1 — Setup
1. Scaffold: pyproject.toml, `adversary/` package, empty tests/ [T001 — P1]

### Phase 2 — sites.py (RED → GREEN)
2. Write `tests/test_sites.py` covering AST site enumeration (Compare/BoolOp/call-arg/
   constant nodes → Site with char start/end, text, kind); observe RED (no module).
   Approve test set. Then implement `sites.py` GREEN. [T002 — P1]
   *Test approval folded into independent test-review gate (AFK: no interactive sign-off).*

### Phase 3 — mutators.py (RED → GREEN)
3. Write `tests/test_mutators.py` covering `Mutator` Protocol contract + documented
   site/replacement units + `DeterministicMutator` operator flips; observe RED.
   Approve test set. Then implement `mutators.py` GREEN (Protocol + site/replacement
   docs + DeterministicMutator). [T003 — P1]

### Phase 4 — runner.py (RED → GREEN)
4. Write `tests/test_runner.py` covering green-gate + scratch-dir shadowed pytest runs
   returning killed/survived/error/timeout; observe RED. Approve test set. Then
   implement `runner.py` GREEN. [T004 — P1]

### Phase 5 — scorer.py (RED → GREEN)
5. Write `tests/test_scorer.py` covering the loop, verdict collection, score formula
   killed/(killed+survived), error+timeout exclusion, survivors JSON write, and a
   second-run identical-score reproducibility assertion (FR-007/SC-001); observe RED.
   Approve test set. Then implement `scorer.py` GREEN. [T005 — P1]

### Phase 6 — CLI + integration
6. Write `tests/test_cli.py` for `adversary score --subject <dir>`; observe RED.
   Then implement `cli.py` wiring GREEN. [T006 — P1]
7. Integration: run `adversary score --subject ../guineapig` — verify score >= 0.8,
   survivors JSON present, second run identical (SC-001/SC-002/SC-004); record the
   weak-test-cohort observation as evidence. [T007 — P1]

### Phase 7 — Docs
8. README documenting Mutator interface + site/replacement units (SC-003) + CLI usage
   [T008 — P2]

## Reuse
- `research/v0-prototype/` already contains a working (throwaway) loop: green gate,
  AST sites, deterministic mutations, scratch-dir pytest, verdicts. Restructure its
  proven logic into the adapter-shaped package here — do not reimplement from scratch.
  Its hard-won lesson: disable pyproject `pythonpath` when shadowing (mutants must
  actually load).

## Handling FAILs
- Reviews by independent sub-agents per method.

## Review Result
STATUS: PASS (round 3; TDD reorder confirmed in 4_plan-review.md).
