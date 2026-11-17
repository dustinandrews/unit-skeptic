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

| # | Surviving fault | Root cause gap | Verdict |
|---|-----------------|----------------|---------|
| G1 | transport HTTP verb `"POST"` -> `"GET"` | `test_real_complete_*` capture `url/body/headers` via `fake_post` but never assert the verb, timeout, or endpoint. | KILL (test-side) |
| G2 | `body.encode("utf-8")` -> `"ascii"` | **EQUIVALENT, not a test gap** (see below). | DOCUMENT only |
| G3 | timeout `60` -> `0` | timeout lives in `_http_post` default; tests never exercise wall-clock. | KILL (test-side) |
| G4 | endpoint swap | endpoint is a `real_complete` default arg, never asserted equals `OPENROUTER_ENDPOINT`. | KILL (test-side) |
| G5 | reply-parser dedupe `s and s != orig and s not in cands` -> `s or s != orig and s not in cands` (fenced-fallback branch) | `test_parse_reply_fenced_fallback_when_no_tags` feeds a single valid block; the dup/identity/empty filtering in the fenced branch is never exercised. (Tag branch mutation IS killed by `test_parse_reply_dedupes...`.) | KILL (test-side) |

**G2 is an equivalent mutant, not a test gap.** `json.dumps` defaults to
`ensure_ascii=True`, so any non-ASCII character in the prompt/body is emitted as
an ASCII `\uXXXX` escape; the encoded body is therefore always 100% ASCII. Under
that default, `.encode("utf-8")` and `.encode("ascii")` produce byte-identical
output (empirically verified), so no black-box test can distinguish them, and
the original (correct) warning that a raw non-ASCII char is never present means
the mutation is behavior-preserving. This is precisely the case the tool's own
JEV `equiv` triage labels **"equivalent"** — a survivor that is NOT test
theatre. Killing it would require a source change (`ensure_ascii=False`), which
is out of scope (non-goal: no source edits) and not clearly desirable (ASCII-safe
bodies are valid). It is recorded here as a documented false positive that
`adversary equiv` would correctly triage.

Goal: every KILL row above becomes red in TDD (a test that fails on the mutant),
i.e. the new tests kill G1, G3, G4, G5. G2 stays as documentation.

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
- the endpoint must be **killed** (fail ≥1 test), not survive, and the request
  must carry the correct `Content-Type: application/json` header (a genuine
  transport-contract assertion the current suite omits).

**Acceptance Scenarios:**
1. **Given** a mutant replacing `"POST"` with `"GET"` in `_http_post`, **When**
   the suite runs `real_complete` with `andy.urllib.request.urlopen` patched to
   capture the `Request`, **Then** the captured request `get_method()` is
   asserted `== "POST"` and that test fails under the mutant. (G1)
2. *(G2 removed as a kill target — equivalent mutant under `ensure_ascii=True`,
   documented in the Evidence table; not a test gap.)*
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
- **FR-002**: The transport tests MUST assert the captured request carries the
  `Content-Type: application/json` header (a genuine transport-contract check
  the current suite omits — it only asserts `Authorization`). The body is
  asserted to be JSON that round-trips via
  `json.loads(body.decode())` (un-escapes `\uXXXX` back to the original prompt).
  No assertion is made that distinguishes UTF-8 from ASCII encoding, because
  the mutation is equivalent under `ensure_ascii=True` (no test can — see G2).
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
- **SC-001**: ≥4 new tests, each mapping 1:1 to one of G1, G3, G4, G5 (the
  KILL rows), that FAIL with the corresponding mutant injected (verified by
  running the mutated copy), plus the FR-002 `Content-Type`/body round-trip
  assertion. G2 is NOT part of SC-001 (equivalent mutant — documented).
- **SC-002**: Full suite green on `main` baseline + new tests (expect 92–93 passed:
  88 baseline + 4–5 new transport/parser tests).
- **SC-003** (reported, not gating): report the live-Andy self-score on
  `andy.py` after this sprint (deterministic baseline 0.923; live baseline
  0.526). Live score is stochastic (model + network may not re-propose these
  exact 5 mutants), so SC-003 is a reported result, NOT a hard gate; SC-001 and
  SC-002 are the deterministic acceptance criteria.
- **SC-004**: All TDD steps observed: each new test written RED (fails for the
  expected reason), then GREEN.

## Review Result
STATUS: COMPLETE (spec-review PASS deleg_129e635c; revised 2026-11-18 after
plan-review deleg_8c7fd1c0 empirically disproved G2's test-side killability:
G2 reclassified as EQUIVALENT mutant under ensure_ascii=True — documented false
positive; kill set is now G1/G3/G4/G5 + FR-002 Content-Type assertion; SC-001/2
updated)
