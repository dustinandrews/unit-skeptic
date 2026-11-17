# Product Review — LLM Andy Driver

**Branch**: `sprint-4-llm-andy` · **Baseline**: 773f975
**Date**: 2026-11-16
**Reviewer**: independent sub-agent, executed golden path live (parent verified
tree hash unchanged after dispatch; the earlier self-signed artifact was VOID)
**Subject**: `guineapig`

## Golden Path Executed
1. Full suite: `pytest -q -p no:cacheprovider` → **76 passed** in 3.88s.
2. Offline Andy e2e: `adversary score --subject ../guineapig --mutator llm
   --offline --trials-per-site 2` → baseline green (0.17s), B: 73 sites,
   `score = 1.000 (killed=65, survived=0, error=8, timeout=0)  mutator=llm
   model=openrouter/auto`, survivors.json written, exit 0.
3. Backward compat: no llm flags → `mutator=deterministic`,
   `score = 1.000 (killed=17, survived=0, error=0, timeout=0)`, exit 0.
4. Reproducibility (FR-008): offline run twice → score lines identical AND
   survivors.json **byte-identical** (diff clean).
5. Repo integrity: `guineapig/src/guineapig/pricing.py` + `__init__.py` mtimes
   unchanged; only survivors.json created (gitignored).
6. `--help` exposes `--mutator {deterministic,llm}`, `--model`,
   `--trials-per-site`, `--offline` with defaults.
7. FR-006 attribution: records carry mutator/model (llm run: all 73 records;
   deterministic run: mutator=deterministic, model="").

## Results checklist
- Entry point accessible: PASS
- Core process executes: PASS
- Expected output produced: PASS
- No critical errors: PASS

## SC mapping
- SC-001 PASS — LlmMutator drives through scorer.run_loop unchanged.
- SC-002 PASS — offline run completes, prints mutator=llm model=openrouter/auto.
- SC-003 PASS — prompt from enclosing function + `<PLACEHOLDER>` only.
- SC-004 PASS — default deterministic output shape compatible; only additive
  change is FR-006 attribution.
- SC-005 — verification note, not a gate; CI stays offline.

## Defects
None. Nit (non-blocking): deterministic survivors records carry `"model": ""`
rather than omitting the field — cosmetic, consistent, satisfies FR-006.

## Cleanup
Reviewer removed survivors.json; temp files only under scratch. No project
source modified.

## Review Result
STATUS: PASS
