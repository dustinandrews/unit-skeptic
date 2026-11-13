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
- **FR-002**: Contains a small domain with at least three pure functions spanning:
  numeric comparisons with thresholds, boolean logic, and a rounding/edge-case rule.
  Proposed domain: an order/pricing calculator (unit price, tiered quantity discount,
  tax rate lookup, total rounding).
- **FR-003**: Every public function is pure and total (defined for all typed inputs,
  no exceptions for normal inputs); invalid input raises `ValueError` / `TypeError` per
  docstring.
- **FR-004**: Test suite covers each function's normal path AND boundary conditions
  (threshold edges, zero, negative rejection, empty collections).
- **FR-005**: Test suite must pass deterministically and fast (< 2s, no network, no
  I/O, no randomness).
- **FR-006**: A `README.md` documents the domain, each function's contract, and how to
  run the suite.

### Non-Functional / Constraints
- **NFR-001**: No dependencies beyond stdlib + pytest (keeps the mutation runner cheap
  and portable).
- **NFR-002**: File layout matches the project template conventions where applicable.

## Success Criteria *(mandatory)*
- **SC-001**: `pytest` in `guineapig/` passes 100% deterministically, exit 0, < 2s.
- **SC-002**: The toy is reproducibly green on the sprint branch and main.
- **SC-003**: Ground-truth known: a reviewer can state, from the README, which
  behaviors are covered and which boundary cases the tests protect.

## Out of Scope (this sprint)
- The adversarial score engine itself (later sprints).
- Any LLM wiring, docker, or mutation logic.

## Review Result
STATUS: draft — pending spec-review.
