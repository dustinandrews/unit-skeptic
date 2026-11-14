# Specification Review — JEV Equivalence Triage

**Branch**: `sprint-3-jev-equiv`
**Date**: 2026-11-13
**Reviewer**: independent subagent (read-only; fixed live-code checks)

## Findings
| Principle | Status | Evidence |
|-----------|--------|----------|
| Serves project purpose | PASS | Triage is the coherent layer after Sprint 2's survivors list; must exist before Andy floods with noisier/equivalent mutants. JEV choice grounded in spike (12/12). |
| Lean / YAGNI | PASS | `construct survivors + prove mechanics` framing sound given guineapig scores 1.000 (0 survivors). Triage mechanics + accuracy only; escalation engine correctly out of scope. |
| Clarity & testability | PASS | Decision seam (FR-003), buckets (FR-004), confidence-cutoff all machine-verifiable. |
| Schema continuity | PASS | Survivors schema {path,start,end,orig,replacement,verdict} matches what Sprint 2's scorer actually emits (verified against scorer.py). |
| Reuse soundness | PASS | Reusing triage-engine/src/jev/client.py via an injectable seam is non-duplicative (adversary stays independent; no client re-implementation). |
| Cross-check | PASS | Builds on Sprint 2; LLM Andy correctly left to Sprint 4. |

## Anti-Patterns (warnings — both applied to the spec)
| # | Pattern | Fix applied |
|---|---------|-------------|
| 1 | Enclosing-extraction undefined for sites at module top level (sites.py emits bare Compare/BoolOp/Const at module scope) | FR-002/SC-002 now define both cases: in-function → that function; top-level → enclosing statement block (or whole module). |
| 2 | Function-B splice-offset translation unstated (`start − func_start`) | FR-002 now defines translating offsets to the function-local span. |

## Review Result
STATUS: PASS (2 warnings applied to spec in round 1)
