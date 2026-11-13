# Plan Review

**Branch**: `sprint-2-score-instrument`
**Date**: 2026-11-12

## Round 1 — findings

### Complexity Metrics
- **Total Tasks**: 8 (OK; one concern per task, each maps to a spec FR).
- **External Dependencies**: pytest + stdlib only (OK — NFR-001).

### Over-Engineering Detected
| Component | Status | Note |
|-----------|--------|------|
| `Mutator` Protocol | Justified | FR-002 mandates adapter; predetermined 2nd consumer (LlmMutator). Minimal signature. |
| 5-module split | OK | Single responsibility; no `util`/`common`. |
| `Site.kind` | Required | DeterministicMutator selects flips by kind. |

Reuse claim sound; v0-prototype existence confirmed by parent (run.py, site_target.py,
andy.py, subject.py present).

### TDD Sequencing — FAIL (blocking)
- Tasks T001–T006 written implement-then-test; all tests dumped in final T007 = test-LAST.
- Unit tasks carried no RED-first marker.
- Constitution §V (Test-First) and the test-approval gate not encoded.
- T007 lacked the FR-007 second-run identical-score assertion.
- Fix: reorder so each unit opens with failing tests; add reproducibility assertion.

### Constitution Compliance
- Library-First: PASS. Simplicity: PASS. (Minor: TECH_STACK.md not yet in plan — status docs updated on land.)

### Round 1 verdict
STATUS: FAIL — test-LAST ordering violates Test-First §V.

---

## Round 2 (prescribed fixes applied 2026-11-12)
- **Reordered to strict TDD**: phases 2–6 each open with `Write tests/test_*.py →
  observe RED → approve test set → implement GREEN` for sites/mutators/runner/
  scorer/cli.
- **Reproducibility** folded into test_scorer.py + T007 integration (second-run
  identical score).
- **Test-approval gate**: folded into the independent test-review gate because the
  user is AFK (documented decision — interactive sign-off unavailable this sprint).
- v0-prototype reuse confirmed.

Re-review dispatched (round 3).

STATUS: PENDING round-3 re-review.
