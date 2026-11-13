# TEMPLATE: Tasks

**Branch**: `sprint-2-score-instrument`
**Date**: 2026-11-12

## Phase 1: Setup
- [ ] T001 [P] Scaffold: pyproject.toml, `adversary/` package, empty tests/

## Phase 2: sites.py (RED → GREEN)
- [ ] T002 [P] Write `tests/test_sites.py` (AST site enumeration: Compare/BoolOp/
      call-arg/constant → Site char start/end, text, kind); observe RED; then
      implement `sites.py` GREEN. (Test approval via test-review gate.)

## Phase 3: mutators.py (RED → GREEN)
- [ ] T003 [P] Write `tests/test_mutators.py` (`Mutator` Protocol, documented site/
      replacement units, `DeterministicMutator` flips); observe RED; then implement
      `mutators.py` GREEN.

## Phase 4: runner.py (RED → GREEN)
- [ ] T004 [P] Write `tests/test_runner.py` (green-gate, scratch-dir shadowed pytest,
      killed/survived/error/timeout verdicts); observe RED; then implement `runner.py`
      GREEN.

## Phase 5: scorer.py (RED → GREEN)
- [ ] T005 [P] Write `tests/test_scorer.py` (loop, verdicts, score=killed/(killed+survived),
      error+timeout exclusion, survivors JSON, second-run reproducibility); observe RED;
      then implement `scorer.py` GREEN.

## Phase 6: CLI + integration
- [ ] T006 [P] Write `tests/test_cli.py` for `adversary score --subject <dir>`; observe
      RED; then implement `cli.py` GREEN.
- [ ] T007 [P] Integration: `adversary score --subject ../guineapig` — score >= 0.8,
      survivors JSON, second run identical; record weak-test-cohort observation.

## Phase 7: Docs
- [ ] T008 [P2] README: Mutator interface + site/replacement units (SC-003) + CLI usage.

## Review Result
STATUS: draft — pending tasks-review.
