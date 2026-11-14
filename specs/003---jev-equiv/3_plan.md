# Implementation Plan

**Branch**: `sprint-3-jev-equiv`
**Date**: 2026-11-13
**Spec**: `specs/003---jev-equiv/1_spec.md`

## Summary
Add a survivor-triage layer to the score instrument: read a survivors JSON,
build A/B code blocks (enclosing function, original vs mutant-spliced), ask a
JEV decision model (via an injectable seam wrapping the existing triage-engine
JevClient) whether the two are behaviorally equivalent, bucket each survivor
`equivalent | killable | undecided` by confidence, and emit a triage JSON.
Proven on a constructed gold-truth survivor set (guineapig scores 1.000, so no
real survivors exist yet).

## Technical Context
- **Language**: Python 3.12+.
- **Dependencies**: stdlib only; reuse `triage-engine/src/jev/client.py`
  `JevClient` behind an injectable seam (no new shipped third-party deps).
- **Storage**: reads survivors JSON + subject source; writes triage JSON.
- **Project Type**: CLI add-on to the existing `adversary` package.

## Project Structure (additions to the existing adversary/ package)
```
adversary/
  adversary/
    equiv.py          # README: A/B block builder + triage driver (seam + bucketing)
    cli.py            # + `adversary equiv` subcommand
  tests/
    test_equiv.py
  (existing: sites.py, mutators.py, runner.py, scorer.py, cli.py, tests/)
```

## Task List (TDD: RED test first, observe failure, then GREEN implement)

### Phase 1 — equiv.py part 1: A/B block builder (RED → GREEN)
1. Write `tests/test_equiv.py` (block-builder section) covering both FR-002
   cases: a site inside a function (Function A = that function, B = A with
   replacement spliced at translated offsets `start−func_start`), and a site at
   module top level (enclosing statement block or whole module); assert B
   differs from A ONLY at the site. Observe RED (no `equiv` module). Approve
   test set. Implement the block-builder GREEN. [T001 — P1]
   *Test approval folded into independent test-review gate (AFK: no interactive
   sign-off).*

### Phase 2 — equiv.py part 2: triage driver + seam + buckets (RED → GREEN)
2. Continue `tests/test_equiv.py` (triage-driver section): with an injected
   stub `decide(state, questions)` returning scripted normalized answers,
   verify high-confidence equivalent → `equivalent`, high-confidence different
   → `killable`, low-confidence → `undecided` (FR-004); verify `undecided`
   never collapses to the other two (SC-003); verify triage of a constructed
   survivors JSON gets every label right and every survivor in exactly one
   bucket (SC-001). Observe RED. Approve test set. Implement the seam + driver
   + bucketing GREEN. [T002 — P1]

### Phase 3 — cli.py `adversary equiv` (RED → GREEN)
3. Write `tests/test_cli.py` (equiv section) for `adversary equiv --subject
   <dir> --survivors <s.json> [--out <triage.json>] [--confidence-cutoff <x>]`:
   requires a subject + survivors file; emits a triage JSON; reproducible on
   re-run (FR-005/FR-006). Observe RED. Implement the `equiv` subcommand wiring
   GREEN. [T003 — P1]
   *Reproducibility assertion folded into this task's tests (FR-006/SC-005).*

### Phase 4 — Integration + ground-truth verification
4. Run `adversary equiv` against a constructed survivors JSON whose gold truth
   is the spike's labeled set (`research/spike-jev-equiv`); verify all labels
   correct with an offline stub (SC-001) AND, as a **verification note** (not a
   pass gate), a live JEV pass on the same set returns labels consistent with
   ground truth (SC-004). Verify `--help` and that no subject source is
   modified (SC-005). [T004 — P1]

### Phase 5 — Docs
5. README section documenting the triage layer: A/B block builder contract,
   decision seam, three buckets + confidence cutoff, CLI usage. [T005 — P2]

## Reuse
- `research/spike-jev-equiv/run_spike.py` — proven A/B prompt shape and labeled
  ground-truth cases; reuse the label set for integration. Its live JEV driver
  becomes the seam's real implementation adapter.
- `triage-engine/src/jev/client.py` — JevClient reused as the real decision
  source behind the injected seam (adversary imports it at the adapter
  boundary only; tests never touch live JEV).

## Handling FAILs
- Reviews by independent sub-agents per method; spec already PASSed round 1
  with 2 warnings applied.

## Review Result
STATUS: Draft — pending plan review.
