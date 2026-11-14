# Feature Specification: JEV Equivalence Triage for Survivors

**Branch**: `sprint-3-jev-equiv`
**Created**: 2026-11-12
**Status**: Draft

## Purpose
Give the Adversary instrument a cheap, mechanical first-pass triage for
surviving faults. A fault that survives the test suite is either a **real
blind spot** (the tests don't catch a genuine behavior change) or an
**equivalent mutant** (syntactically different, behaviorally identical — a
false positive that inflates nothing and dilutes the gap list). Equivalence
triage labels each survivor `equivalent | killable | undecided` using the JEV
decision model (`typesafe/jev-1.14`), presented as two clean A/B code blocks
(no diff). De-risked by an earlier spike (`research/spike-jev-equiv/`: JEV
classified 12/12 labeled cases exactly, including a half-penny edge).

## Why JEV / why now
- Equivalence is a per-survivor **decision** (equivalent? / different?) — exactly
  JEV's shape. Cheap and fast enough to stream a survivors list.
- Sprint 2 ships the survivors list and deterministic mutator; this sprint adds
  the triage layer. **Andy (Sprint 4) will flood survivors with noisier, more
  equivalent mutants** — LLMorpheus data showed +~26pts non-compiling and more
  equivalents than rule-based — so the triage must exist before Andy lands.

## Key decision: subject for verification
guineapig's strong suite scores **1.000 (0 survived)** — there are no real
survivors to triage yet. So this sprint proves the **mechanics and accuracy**
of the triage pipeline against a constructed survivor set with known ground
truth; operational value (triaging a live survivor flood) is realized in
Sprint 4+.

## User Scenarios *(mandatory)*

### User Story 1 - Analyst triages a survivor list (P1)
Given a survivors JSON (from Sprint 2's `adversary score`), an engineer runs a
triage pass that labels every surviving fault as behaviorally-equivalent,
likely-killable, or undecided.

**Acceptance Scenarios:**
1. **Given** a survivors JSON with known equivalent and known killable faults,
   **When** the triage pass runs, **Then** each survivor gets a label +
   confidence, written to a triage JSON, reproducibly (same input -> same labels).
2. **Given** a survivor whose site sits inside a real function, **When** the
   A/B blocks are built, **Then** Function A is the enclosing function with the
   original text and Function B is the same function with the replacement
   spliced at the site — verified against guineapig source.

### User Story 2 - Confidence decides escalation (P2)
Low-confidence triage must not be silently trusted as a final say.

**Acceptance Scenarios:**
1. **Given** a survivor where JEV is unsure, **When** triaged, **Then** it is
   bucketed `undecided` (never forced to equivalent or killable), so a heavier
   partner model / human can escalate only those.

## Requirements *(mandatory)*

### Functional Requirements
- **FR-001**: `equiv` module consumes a survivors JSON (schema: each record has
  `path`, `start`, `end`, `orig`, `replacement`, `verdict`) and emits a triage
  JSON adding, per survivor, `"label"` in {`equivalent`, `killable`,
  `undecided`} and `"confidence"` in [0,1].
- **FR-002**: **A/B block builder**: given module source + a site (start/end,
  orig, replacement), extract the **enclosing function/statement** as Function A
  (original) and Function B (A with `replacement` spliced at [start,end)).
  Pure, tested against real guineapig source.
- **FR-003**: **Decision seam**: triage calls a single injectable `decide(state,
  questions) -> normalized answers` callable. The real implementation wraps the
  existing `triage-engine/src/jev/client.py` `JevClient` (key read indirectly
  from env/file, never a literal; never a key in prompts). Tests inject an
  offline stub — no live provider in CI.
- **FR-004**: Confidence bucketing: high-confidence `equivalent` -> equivalent;
  high-confidence `different` -> killable; low confidence -> undecided.
  Thresholds are module constants (single source of truth), configurable via
  CLI flag.
- **FR-005**: CLI: `adversary equiv --subject <dir> --survivors <s.json>
  [--out <triage.json>] [--confidence-cutoff <x>]`. Requires a subject dir (to
  build A/B blocks from real source) plus a survivors file.
- **FR-006**: Reproducible: given the same survivors JSON + same decision
  results, output is deterministic (no randomness in the pipeline; ordering
  preserved from input).
- **FR-007**: No modification of the real repo (read-only on subject source).

### Non-Functional / Constraints
- **NFR-001**: No new shipped third-party runtime deps — stdlib + reuse of the
  existing triage-engine JevClient seam (no re-implementation; thin adapter).
  Live JEV network access lives behind the injected seam.
- **NFR-002**: Triage of a typical survivors JSON (tens of records) completes
  fast; JEV calls are the only external cost and are bounded per record.

## Success Criteria *(mandatory)*
- **SC-001**: With an offline stub decision source, a constructed survivors JSON
  containing known equivalent + known killable survivors triages with every
  label correct and every survivor assigned to exactly one of the three buckets.
- **SC-002**: A/B block builder is verified: embedding real guineapig source +
  a known site yields Function B that differs from Function A ONLY at the site
  (splice-correct), asserted in tests.
- **SC-003**: `undecided` never maps to equivalent or killable (FR-004 low-
  confidence path covered by a test).
- **SC-004**: Live JEV on a labeled verification set (reusing the spike's case
  data) returns labels consistent with ground truth — a **verification note**,
  not a pass gate (the spike already established 12/12; CI stays offline).
- **SC-005**: `adversary equiv --help` and a live run on
  `research/spike-jev-equiv` fixtures produce the triage JSON without modifying
  any subject source.

## Out of Scope (this sprint)
- LLM "Andy" driver (Sprint 4).
- Dead-test detection (Sprint 5).
- Escalation engine for `undecided` (a heavier partner model / human review) —
  the bucket exists, the consumer does not yet.
- Large real-world subjects (scope triage to small/medium pure functions,
  matching what Andy mutates).

## Review Result
STATUS: Draft — pending spec review.
