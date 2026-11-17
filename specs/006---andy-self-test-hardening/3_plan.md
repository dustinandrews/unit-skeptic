# Implementation Plan: Andy Self-Test Hardening

**Branch**: `sprint-6-andy-self-test-hardening`
**Date**: 2026-11-18
**Spec**: [1_spec.md](1_spec.md)

## Summary
Harden `adversary`'s own test suite so it kills the five surviving mutations
(G1–G5) the live-Andy dogfood exposed, by adding transport tests that patch
`andy.urllib.request.urlopen` (verb + timeout), a non-vacuous encoding test, an
endpoint assertion, and a fenced-fallback dedupe test. Test-only; no source
changes, no new deps.

## Technical Context
- **Language**: Python 3.11 — **Dependencies**: stdlib only (NFR-001).
- **Project Type**: library + CLI (`adversary` package).
- **Subject under test**: `adversary/adversary/andy.py` (target of mutation).
- **Test host**: `adversary/tests/test_andy.py` (unit) — all tests go here.
- **No real I/O ever**: verb/timeout via patched `andy.urllib.request.urlopen`
  (patch target is legal: `_http_post` uses module-level `import urllib.request`
  → `urllib.request.urlopen` resolved via `andy`'s namespace). The fake must
  return an object with `read() -> bytes` of a valid completion JSON.
- **Existing fake seam** (`test_real_complete_puts_key_in_header...`) already
  captures url/body/headers; reuse its shape for G4.

## Trigger words / semantics recap (from spec)
- **G1** verb `"POST"`→`"GET"` survives → new test asserts `req.get_method()=="POST"`.
- **G2** `.encode("utf-8")`→`.encode("ascii")` survives → new test uses a
  NON-ASCII prompt char so the ascii mutant raises `UnicodeEncodeError`.
- **G3** `timeout=60`→`0` survives → new test asserts recorded `timeout kwarg == 60`.
- **G4** endpoint swap survives → new test asserts captured `url == OPENROUTER_ENDPOINT`.
- **G5** fenced dedupe `and`→`or` survives → new test feeds fenced blocks
  containing a duplicate, an empty, and an identity; asserts dedupe/empty/identity
  filtering in the fenced branch.
- sc_overbar: G1/G3 share one urlopen-patch test (observes method AND timeout in
  one call); G2 and G4 can share the injected-fake shape but must be asserted
  distinctly. Keep each mutation mapped to ≥1 obviously-failing test (SC-001).

## Project Structure (no new files)
```
adversary/adversary/andy.py   # UNTOUCHED (correct)
adversary/tests/test_andy.py  # +5 new tests (T001–T005), under the existing
                              # "Real transport" and parse_reply sections
```

## Task List
1. **T001 — transport verb + timeout pin** (P1) `test_real_complete_transport_uses_http_post_method_and_60s_timeout`
   Monkeypatch `andy.urllib.request.urlopen` with a fake capturing `req` and the
   `timeout` kwarg, returning a fake resp (`read()` → completion JSON with a
   non-ASCII-ish content is fine). Call `andy.real_complete("probe prompt",
   api_key="k")` (http_post stays `None` so the real `_http_post` runs against
   the stubbed urlopen). Assert `req.get_method()=="POST"` and `timeout==60`.
   RED on G1 (`"GET"`) and G3 (`timeout=0`); GREEN on baseline.
   *(Independent sub-asserts so it maps to both G1 and G3 for SC-001.)*
2. **T002 — encoding pinned non-vacuously** (P1) `test_real_complete_body_is_utf8_not_ascii`
   Inject fake `http_post` capturing body (existing shape); prompt contains a
   NON-ASCII char (e.g. `"probe … prompt"` or a unicode escape). Assert body is
   `utf-8` bytes containing the non-ASCII char, and
   `body.decode("utf-8")` re-derives it. RED on G2 (`.encode("ascii")` raises
   during the call); GREEN on baseline.
3. **T003 — endpoint pinned** (P1) `test_real_complete_uses_openrouter_endpoint`
   Inject fake `http_post` capturing `url`; assert `url == andy.OPENROUTER_ENDPOINT`.
   RED on G4 (endpoint swapped); GREEN on baseline.
4. **T004 — fenced-fallback dedupe/empty/identity** (P1)
   `test_parse_reply_fenced_fallback_dedupes_empty_and_identity`
   Fenced-only reply (no `<snippet>` tags, so it reaches the fallback branch)
   containing: a duplicate, an empty block, an identity-original block, and a
   distinct valid block. Assert only the distinct valid candidate returns.
   RED on G5 (`or` lets the dup/empty/identity through); GREEN on baseline.
5. **T005 — SC-001 verification of G1–G5 mutations** (P1) (test-side)
   After T001–T004 land, run the deterministic mutator against `andy.py` with
   the new tests as the oracle to confirm G1–G5 no longer survive and the
   self-score rises. Not a committed unit test — a verification run (SC-001/SC-002).
6. **T006 — docs/plan/stack** (P2) update `TECH_STACK.md` "test hardening" note
   and `PRODUCT_PLAN.md` "Done" (Sprint 6), test count 88 → 93, and the self-score
   impact note. Re-run full suite (expect 93 passed).

## Review Result
STATUS: Draft
