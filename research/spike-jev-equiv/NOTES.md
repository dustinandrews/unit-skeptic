# JEV Equivalence-Triage Spike — results

**Date:** 2026-11-12
**Model:** `typesafe/jev-1.14` via OpenRouter `/api/alpha/decisions`
**Driver:** reused `triage-engine/src/jev/client.py` (JevClient + injected stdlib
urllib transport; no client changes). Key read from `~/orchestrator-openrouter-api-key.txt`.

## Method
For each labeled case, present the original ("Function A") and the mutant
("Function B") as two **clean labeled code blocks** — no diff — plus a single
`choice` question with criteria `equivalent` / `different`, and ask for the label.

## Result — 12/12 exact
| Metric | Value |
|--------|-------|
| accuracy | 1.00 |
| precision (equiv) | 1.00 |
| recall (equiv) | 1.00 |
| tp / fp / tn / fn | 6 / 0 / 6 / 0 |

### Cases tested
- **equivalent (6, all correct):** commutative `0 < n` vs `n > 0`; `0` vs `0.0`
  return value; set-literal reorder + `"gift" == k` commute; `int` transcribe
  identity; no-op `and True`; boundary transcription.
- **different (6, all correct):** `<` vs `>` flip; shifted thresholds `>10`/`>5`;
  gift-exempt removed; exempt-negation; default rate `0.1` vs `0.0`;
  **half-penny `round()` vs Decimal `ROUND_HALF_UP`** (genuinely hard: an edge
  case, not a mechanical flip).

## Takeaways for Sprint 4
1. JEV is **genuinely competent** at A/B code-equivalence classification on
   small pure functions — including the half-penny edge a lightweight model
   should miss.
2. **A/B blocks beat a diff** (user preference, confirmed sensible): JEV reads
   two self-contained wholes; presentation is cheap and clean.
3. Confidence is returned per answer — usable for an `undecided` bucket when
   JEV is unsure, so a heavier partner model escalates only the genuinely hard
   few. (Not yet exercised in this spike.)
4. Not yet tested: larger real-world functions, multi-statement equivalent
   refactors, and behavior hidden behind non-trivial control flow. Scope Sprint
   4's equiv pass to small/medium pure functions first.

## Repro
```
cd ~/projects/adversary/research/spike-jev-equiv
~/projects/triage-engine/.venv/bin/python run_spike.py          # live JEV
~/projects/triage-engine/.venv/bin/python run_spike.py --dry     # payloads only
```
