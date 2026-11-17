# Spec Review — Dead-Test Detection

**Branch**: `sprint-5-dead-tests` · **Baseline**: 413f963
**Date**: 2026-11-16
**Reviewer**: independent sub-agent, STRICTLY read-only (tree hash verified
unchanged after dispatch)

## Findings
| Axis | Status | Note |
|------|--------|------|
| Serves project purpose | PASS | Completes Phase 2 (dead-test detection) coherently; `dead = kills == 0` across deterministic corpus is the right MVP mechanism. |
| Lean/YAGNI | PASS | Tight scope; excluding error/timeout matches S2 score denominator exactly. |
| Clarity & testability | PASS | SC-001 grounded truth verified against tree (4 weak + 29 strong exactly as claimed). |
| Reuse (NFR-003) | WARNING → APPLIED | Named the extension point: `run_mutant` optional `junit_path` + parse-before-rmtree + absolute path; default keeps verdict-string behavior. |
| rmtree deletes post-hoc junit | WARNING → APPLIED | Parse inside run_mutant before cleanup. |
| Unqualified `dead` overclaim | WARNING → APPLIED | FR-003 now carries top-level `"corpus": "deterministic"` qualifier; SC-001 frames weak→dead as corpus-independent subset. |
| `__pycache__` polluting subject (SC-004) | WARNING → APPLIED | Runner sets `PYTHONDONTWRITEBYTECODE=1`; SC-004 robust even if .gitignore drifts. |
| Cross-check Sprints 1–4 | PASS | LLM corpus + why-grouping correctly out of scope. |

## Anti-patterns
1. Reuse claimed without naming fork-point → fixed by Reuse contract section.
2. Post-hoc read of rmtree-deleted junit → fixed (parse pre-cleanup).
3. Corpus-unqualified `dead` label → fixed (FR-003 qualifier).
4. `.pyc` into tracked subject → fixed (bytecode guard).

## Review Result
STATUS: PASS (round 1; 4 warnings applied)
