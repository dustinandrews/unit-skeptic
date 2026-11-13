# Feature Specification: Guinea-Pig Toy Project

**Branch**: `sprint-1-guineapig`
**Created**: 2026-10-28
**Status**: Draft

## Purpose
Give the Adversary instrument a small, known, controllable subject to mutate and
score. triage-engine is too large and unstructured for the first pass; the toy is a
scratch guinea pig whose behavior we fully understand, so test-suite scores and
surviving faults can be verified against known ground truth.

Where: `~/projects/adversary/guineapig/` — a new small pure-Python package with its
own test suite (the adversarial engine/subject lives elsewhere; this sprint is ONLY
the guinea pig).

## User Scenarios *(mandatory)*

### User Story 1 - Analyst can run the toy's suite as an oracle (P1)
A developer wants a fast, deterministic, fully-understood Python project to serve as
the target that the (later) score instrument mutates. They can run its pytest suite
and get green, quickly.

**Acceptance Scenarios:**
1. **Given** the guinea-pig repo, **When** the full pytest suite runs, **Then** all
   tests pass, deterministically, in < 2 seconds, with exit code 0.
2. **Given** the guinea-pig repo, **When** the behavior of any function is inspected,
   **Then** the code is pure (no I/O, no randomness, no network, no clock) so results
   are reproducible and mutation-verdicts are stable.

### User Story 2 - Boundary behavior is explicitly tested (P2)
The toy must include behavior where off-by-one / boundary / operator errors are easy
for a mutator to introduce AND easy to reason about, so future surviving-fault
results are interpretable.

**Acceptance Scenarios:**
1. **Given** functions with numeric thresholds and branching (`<` vs `<=`, tiered
   discounts, rounding), **When** those boundaries are mutated, **Then** a good test
   suite would catch them — this is the "known-good" region to validate the score
   later.

## Requirements *(mandatory)*

### Functional Requirements
- **FR-001**: Project lives at `guineapig/` as an installable pure-Python package
  (`pyproject.toml`, `src/guineapig/`, `tests/`), Python >= 3.12.
- **FR-002**: Contains a small pricing domain with **five named pure functions**
  in `src/guineapig/`:
  1. `tier_discount(quantity) -> float` — tiered discount rate by quantity
     threshold (numeric comparisons; boundary edges: 0, tier cutoffs, e.g. 5/10).
  2. `apply_tier_discount(unit_price, quantity) -> float` — composes #1 (numeric,
     threshold-sensitive).
  3. `is_taxable(region, item_kind) -> bool` — boolean logic flag.
  4. `tax_rate(region) -> float` — region lookup with a default fallback.
  5. `round_cents(amount) -> int` — round-to-nearest-cent edge rule (boundary:
     exact half-penny).
  These span the mutation surface classes the score instrument must later exercise:
  numeric comparisons, boolean logic, and rounding edges. See README for contracts.
- **FR-003**: Every public function is pure and total (defined for all typed inputs,
  no exceptions for normal inputs); invalid input raises `ValueError` / or a documented
  domain exception per docstring.
- **FR-004**: Test suite covers each function's normal path AND boundary conditions
  (threshold edges, zero, negative rejection, empty collections).
- **FR-005**: Test suite must pass deterministically and fast (< 2s, no network, no
  I/O, no randomness).
- **FR-007**: The suite MUST include a cohort of deliberately weak/pointless tests
  — e.g. tautologies (`assert True`), tests asserting a constant against itself,
  or assertions that call no behavior — so later dead-test detection (Phase 2) has
  verifiable ground truth. The README MUST enumerate exactly which tests are weak
  and why, so the engine's dead-test flags can be scored against ground truth.
- **FR-006**: A `README.md` documents the domain, each function's contract, and how to
  run the suite.

### Non-Functional / Constraints
- **NFR-001**: No dependencies beyond stdlib + pytest (keeps the mutation runner cheap
  and portable).
- **NFR-002**: File layout matches the project template conventions where applicable.

## Success Criteria *(mandatory)*
- **SC-001**: `pytest` in `guineapig/` passes 100% deterministically, exit 0, < 2s.
- **SC-002**: The toy is reproducibly green on the sprint branch and main.
- **SC-003**: Ground-truth known (artifact checklist, verified by reviewer
  inspection): README exists; documents each public function's contract; and
  enumerates the protected boundary cases (tier thresholds, zero, negative
  rejection, half-penny rounding); and enumerates the deliberate weak-test cohort
  (FR-007).

## Out of Scope (this sprint)
- The adversarial score engine itself (later sprints).
- Any LLM wiring, docker, or mutation logic.

## Review Result
STATUS: PASS (round 3; rounds 1-2 in 2_spec-review.md — round 3 adds FR-007,
deliberate weak-test cohort for Phase-2 dead-test ground truth).
