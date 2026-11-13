# TEMPLATE: Specification Review

**Branch**: `sprint-2-score-instrument`
**Date**: 2026-11-12

## Findings (round 1)

| Principle | Status | Issue |
|----------|--------|-------|
| Serves purpose | PASS | Coherent with WHAT_AND_WHY Phase 1; score is the deliverable. |
| Deterministic-first forcing function | PASS | Single Mutator interface returning per-site replacement candidates; LLM slots in unchanged. |
| Lean / YAGNI | PASS | LLM driver, equivalence triage, dead-test detection, docker all out of scope. |
| Score formula unambiguous | FAIL (round 1) | Two denominators (`caught/total_valid_faults` vs `caught/(caught+survived)`); timeout unplaced. |
| Verdict taxonomy | PASS | Standard taxonomy; timeout placement flagged. |
| Scratch-dir shadowing | PASS | Sound; assume subject imported from local dir, not installed copy. |
| 'site' & Mutator contract defined | FAIL (round 1) | `site` primitive and replacement unit undefined; would block LlmMutator slot-in. |
| Deterministic reproducibility | PASS | Fully deterministic, no seed. |

## Anti-Patterns (round 1)
| Pattern | Severity |
|---------|----------|
| Duplicate non-equivalent score denominators | BLOCKER |
| `timeout` verdict never placed in score | WARNING |
| SC-004 leaked dead-test scope / undefined subject property | WARNING |
| Stochastic wording contradicted FR-007 | WARNING |

## Result (round 1)
STATUS: FAIL — two blockers: ambiguous score denominator, undefined `site`/contract.

---

## Round 2 (prescribed fixes applied 2026-11-12)
- **Score formula single-valued**: score = killed/(killed+survived); `error` AND
  `timeout` both excluded from denominator (FR-004, SC-002, US1-AS1 aligned).
- **Site primitive defined**: {module_source_path, start_offset, end_offset,
  original_text, kind}, character offsets, atomic AST region (FR-002).
- **Replacement unit defined**: candidate = full source text spliced at [start,end);
  one site at a time, no whole-file diffs (FR-002).
- **SC-004 reframed**: score >= 0.8 on strong suite is the criterion; weak-cohort
  is a verification note (observable evidence), not a pass gate.
- **Determinism wording single-voiced**: removed seed/temperature phrasing.

Re-review dispatched (round 3) — a fresh independent reviewer confirms closes.

STATUS: PENDING round-3 re-review.
