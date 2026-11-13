# Feature Specification: Score Instrument (MVP)

**Branch**: `sprint-2-score-instrument`
**Created**: 2026-10-28
**Status**: Draft

## Purpose
Build the measurement core of Adversary: given a green Python codebase, inject
faults, run its test suite per fault, and produce a **score** (caught fraction) plus
the list of surviving faults — all without modifying the real repo.

First mutator driver is **deterministic** (operator flips: `==`↔`!=`, `<`↔`>=`,
`and`↔`or`, call-arg / constant tweaks). The mutator is isolated behind an **adapter
interface** so the LLM "Andy" can be swapped in via the same contract in a later
sprint — the deterministic driver is the forcing function that nails the adapter
shape now, at zero LLM cost.

Subject for verification: the `guineapig` package (sprint 1).

## User Scenarios *(mandatory)*

### User Story 1 - Engineer gets a defensible test-suite score (P1)
Given a green codebase, an engineer runs the instrument and gets one calibrated,
reproducible number: "your suite catches X% of injected faults," plus a machine-
readable list of the surviving faults.

**Acceptance Scenarios:**
1. **Given** the instrument pointed at guineapig's suite, **When** it runs,
   **Then** it emits a score in [0,1] = caught_faults / total_valid_faults and a
   JSON record of every fault + verdict.

### User Story 2 - Scoring is honest / reproducible (P1)
The score must not be inflated by broken mutants, and the run must be repeatable.

**Acceptance Scenarios:**
1. **Given** a fault that fails to compile, **When** scored, **Then** it is
   classified `error` and EXCLUDED from the denominator (not counted as caught).
2. **Given** the same subject and seed/temperature, **When** the instrument runs
   twice, **Then** the resulting score is identical (deterministic driver = exact).

## Requirements *(mandatory)*

### Functional Requirements
- **FR-001**: CLI (`adversary score --subject <dir>`) runs the full A→C loop:
  green-gate → enumerate sites → mutate → run suite → verdict → record → revert.
- **FR-002**: Mutator is behind a `Mutator` adapter interface (`mutate(site) ->
  list[str]` of candidate replacements). A `DeterministicMutator` implements it; the
  interface must be shaped so an `LlmMutator` can implement it unchanged later.
- **FR-003**: Verdicts are mechanical (no model judges pass/fail): `killed`,
  `survived`, `error` (bad mutant/compile), `timeout`.
- **FR-004**: `error`/invalid mutants excluded from the score denominator; only
  `killed` and `survived` count toward the fraction.
- **FR-005**: Surviving faults recorded as a machine-readable list (path, site
  offset, original text, replacement, verdict) — the actionable gap list and the
  Phase-2 dead-test input.
- **FR-006**: No modification of the real repo: mutants materialize in a scratch
  dir (shadowing the subject on `sys.path`), suite runs there, then discarded.
- **FR-007**: Reproducible: deterministic driver is fully deterministic (no
  randomness, no seed needed) for this sprint.

### Non-Functional / Constraints
- **NFR-001**: Only FastProducer-subject deps: stdlib + pytest. No new third-party
  runtime deps.
- **NFR-002**: Mutating a ~60-line pure module (guineapig) completes well under a
  minute (target < 30s).

## Success Criteria *(mandatory)*
- **SC-001**: Running `adversary score --subject ../guineapig` produces a score and
  a survivors JSON; the run is reproducible (identical score on second run).
- **SC-002**: Score denominator excludes `error` mutants; score = caught/(caught+survived).
- **SC-003**: A `DeterministicMutator` and the `Mutator` interface both exist; the
  interface is documented so `LlmMutator` slots in without interface changes.
- **SC-004**: Known result: on guineapig's strong suite the score is high (>= 0.8),
  and the deliberate weak-test cohort does NOT move the score (they are dead — flag
  this observation, don't fail on it).

## Out of Scope (this sprint)
- LLM Andy driver (next sprint), equivalence triage, dead-test detection, docker.

## Review Result
STATUS: draft — pending spec-review.
