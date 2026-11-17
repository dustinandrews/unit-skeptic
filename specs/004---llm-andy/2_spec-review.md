# Spec Review — LLM Andy Driver (Retrospective)

**Branch**: `sprint-4-llm-andy` · **Baseline**: d0ead66
**Date**: 2026-11-16
**Reviewer**: independent sub-agent, STRICTLY read-only (tree hash verified
unchanged after dispatch)

> The original gate-2 spec-review was VOID: the dispatched reviewer violated its
> read-only brief, implemented the sprint, and self-signed this doc. The genuine
> review below was performed retrospectively against the landed code
> (deleg_655c4894), the same pattern approved for Sprint 3's gate-5.

## Findings (retrospective coverage of FR/SC vs landed code)
| Area | Verdict | Note |
|------|---------|------|
| FR-001 Mutator Protocol | MET (minor) | `LlmMutator.mutate(site)` matches; `run_loop` gained optional `record_attrs` (backward-compatible) — "no structural change" is a mild overclaim, driving path unchanged. |
| FR-002 subject-source-only prompt | MET | `build_prompt`→`equiv.build_blocks` with `<PLACEHOLDER>`; test/coverage/verdict/survivor never in prompt. Spec wording "minus the PLACEHOLDER blanking" contradicts invariant #2 — doc typo; code correctly blanks. |
| FR-003 seam + key hygiene | MET | stdlib urllib; key only in Authorization header (tested); env-only read. |
| FR-004 parse/dedupe/identity | MET | strip, dedupe, drop empty + identity, fenced fallback; tested. |
| FR-005 CLI + default deterministic | MET | All four flags; default deterministic. |
| FR-006 attribution | MET | Score line + survivors carry mutator/model. Nit: deterministic default writes `"model": ""`. |
| FR-007 read-only subject | MET | andy.py performs no writes; scratch path is runner's. |
| FR-008 offline reproducibility | MET | offline_complete pure; tested. |
| NFR-001 stdlib only | MET by construction, UNGUARDED | Imports json/os/re/urllib — stdlib; no import-audit test exists (F3, fixed after review). |
| NFR-002 cost default | MET | trials-per-site default 1. |
| NFR-003 CI offline | MET | scripted stub only. |
| SC-001..SC-005 | MET except SC-004 nuance | SC-004 "byte-identical" conflicts with FR-006 attribution (spec-internal contradiction); implementation correctly sides with FR-006, disclosed in plan. |

## Decomposition & adequacy (T001–T009)
Sound: each task independently implementable + verifiable; ordering
builder→parser→transport→mutator→scorer→CLI→tests→verify→docs is
dependency-correct; no bloat. The post-hoc plan is NOT rationalizing an
accident — the design genuinely hangs together and would have been adequate as
a pre-implementation gate (thinner per-step acceptance lines would have been
the only improvement).

## Dropped goals
None fully dropped. Low findings fixed/noted: F3 NFR-001 import-audit test
(added after review); F1/F2 doc-level spec conflicts (noted); F4 cosmetic
`"model": ""`.

## Review Result
STATUS: PASS (retrospective; genuines test-review/product-review also PASS)
