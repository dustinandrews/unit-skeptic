# Adversary — Action Plan

## Subject (locked)
- Repo: ~/projects/triage-engine (MIT, pure rule engine, deterministic)
- Mutate: src/engine.py (377 lines, no I/O)
- Oracle: tests/test_engine.py → 117 passed in 0.16s
- Hermetic, fast → cheap per-mutant runs

## MVP (Phase 1) — vertical slice, prove the whole loop
Components in `adversary/`:
1. **run.py** — orchestrates A→B→C→record loop
2. **site_target.py** — AST finder for candidate sites (start: binary ops + call args)
3. **andy.py** — Andy driver (interface: given placeholder+context, return N snippets).
   SWAPPABLE: `deterministic` mutator (zero cost, proves plumbing) and `llm` (real Andy).
4. **validate.py** — mechanical gate: parse, identical/dedupe, ban-list
5. **verdict + record** — apply mutant → pytest → killed/survived/error/timeout → append json

## Acceptance (MVP)
- Loop runs end-to-end on ≥10 sites, survivors recorded to results/*.json
- Same mutation reproducible (deterministic mode)
- Green gate enforced (skip if baseline fails)

## Later (additive)
- Expand site types → equivalence triage on survivors → docker sandbox runner → adaptivity
