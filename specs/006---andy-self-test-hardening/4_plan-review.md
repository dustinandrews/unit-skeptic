# Plan Review — Sprint 6: Andy Self-Test Hardening

**Branch**: `sprint-6-andy-self-test-hardening`
**Date**: 2026-11-18
**Delegation**: deleg_8c7fd1c0 (initial) → deleg_71e2c823 (re-review)

## Initial Review: STATUS FAIL
deleg_8c7fd1c0 empirically proved the plan's T002 was **fatally flawed**:

- `json.dumps` defaults to `ensure_ascii=True`, so a non-ASCII prompt char is
  escaped to `\uXXXX`; the encoded body is always 100% ASCII.
- `.encode("utf-8")` vs `.encode("ascii")` are **byte-identical** on the escaped
  string → the G2 mutant is behavior-preserving → **no black-box test can kill
  it**; the proposed assertion was RED on baseline (breaking SC-002).
- Also flagged: FR-002's `Content-Type: application/json` header was never
  asserted (only `Authorization` was).

## Re-review: STATUS PASS
deleg_71e2c823 verified all seams empirically and confirmed the revision:

1. **G2 reclassified EQUIVALENT** (documented-only, dropped from kill set and
   SC-001) — correct: the mutation is behavior-preserving under
   `ensure_ascii=True`; it is precisely what the tool's own JEV `equiv` triage
   would label "equivalent". No test attempts the impossible utf8/ascii
   distinction.
2. **T002 rewritten** to the genuine FR-002 gap: asserts
   `headers["Content-Type"] == "application/json"` and body round-trips via
   `json.loads(body.decode())` (un-escapes `\uXXXX` back to the original
   prompt). GREEN on baseline.
3. **T001** (urlopen-patch context manager → `get_method()=="POST"` +
   `timeout==60`) kills G1/G3, legal patch target, GREEN baseline.
4. **T003** (endpoint == `OPENROUTER_ENDPOINT`) kills G4; **T004** (fenced
   dedupe/empty/identity) kills G5. Both verified.
5. **Count corrected: 92** (88 baseline + 4 committed tests T001–T004; T005 is
   a verification run, T006 docs). SC-001's "1:1" wording noted loose (T001
   covers G1+G3) but every KILL row is covered.

No test is RED on baseline; all deterministic-gated; NFR-001/002 intact; YAGNI
preserved (`andy.py` UNTOUCHED, no deps, no subcommands).

## Result
**STATUS: PASS**
