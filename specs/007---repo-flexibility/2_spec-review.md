# Spec Review — Sprint 7: Repo-Flexible Subjects

**Branch**: `sprint-7-repo-flexibility`
**Date**: 2026-11-18
**Delegation**: deleg_a7e0dd5b

## Result
**STATUS: PASS** (92 passed baseline on main; all three Background claims
G1/G2/G3 verified accurate against the actual code).

## Findings acted on
| # | Sev | Issue | Action taken in spec |
|---|-----|-------|----------------------|
| 1 | MED | SC-003 had no test seam — no production code records `sys.executable`; achievable only via monkeypatch capture | Spec now names the seam: monkeypatch `runner.subprocess.run`/`_pytest` to capture `cmd` and fake rc=0, assert interpreter == `--python`, for oracle + first mutant |
| 2 | LOW | "common plumbing" FR contradicted itself ("run_loop keeps signature" AND "default lambda must forward via closure") | Reworded: forwarding 100% caller-owned via `cli.run_score` passing a `run_mutant_impl` closure; `run_loop` signature/lambda unchanged; no new `run_loop` params |
| 3 | LOW | Changed CLI surface not named (cli.run_score/run_deadtests + argparse) | Added explicit "Changed CLI surface" para listing the wrapper signatures and subparser args |
| 4 | LOW | Error strings hardcode `"src"` (cli.py:39, deadtests.py:99) — misleading under `--src-rel` | Spec requires interpolating the effective `src_rel` in those messages |

## Consistent (INFO)
- `--tests-rel`+`--python` on score+deadtests; `--src-rel` on score+equiv+deadtests; `equiv` correctly gets only `--src-rel` (runs no pytest).
- `record_attrs python=<basename>` on score only; deadtests emits `build_output` (no survivors file).
- `_baseline_test_ids` seam (hardcoded `"tests"` + `sys.executable`) covered by FR-002.
- YAGNI clean: no auto-detect, no multi-module, no semantic change.
- SC-002/004/005/006 achievable with tmp-dir synthetic subjects (deterministic, no external repo).
