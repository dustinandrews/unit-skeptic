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
1. **Given** a mutant replacing `"POST"` with `"GET"` in the transport, **When**
   the suite runs, **Then** ≥1 test fails. (G1)
2. **Given** a mutant changing `body.encode("utf-8")` to `.encode("ascii")`,
   **When** the suite runs, **Then** ≥1 test fails. (G2)
3. **Given** a mutant setting the connection timeout to `0`, **When** the suite
   runs, **Then** ≥1 test fails. (G3)
4. **Given** a mutant swapping the endpoint default, **When** the suite runs,
   **Then** ≥1 test fails. (G4)

### User Story 2 - Fenced-fallback dedupe is proven (P2)
The reply parser's fenced (non-tag) fallback branch filters duplicates, empties,
and identity just like the tag branch. A regression that weakens that filter
must be killed.

**Acceptance Scenarios:**
1. **Given** a fenced reply containing a duplicate and an identity-original
   block, **When** `parse_reply` runs, **Then** only distinct non-empty, non-identity
   candidates are returned.
2. **Given** a mutant weakening the fenced filter to `or`, **When** the suite
   runs, **Then** ≥1 test fails. (G5)

## Requirements

### Functional Requirements
- **FR-001**: `real_complete` transport tests MUST assert the HTTP request targets
  `OPENROUTER_ENDPOINT` via the `POST` method.
- **FR-002**: The transport tests MUST assert the request body is
  UTF-8-encoded JSON (not ASCII) and the headers set `Content-Type:
  application/json`.
- **FR-003**: The transport tests MUST pin `_http_post`'s connection timeout to
  `60`.
- **FR-004**: `parse_reply` MUST have a fenced-fallback test proving dedupe
  (duplicate collapse), empty-drop, and identity-drop behave identically to the
  tag branch.
- **FR-005**: NO test does real I/O; `_http_post` internals are verified without
  network (inject fake `http_post` and/or assert via a fake that the model's
  expected method/timeout/encoding are passed through where observable).

### NFRs
- **NFR-001** (`adversary` package): stdlib-only imports preserved; no new
  third-party dependency. Guard test must still pass.
- **NFR-002**: Test count increases; all existing 88 tests still green.

## Success Criteria
- **SC-001**: ≥5 new tests, each mapping 1:1 to one of G1–G5, that FAIL with the
  corresponding mutant injected (verified by running the mutated copy).
- **SC-002**: Full suite green on `main` baseline + new tests (expect 92–94 passed).
- **SC-003**: Deterministic AND live-Andy self-score on `andy.py` improves vs the
  recorded baseline (0.923 deterministic stays or rises; live 0.526 → strictly
  higher), with the five specific mutations no longer surviving.
- **SC-004**: All TDD steps observed: each new test written RED (fails for the
  expected reason), then GREEN.

## Review Result
STATUS: Draft
