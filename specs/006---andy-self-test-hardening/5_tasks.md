# Tasks — Sprint 6: Andy Self-Test Hardening

**Branch**: `sprint-6-andy-self-test-hardening`
**Date**: 2026-11-18
**Plan**: [3_plan.md](3_plan.md)

## Phase 1: Setup
- [ ] T001 [P] Branch + feature dir + spec/plan/review docs already landed
  (gates 1–4). No setup tasks pending — code lives in `adversary/tests/test_andy.py`.

## Phase 2: Test hardening (User Stories 1–2, all P1)

### Transport (US1)
- [ ] T002 [US1/G1+G3] Add `test_real_complete_transport_uses_http_post_method_and_60s_timeout`:
  patch `andy.urllib.request.urlopen` with a fake context-manager capturing
  `req` + `timeout` kwarg (`__enter__` → resp whose `read()` yields completion
  JSON); call `real_complete("probe prompt", api_key="k")` (http_post=None so
  real `_http_post` runs against the stub). Assert `req.get_method()=="POST"`
  and `timeout==60`. RED on G1/G3, GREEN on baseline.
- [ ] T003 [US1/FR-002] Add `test_real_complete_sets_content_type_and_body_roundtrips`:
  inject fake `http_post` capturing `headers`+`body`; prompt has a non-ASCII
  char (`"probe … prompt"`). Assert `headers["Content-Type"]=="application/json"`
  and `json.loads(body.decode())["messages"][0]["content"] == original prompt`.
  GREEN on baseline. (No utf8/ascii distinction — impossible, G2 equivalent.)
- [ ] T004 [US1/G4] Add `test_real_complete_uses_openrouter_endpoint`: inject
  fake `http_post` capturing `url`; assert `url == andy.OPENROUTER_ENDPOINT`.
  RED on G4, GREEN on baseline.

### Parser (US2)
- [ ] T005 [US2/G5] Add `test_parse_reply_fenced_fallback_dedupes_empty_and_identity`:
  fenced-only reply (no `<snippet>` tags) containing a duplicate, an empty
  block, an identity-original, and a distinct valid block; assert only the
  distinct valid candidate returns. RED on G5, GREEN on baseline.

## Phase 3: Verification + docs
- [ ] T006 [P] Run deterministic mutator against `andy.py` with new tests as
  oracle (SC-001): confirm G1/G3/G4/G5 no longer survive; self-score rises
  (baseline deterministic 0.923). G2 remains a documented equivalent survivor.
  Verification run only — not a committed test.
- [ ] T007 [P] Update `TECH_STACK.md` + `PRODUCT_PLAN.md` (Sprint 6 Done),
  test count 88 → 92, self-score impact, G2-equivalence finding. Full suite
  green: **92 passed**.

## Review Result
STATUS: Draft
