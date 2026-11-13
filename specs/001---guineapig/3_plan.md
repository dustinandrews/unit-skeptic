# TEMPLATE: Implementation Plan

**Branch**: `sprint-1-guineapig`
**Date**: 2026-10-28
**Spec**: `specs/001---guineapig/1_spec.md`

## Summary
Build a small pure-Python pricing package (`guineapig/`) with five public functions
and a pytest suite that is both genuinely boundary-covering AND contains a deliberate
weak-test cohort — giving the later Adversary score engine a known, controllable
subject with verifiable ground truth.

## Technical Context
- **Language**: Python >= 3.12
- **Dependencies**: stdlib + pytest only (no network, no I/O in library code)
- **Storage**: none (pure library)
- **Project Type**: library

## Project Structure
```
guineapig/
  pyproject.toml
  src/guineapig/
    __init__.py
    pricing.py       # 5 public functions
  tests/
    test_pricing.py     # real, boundary-covering tests
    test_weak.py        # deliberate weak/pointless tests (FR-007 cohort)
  README.md            # contracts + protected boundaries + weak-test enumeration
```

## Task List
1. Scaffold package: pyproject.toml, src/guineapig/ (+ __init__), empty tests [T001 — P1]
2. Implement (TDD): `tier_discount(quantity) -> float` — tiered rate, thresholds 0/5/10 [T002 — P1]
3. Implement (TDD): `apply_tier_discount(unit_price, quantity) -> float` [T003 — P1]
4. Implement (TDD): `is_taxable(region, item_kind) -> bool` [T004 — P1]
5. Implement (TDD): `tax_rate(region) -> float` — region lookup + default fallback [T005 — P1]
6. Implement (TDD): `round_cents(amount) -> int` — half-penny rounding rule [T006 — P1]
7. Write boundary-covering test battery across all 5 functions (thresholds, zero,
   negative rejection) PLUS explicit invalid-input cases (negative/typo region raises
   ValueError or documented exception) per FR-003 [T007 — P1]
8. Write `test_weak.py` — deliberate tautological/pointless tests (FR-007 cohort, ≥4) [T008 — P2]
9. README: domain write-up + each function contract + protected boundaries + weak-test
   enumeration (SC-003) + how to run the suite (FR-006) [T009 — P2]

## Handling FAILs
- No review gates pre-completed; plan-review and test-review are independent sub-agents.

## Review Result
STATUS: draft — pending plan-review.
