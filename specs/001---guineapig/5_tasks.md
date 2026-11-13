# TEMPLATE: Tasks

**Branch**: `sprint-1-guineapig`
**Date**: 2026-11-12

## Phase 1: Setup
- [x] T001 [P] Scaffold package: pyproject.toml, src/guineapig/pricing.py + __init__,
      tests/ dirs

## Phase 2: Foundational (TDD — RED test first, then GREEN)
- [ ] T002 [P] RED test for `tier_discount` (thresholds 0/5/10, negative rejection) then
      implement GREEN
- [ ] T003 [P] RED test for `apply_tier_discount` (composes #1) then implement GREEN
- [ ] T004 [P] RED test for `is_taxable` (boolean flag) then implement GREEN
- [ ] T005 [P] RED test for `tax_rate` (region lookup + default fallback, invalid region)
      then implement GREEN
- [ ] T006 [P] RED test for `round_cents` (half-penny edge) then implement GREEN

## Phase 3: Boundary battery + weak cohort
- [ ] T007 [P] Comprehensive boundary test battery across all 5 functions (thresholds,
      zero, negative rejection, invalid-input per FR-003)
- [ ] T008 [P2] `test_weak.py` — deliberate weak/pointless tests (FR-007 cohort, ≥4)

## Phase 4: Docs
- [ ] T009 [P2] README: domain write-up, each function contract, protected boundaries,
      weak-test enumeration (SC-003), how to run suite (FR-006)

## Review Result
STATUS: draft — pending tasks-review.
