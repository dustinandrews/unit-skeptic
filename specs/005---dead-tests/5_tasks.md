# Tasks — Dead-Test Detection (Sprint 5)

## Status
Gates 1–3 PASS (spec-review PASS + 4 warnings; plan-review PASS + nodeid pin;
tasks-review PASS — categorized done). Start T001 implementation.

- [ ] T001 runner per-test attribution: `run_mutant` optional `junit_path`
      (absolute only), parse junit failures BEFORE rmtree cleanup, return
      `(verdict, failing_ids)` when junit set; default keeps verdict-string.
      RED: 4 tests (killed→ids, survived→[], backward-compat string,
      absolute-required, nodeid reconstruction pinned `classname::name`).
      GREEN: implement + `PYTHONDONTWRITEBYTECODE=1` in runner env.
- [ ] T002 pure aggregation: `adversary/deadtests.py` — `aggregate_kills`
      (error/timeout NOT attributed), `classify` (dead = kills == 0),
      `build_output` (FR-003: corpus-qualified, dead-first stable order,
      totals). RED: 3 tests → GREEN.
- [ ] T003 driver + CLI: `run_deadtests(subject_dir, out_path)` walks sites +
      DeterministicMutator, junit attribution per mutant; `cli.py` gains
      `deadtests --subject --out`. TDD RED: CLI required-arg, `--out` honored,
      guineapig integration (SC-001: 4 weak dead + strong alive), SC-003
      reproducibility (byte-identical), SC-004 subject unmodified + no
      `__pycache__`. GREEN: implement; full suite green.
- [ ] T004 verify + docs: real CLI run on guineapig → dead list = exactly the 4
      weak tests (SC-001 evidence); README deadtests section; PRODUCT_PLAN +
      TECH_STACK updated; commit on `sprint-5-dead-tests`.

## Review Result
STATUS: PASS (6_tasks-review.md)
