# Product Review — Dead-Test Detection

**Branch**: `sprint-5-dead-tests` · **Baseline**: 890695e
**Date**: 2026-11-16
**Reviewer**: independent sub-agent, executed golden path live (git forbidden by
brief; subject verified by sha256 + byte inspection instead)

## Golden Path
1. Suite: **88 passed** in 15.24s.
2. e2e: `adversary deadtests --subject guineapig --out dead.json` →
   `dead tests: 13 of 33 (corpus=deterministic)`, JSON shape correct
   (corpus/total/dead/alive/tests, dead-first, weak tests dead kills=0).
3. Reproducibility: two runs byte-identical (diff clean).
4. Subject integrity: sha256 `pricing.py` unchanged; no residual dead-tests.json
   in subject; zero new `.pyc` (bytecode guard verified).
5. `--help` shows `--subject`/`--out`; default `--out` writes to cwd and works.
6. Corpus-scoped: 9 strong tests read dead (operator-unreachable constant/
   rejection assertions) — correct, matches spec; 20 strong confirmed alive
   (e.g. kills=13, kills=5), tool non-trivial.

## Results checklist
- Entry point: PASS
- Core process: PASS
- Expected output: PASS
- No critical errors: PASS

## Defects
None.

## Review Result
STATUS: PASS
