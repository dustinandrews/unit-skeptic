# Spec Review — Sprint 6: Andy Self-Test Hardening

**Branch**: `sprint-6-andy-self-test-hardening`
**Date**: 2026-11-18
**Delegation**: deleg_185d4b58 (initial) → deleg_129e635c (re-review)

## Initial Review: STATUS FAIL
The first independent review (deleg_185d4b58) confirmed all five G1–G5 surviving
mutant claims are accurate against the code, but flagged ***blockers*** that
made G1/G2/G3 not cleanly testable as written:

1. **G1 (verb) / G3 (timeout) — BLOCKER**: `real_complete` calls the injected
   `http_post(endpoint, body, headers)` with only 3 args; the `method="POST"` and
   `timeout=60` live *inside* `_http_post`'s `Request(...)` / `urlopen(...,
   timeout=60)`, so an injected fake `http_post` can never observe them. A
   faithful implementer could not write a failing-then-passing test under the
   original FR-001/FR-003/FR-005 "inject fake http_post" mechanism.
2. **G2 (encoding) — BLOCKER**: with an ASCII-only prompt, `.encode("utf-8")`
   and `.encode("ascii")` produce identical bytes, so the encoding assertion was
   vacuous and the ascii mutant would survive.
3. **US2 AS1 — WARNING**: omitted the empty fenced block that FR-004 requires.
4. **SC-003 — WARNING**: was a hard gate tied to stochastic live-LLM + network
   output ("strictly higher live score") — not a deterministic CI criterion.

## Revised Spec: STATUS PASS
Re-review (deleg_129e635c) verified all four blockers resolved against the
actual code (`import urllib.request` is module-level at andy.py:42; `_http_post`
builds `Request(..., method="POST")` and calls `urlopen(req, timeout=60)` at
152–153):

1. **G1/G3 seam fixed**: spec now mandates patching `andy.urllib.request.urlopen`
   to capture the `Request` (`get_method()=="POST"`) and the `timeout` kwarg
   (`==60`). Stdlib-practical; correctly abandons the injectable-fake seam that
   cannot see method/timeout.
2. **G2 fixed**: FR-002/US1 AS2 require a non-ASCII prompt char, so an
   `.encode("ascii")` mutant raises `UnicodeEncodeError` in `real_complete`
   (before either seam) — non-vacuous and kills the ascii mutant.
3. **US2 AS1 fixed**: now requires duplicate + empty + identity fenced blocks;
   the empty block is what fails the `or` mutant, in a fenced-only reply that
   reaches the fallback branch.
4. **SC-003 fixed**: demoted to "reported, not gating"; SC-001/SC-002 are the
   deterministic hard gates.

No new blockers surfaced. FR-001/002/003/005 internally consistent; NFR-001
(stdlib-only) and NFR-002 (88 → 92–94) intact; non-goals preserved (no source
edits, no live HTTP, no new deps, no new subcommands). G1–G5 killed via
test-side changes only.

## Result
**STATUS: PASS**

## Review Plan
SEE APPROVED SPEC (1_spec.md) — proceed to implementation planning.
