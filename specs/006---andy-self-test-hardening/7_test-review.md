# Test Review — Sprint 6: Andy Self-Test Hardening

**Branch**: `sprint-6-andy-self-test-hardening`
**Date**: 2026-11-18
**Delegation**: deleg_f08811ad (task 1)

## Results
92 passed / 0 failed / 0 skipped (14-15s).

## SC-001 Mutation Verification (empirical, scratch copies; repo untouched)
| Mutant | Injected | Target test | Result |
|--------|----------|-------------|--------|
| G1 | `method="POST"`→`"GET"` | transport verb+timeout | FAILED ✓ KILLED |
| G3 | `timeout=60`→`0` | transport verb+timeout | FAILED ✓ KILLED |
| G4 | endpoint→evil URL | `uses_openrouter_endpoint` | FAILED ✓ KILLED |
| G5 | fenced `and`→`or` (line 141) | `fenced_fallback_dedupes...` | FAILED ✓ KILLED |
| G2 | utf8→ascii (NOT injected) | — | Correctly excluded (equivalent under ensure_ascii=True) |

## Findings
1. SC-001 PASS — 4 new tests (G1+G3 share the urlopen-patch seam) all
   red-on-mutant / green-on-baseline.
2. FR-001/003 patch target + context-manager fake shape CORRECT
   (module-level `import urllib.request`; `with urlopen(...) as resp`).
3. FR-002 Content-Type + body round-trip CORRECT; correctly does NOT attempt
   the impossible utf8/ascii byte distinction.
4. G5 exercises the fenced fallback branch (no `<snippet>` tags), `or`-mutant
   leaks dup/empty/identity → fails.
5. Behavior specs, not tautologies.
6. No new test RED on baseline; G2 correctly absent from the kill set.
7. NFR-001 stdlib-only preserved; NFR-002 88→92.

Minor (non-blocking): endpoint test would be tautological vs a mutant that
changed the `OPENROUTER_ENDPOINT` constant itself — out of G4's defined scope.

## Review Result
**STATUS: PASS**