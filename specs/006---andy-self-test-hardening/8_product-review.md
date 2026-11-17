# Product Review — Sprint 6: Andy Self-Test Hardening

**Branch**: `sprint-6-andy-self-test-hardening`
**Date**: 2026-11-18
**Delegation**: deleg_f08811ad (task 2)

## Golden-path verification
| Claim | Verdict | Evidence |
|-------|---------|----------|
| 92 tests green | ✅ | `.venv/bin/python -m pytest` → 92 passed in 14.62s |
| Self-score 0.923 → 0.929 (13 killed / 1 survived) | ✅ | `adversary.cli score` on scratch copy → 0.929; survivor = `.env` loader `key and ... not in os.environ` `and`→`or` |
| No source change | ✅ | `git status` clean; `andy.py` untouched across Sprint 6 commits (TDD `0e4f6e9` = tests only; docs `28e0c86` = plan/stack only) |
| No secrets pushed | ✅ | Only `.env.example` tracked (template); real `.env` gitignored + untracked |
| New tests kill G1/G3/G4/G5 | ✅ | Scratch-spliced each mutant → all 4 RED on the matching test |

## Evaluations
- **SC-001 (G1/G3/G4/G5 killed test-side): SATISFIED** — all four mutants RED; none appear in survivors output.
- **SC-002 (92 green): SATISFIED** — reproducible. Score math checks: 0.929 = 13/14, baseline 0.923 = 12/13 (+1 kill). Count 92 = 88 + 4, exactly 4 new tests.
- **G2 not expected to die: CONFIRMED correct** — equivalent under
  `ensure_ascii=True` (byte-identical), documented, no test added.
- **Docs accurate** — PLAN/STACK match (92 green, 0.929/13 kills/1 survivor, `.env`-loader gap recorded for follow-up, G2 framed as "documented, not a test gap").
- No broken tests, wrong claims, or leftover artifacts (scratch + survivors cleaned).

No blockers, majors, or minors.

## Review Result
**STATUS: PASS**