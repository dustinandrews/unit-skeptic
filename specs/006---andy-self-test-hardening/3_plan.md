# Implementation Plan: Andy Self-Test Hardening

**Branch**: `sprint-6-andy-self-test-hardening`
**Date**: 2026-11-18
**Spec**: [1_spec.md](1_spec.md)

## Summary
Harden `adversary`'s own test suite so it kills the surviving mutations the
live-Andy dogfood exposed that are REAL test gaps (G1 verb, G3 timeout, G4
endpoint, G5 fenced dedupe), and assert the `Content-Type: application/json`
transport contract (FR-002). G2 (encoding) is reclassified as an EQUIVALENT
mutant under `json.dumps(ensure_ascii=True)` — empirically byte-identical
output, not a test gap, documented only. Test-only; no source changes, no new
deps.

## Technical Context
- **Language**: Python 3.11 — **Dependencies**: stdlib only (NFR-001).
- **Project Type**: library + CLI (`adversary` package).
- **Subject under test**: `adversary/adversary/andy.py` (target of mutation).
- **Test host**: `adversary/tests/test_andy.py` (unit) — all tests go here.
- **No real I/O ever**: verb/timeout via patched `andy.urllib.request.urlopen`
  (module-level `import urllib.request` at andy.py:42 → patch target is legal).
  `_http_post` uses `with urllib.request.urlopen(...) as resp:`, so the fake
  must be a **context manager** (`__enter__` returning an object whose `read()`
  yields valid completion JSON; `__exit__` a no-op). endpoint/body/headers via
  injected fake `http_post` (existing shape at test_andy.py:166-184).
- **G2 is NOT killable test-side** (empirically verified): `json.dumps` escapes
  non-ASCII to `\uXXXX`, so the encoded body is always 100% ASCII; the
  utf-8→ascii mutation is byte-identical and behavior-preserving. Any test
  attempting to distinguish them is RED on baseline (SC-002 violation). Do NOT
  add such a test. Document the equivalence (spec Evidence table) instead.

## Trigger words / semantics recap (from spec)
- **G1** verb `"POST"`→`"GET"` survives → new test asserts `req.get_method()=="POST"`.
- **G3** `timeout=60`→`0` survives → new test asserts recorded `timeout kwarg == 60`.
- **G4** endpoint swap survives → new test asserts captured `url == OPENROUTER_ENDPOINT`.
- **G5** fenced dedupe `and`→`or` survives → new test feeds fenced blocks
  containing a duplicate, an empty, and an identity; asserts dedupe/empty/identity
  filtering in the fenced branch.
- **FR-002** genuine gap: `Content-Type: application/json` header never asserted
  (only `Authorization` is) → new test asserts it + body round-trips via
  `json.loads(body.decode())`.
- **G2** — equivalent; no test (documented only).

## Project Structure (no new files)
```
adversary/adversary/andy.py   # UNTOUCHED (correct)
adversary/tests/test_andy.py  # +5 new tests (T001–T005), under the existing
                              # "Real transport" and parse_reply sections
```

## Task List
1. **T001 — transport verb + timeout pin** (P1) `test_real_complete_transport_uses_http_post_method_and_60s_timeout`
   Monkeypatch `andy.urllib.request.urlopen` with a fake context-manager
   capturing `req` and the `timeout` kwarg; `__enter__` returns a fake resp
   whose `read()` yields completion JSON. Call `andy.real_complete("probe
   prompt", api_key="k")` (http_post stays `None` so the real `_http_post` runs
   against the stubbed urlopen). Assert `req.get_method()=="POST"` and
   `timeout==60`. RED on G1 (`"GET"`) and G3 (`timeout=0`); GREEN on baseline.
2. **T002 — Content-Type + body round-trip (FR-002)** (P1)
   `test_real_complete_sets_content_type_and_body_roundtrips`
   Inject fake `http_post` capturing `headers` + `body` (existing shape);
   prompt contains a non-ASCII char (e.g. `"probe … prompt"`). Assert
   `headers["Content-Type"] == "application/json"` (the genuine gap the review
   found — only Authorization was asserted before) and that
   `json.loads(body.decode())["messages"][0]["content"]` equals the original
   prompt (un-escapes `\uXXXX` → proves body is JSON). GREEN on baseline. This
   test does NOT attempt to distinguish utf-8/ascii (impossible — G2).
3. **T003 — endpoint pinned** (P1) `test_real_complete_uses_openrouter_endpoint`
   Inject fake `http_post` capturing `url`; assert `url == andy.OPENROUTER_ENDPOINT`.
   RED on G4 (endpoint swapped); GREEN on baseline.
4. **T004 — fenced-fallback dedupe/empty/identity** (P1)
   `test_parse_reply_fenced_fallback_dedupes_empty_and_identity`
   Fenced-only reply (no `<snippet>` tags → fallback branch) containing: a
   duplicate, an empty block, an identity-original block, and a distinct valid
   block. Assert only the distinct valid candidate returns.
   RED on G5 (`or` lets the dup/empty/identity through); GREEN on baseline.
5. **T005 — SC-001 verification of G1/G3/G4/G5** (P1) (test-side)
   After T001–T004 land, run the deterministic mutator against `andy.py` with
   the new tests as the oracle to confirm G1/G3/G4/G5 no longer survive and the
   self-score rises (baseline deterministic 0.923). G2 expected to remain a
   documented equivalent survivor (triaged `equivalent` by JEV equiv). Not a
   committed unit test — a verification run (SC-001/SC-002).
6. **T006 — docs/plan/stack** (P2) update `TECH_STACK.md` "test hardening" note
   and `PRODUCT_PLAN.md` "Done" (Sprint 6), test count 88 → 93, self-score
   impact, and the G2-equivalence finding. Re-run full suite (expect 93 passed).

## Review Result
STATUS: Revised (plan-review deleg_8c7fd1c0 FAIL → T002 rewritten from an
impossible encoding assertion to the genuine Content-Type/body round-trip
check; G2 dropped from kill scope as equivalent; expect 93 passed). Re-review
pending.
