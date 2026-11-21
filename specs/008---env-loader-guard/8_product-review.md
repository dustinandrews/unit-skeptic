# Product-Review: `.env`-Loader Export-Wins Guard (sprint 8)

**Date**: 2026-11-21
**Status**: PASS (independent, deleg_8a95e856)

## Outcome check vs spec intent
Original gap: `_load_env_file` ("and"→"or") export-wins bug escaped the suite —
a `.env` value would silently overwrite an exported env var (e.g. the wrong
`OPENROUTER_API_KEY`). Prior deterministic self-score 0.929 had this one
survivor.

End state (verified):
- Export-wins contract now locked by a genuine kill test.
- Deterministic self-score on the adversary package: **1.000** (14 caught /
  0 escapes).
- Full suite **107 green**; test count +3 (FR-001/002/003 covered).

## Gate
PASS — product intent met; the last S6 deterministic escape is closed and the
self-score is clean (1.000).