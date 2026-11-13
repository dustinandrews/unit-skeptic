# Product Review — Sprint 2 Score Instrument

**Branch**: `sprint-2-score-instrument`
**Date**: 2026-11-12
**Reviewer**: independent subagent (executed golden path live)

## Golden Path Tested (live)
- Baseline: `cd ~/projects/adversary/guineapig && .venv/bin/python -m pytest -q -p no:cacheprovider` → 33 passed, exit 0.
- CLI end-to-end: `cd ~/projects/adversary/adversary && .venv/bin/python -m adversary.cli score --subject ../guineapig` → baseline green (0.14s), 73 sites, score = **1.000** (killed=17, survived=0, error=0, timeout=0), survivors.json written (path, char offsets, orig/replacement, verdict).
- Reproducibility: second run identical (1.000; survivors.json diff-identical).
- Repo integrity: guineapig `src/guineapig/pricing.py` sha256 unchanged after run; no leftover `adv_mutant_` scratch dirs (FR-006).
- SC-004: score ≥ 0.8 met (1.000). Weak-test cohort does not move the score (exercises no pricing behavior).

## Defects
- (Fixed during review) DeterministicMutator substring-matched `>` inside `>=`, producing malformed mutants like `quantity <= = 10` — wasted runs + noise. Fix: token-level longest-first matching. Verified: error verdicts dropped 4 → 0, score still 1.000, regression tests added.
- (Accepted) Compare sites + nested Op sites can yield duplicate identical mutants — efficiency only, not correctness; deferred.

## Review Result
STATUS: PASS
