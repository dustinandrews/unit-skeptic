# Test Review — LLM Andy Driver

**Branch**: `sprint-4-llm-andy` · **Baseline**: 773f975
**Date**: 2026-11-16
**Reviewer**: independent sub-agent, STRICTLY read-only (parent verified tree
hash unchanged after dispatch; the earlier self-signed artifact was VOID)

## Test Results
| Metric | Count |
|--------|-------|
| Total | 76 |
| Passed | 76 (100%) |
| Failed | 0 |
| Skipped | 0 |

Run: `.venv/bin/python -m pytest -q -p no:cacheprovider` → 76 passed in 4.21s.
test_andy.py collects 20 test functions (context said 19 — count nit, not a defect).

## Findings
| # | FR/SC | Verdict | Notes |
|---|-------|---------|-------|
| 1 | SC-003 structural blindness | PASS | build_prompt receives only subject source + one site; blanks site to `<PLACEHOLDER>` via equiv.build_blocks; PROMPT_TEMPLATE never references tests/coverage/verdicts/survivors. Test asserts forbidden words absent; a spy on the actual complete() arg confirms site text and 'test' never reach transport. Stateless one-shot, no feedback loop. |
| 2 | FR-004 parse_reply filtering | PASS | Dedupe, non-empty, identity filter, fenced fallback, garbage/empty handled. Runner double-guards identity skip. |
| 3 | SC-001 + FR-003 key hygiene | PASS | runtime_checkable Mutator conformance asserted; run_loop drives LlmMutator with zero changes. Key appears ONLY in Authorization header (captured URL/body/headers), never body/prompt; missing key → clear RuntimeError. |
| 4 | FR-008 offline determinism | PASS | offline_complete pure and reproducible; no network, no key (NFR-003). |
| 5 | SC-002 CLI offline end-to-end | PASS | Real tmp repo, real runner subprocess, real score; asserts mutator=llm, rc==0. |
| 6 | SC-004 backward compatibility | PARTIAL, non-blocking | Default --mutator deterministic wired + asserted; no golden byte-parity, but FR-006 intentionally adds mutator=/model= attribution, so strict byte-identity is in tension with the sprint's own feature. Compatibility intent honored (same sites/score formula). |
| 7 | Behavior specs, not tautologies | PASS | Real subprocess/file I/O, wire-format spies, cross-module guard vs equiv.build_blocks. Only implementation-coupled assertions are offline stub canned strings — appropriate for a determinism contract. |

## Non-blocking gaps
- FR-007 (subject read-only) not asserted in test_andy.py — inherited from runner guarantee; Andy performs no I/O.
- Score-line `model=<id>` segment not asserted (mutator=llm asserted; model asserted in JSON records).
- SC-004 strict byte-parity — finding 6.
- SC-005 live-run — correctly not tested (verification note; CI offline).
- NFR-001 — not tested, but andy.py imports only stdlib + adversary.equiv (verified by inspection).

## Review Result
STATUS: PASS
