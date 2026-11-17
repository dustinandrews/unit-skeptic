# Feature Specification: Andy Self-Test Hardening

**Branch**: `sprint-6-andy-self-test-hardening`
**Created**: 2026-11-18
**Status**: Draft

## Background / Motivation
Sprint-4 dogfooding ran unit-skeptic's own "Andy" LLM mutator (live, `openrouter/auto`)
against `adversary/andy.py` using the suite's own tests as the oracle. Result:
**score 0.526** (41 killed / 37 survived / 4 error). The surviving faults expose
concrete blind spots in the suite — the very "test theatre" this tool exists to
catch, present in its own harness. This sprint hardens those tests so the
live-LLM self-score rises and the specific gaps close.

Recorded surviving mutations (evidence), grouped by cause:

| # | Surviving fault | Root cause gap |
|---|-----------------|----------------|
| G1 | transport HTTP verb `"POST"` -> `"GET"` | `test_real_complete_*` capture `url/body/headers` via `fake_post` but never assert the verb, encoding, timeout, or endpoint. |
| G2 | `body.encode("utf-8")` -> `"ascii"` | same: encoding never asserted. |
| G3 | timeout `60` -> `0` | timeout lives in `_http_post` default; health-check/broker tests never exercise wall-clock. |
| G4 | endpoint swap | endpoint is a `real_complete` default arg, never asserted equals `OPENROUTER_ENDPOINT`. |
| G5 | reply-parser dedupe `s and s != orig and s not in cands` -> `s or s != orig and s not in cands` (fenced-fallback branch) | `test_parse_reply_fenced_fallback_when_no_tags` feeds a single valid block; the dup/identity/empty filtering in the fenced branch is never exercised. (Tag branch mutation IS killed by `test_parse_reply_dedupes...`.) |

Goal: every row above becomes red in TDD (a test that fails on the mutant),
i.e. the new tests kill G1–G5.

## Non-goals (YAGNI)
- NOT fixing `andy.py` source — it is correct; the suite needs to *prove* it.
- NOT adding JEV/equiv/LlmMutator behavior, no new subcommands.
- NO live HTTP in CI; `_http_post` stays untested for real I/O (offline stub /
  injected fake only).
- NO new third-party deps (NFR-001 stdlib only must hold).

## User Scenarios

### User Story 1 - Andy's suite kills its own transport mutations (P1)
An engineer runs the Andy mutator against `andy.py`. Faults that would change
the HTTP method to `GET`, encode the body as `ascii`, set timeout to 0, or swap
the endpoint must be **killed** (fail ≥1 test), not survive.

**Acceptance Scenarios:**
1. **Given** a mutant replacing `"POST"` with `"GET"` in `_http_post`, **When**
   the suite runs `real_complete` with `andy.urllib.request.urlopen` patched to
   capture the `Request`, **Then** the captured request `get_method()` is
   asserted `== "POST"` and that test fails under the mutant. (G1)
2. **Given** a mutant changing `body.encode("utf-8")` to `.encode("ascii")`,
   and the transport test uses a prompt containing a non-ASCII character,
   **When** the suite runs, **Then** the `.encode("ascii")` mutant raises and
   ≥1 test fails. (G2)
3. **Given** a mutant setting the connection timeout to `0` **When** the suite
   runs `real_complete` with `andy.urllib.request.urlopen` patched to record the
   `timeout` kwarg, **Then** the recorded timeout is asserted `== 60` and that
   test fails under the mutant. (G3)
4. **Given** a mutant swapping the endpoint default, **When** the suite runs,
   **Then** the captured `url` is asserted `== OPENROUTER_ENDPOINT` and that
   test fails under the mutant. (G4)

### User Story 2 - Fenced-fallback dedupe is proven (P2)
The reply parser's fenced (non-tag) fallback branch filters duplicates, empties,
and identity just like the tag branch. A regression that weakens that filter
must be killed.

**Acceptance Scenarios:**
1. **Given** a fenced reply containing a duplicate, an empty, and an
   identity-original block, **When** `parse_reply` runs, **Then** only distinct
   non-empty, non-identity candidates are returned.
2. **Given** a mutant weakening the fenced filter to `or`, **When** the suite
   runs, **Then** ≥1 test fails. (G5)

## Requirements

### Functional Requirements
- **FR-001**: The transport tests MUST assert the HTTP request targets
  `OPENROUTER_ENDPOINT` and uses method `POST`, by capturing the `Request` via
  a patched `andy.urllib.request.urlopen` and asserting `request.get_method()
  == "POST"`.
- **FR-002**: The transport scheme test MUST assert the request body is
  UTF-8-encoded JSON (NOT ASCII) and the headers set `Content-Type:
  application/json`. To make the encoding observable, the prompt MUST contain a
  non-ASCII character so an `.encode("ascii")` mutant raises.
- **FR-003**: The transport tests MUST pin `_http_post`'s connection timeout to
  `60` by patching `andy.urllib.request.urlopen` to record and assert the
  `timeout` kwarg.
- **FR-004**: `parse_reply` MUST have a fenced-fallback test proving dedupe
  (duplicate collapse), empty-drop, and identity-drop behave identically to the
  tag branch.
- **FR-005**: NO test does real I/O or hits the network. The verb (G1), timeout
  (G3) and encoding (G2) are observed by patching `andy.urllib.request.urlopen`
  with a fake that records the `Request`/`timeout` and returns a valid
  completion JSON response; the endpoint/body/headers (G4) are captured by an
  injected fake `http_post` as today. Neither seam reaches the live network.

### NFRs
- **NFR-001** (`adversary` package): stdlib-only imports preserved; no new
  third-party dependency. Guard test must still pass.
- **NFR-002**: Test count increases; all existing 88 tests still green.

## Success Criteria
- **SC-001**: ≥5 new tests, each mapping 1:1 to one of G1–G5, that FAIL with the
  corresponding mutant injected (verified by running the mutated copy).
- **SC-002**: Full suite green on `main` baseline + new tests (expect 92–94 passed).
- **SC-003** (reported, not gating): report the live-Andy self-score on
  `andy.py` after this sprint (deterministic baseline 0.923; live baseline
  0.526). Live score is stochastic (model + network may not re-propose these
  exact 5 mutants), so SC-003 is a reported result, NOT a hard gate; SC-001 and
  SC-002 are the deterministic acceptance criteria.
- **SC-004**: All TDD steps observed: each new test written RED (fails for the
  expected reason), then GREEN.

## Review Result
STATUS: Revised (addressing review blockers: urlopen-patch seam for G1/G3
method+timeout; non-ASCII prompt for G2 encoding; empty block added to US2 AS1;
SC-003 demoted to reported-not-gating). Re-review pending.
