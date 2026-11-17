# Tasks Review — Sprint 6: Andy Self-Test Hardening

**Branch**: `sprint-6-andy-self-test-hardening`
**Date**: 2026-11-18
**Delegation**: deleg_730773a7

## Findings
| # | Criterion | Verdict | Evidence |
|---|-----------|---------|----------|
| 1 | Task coverage vs plan/spec | PASS | All 7 tasks map 1:1 to plan tasks; no orphans/missing items. T002–T005 match plan T001–T004 test names; T006 ↔ verification/SC-001; T007 ↔ docs. |
| 2 | Concrete acceptance criteria / TDD | PASS | Each test task names its mutant and baseline (RED on GX / GREEN on baseline); T003 correctly GREEN-only (closes FR-002 assertion gap, no KILL row). SC-004 makes RED→GREEN ordering explicit. |
| 3 | Setup claim | PASS | Branch + spec/plan/review docs confirmed landed; nothing pending in setup phase. |
| 4 | T006 excludes G2 | PASS | Explicitly documents G2 as equivalent survivor; not in kill set. Correct under `ensure_ascii=True` (andy.py:168). |
| 5 | Count 92 not 93 | PASS | Tasks file says 88 → 92 (88 + 4 committed tests). Stale "92–93"/"+5" residue in spec/plan noted; corrected in this same revision. |
| 6 | Ordering | PASS | Tests → verification → docs; dependency-correct. |

Code seams re-verified by reviewer against actual source (module-level
`import urllib.request`, `_http_post` Request/POST + timeout=60, positional
`(endpoint, body, headers)` call, Content-Type set, fenced filter at line 141).
All tests offline (patch/injection only) — FR-005/non-goal upheld.

## Result
**STATUS: PASS**
