# TEMPLATE: Specification Review

**Branch**: `sprint-1-guineapig`
**Date**: 2026-11-12

## Findings

| Principle | Status | Issue | Fix |
|----------|--------|-------|-----|
| Serves purpose | PASS | "triage-engine is too large and unstructured for the first pass; the toy is a scratch guinea pig whose behavior we fully understand" directly matches the mission (score suites by "the fraction of injected faults the tests catch"). A 3-function pricing domain is small enough to fully understand and rich enough to mutate. | — |
| Lean / YAGNI | PASS | Out of Scope correctly excludes "The adversarial score engine itself," "Any LLM wiring, docker, or mutation logic." Nothing speculative; the README (FR-006) is justified as it feeds SC-003. | — |
| Clarity & testability | PASS | FR-001–FR-005 and acceptance scenarios are concrete and machine-verifiable ("all tests pass, deterministically, in < 2 seconds, with exit code 0"). | Remove/rewrite SC-003 — not verifiable (see below). |
| Correctness of claims | PASS | "Every public function is pure and total," "no dependencies beyond stdlib + pytest," "Python >= 3.12," `src/guineapig/` layout, "< 2s": internally consistent and reasonable. A tiny pure stdlib package pass in <<2s is trivially true. | — |

## Anti-Patterns

| Pattern | Severity | Fix |
|---------|----------|-----|
| SC-003 is an unverifiable vibes criterion — "a reviewer can state, from the README, which behaviors are covered" is subjective and not machine-checkable, unlike every other acceptance criterion. | WARNING | Recast as an artifact checklist: "README exists, documents each public function's contract, and enumerates the protected boundary cases (thresholds, zero, negative rejection), verified by reviewer inspection." |
| FR-002 lists only "at least three" functions with a "Proposed domain" that is optional — a lo-fi guardrail, not a blocker. Returns zero-function-suites ("at least three" is satisfiable but thin). | WARNING | Fix the minimum count upward (e.g. ≥4) or name the concrete function list so the score instrument has a defined, known-good mutation surface from day one. |

## Review Result
STATUS: PASS — round 1. Two warnings applied as prescribed fixes in round 2 (below).

---

## Round 2 (prescribed fixes applied 2026-11-12)

- **SC-003 recast** in `1_spec.md` to a verifiable artifact checklist (README must exist,
  document each public function's contract, and enumerate protected boundary cases).
- **FR-002 fixed**: function list made concrete — a pricing domain with ≥5 named public
  functions spanning numeric comparisons (tiered discount thresholds), boolean logic
  (tax applicability / free-shipping flag), and rounding (round-cents edge rule).

STATUS: PASS
