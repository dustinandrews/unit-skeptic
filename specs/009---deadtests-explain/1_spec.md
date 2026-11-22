# Feature Specification: Dead-Test Explanation (mechanical)

**Branch**: `sprint-9-deadtests-explain`
**Created**: 2026-11-21
**Status**: Draft → REVISED (gate-2 deleg_06d0e24c FAIL: FR-003(b) was data-ungrounded; redesigned below)

## Background / Motivation
`adversary deadtests` flags tests that catch nothing in the current corpus
(status `dead`, kill count 0) — but the CLI only prints a count
(`bad tests (catch nothing): N of M`) and the JSON gives `{test_id, kills,
status}`. It does NOT say **why** a test is dead. A developer staring at "9 of
16 tests are bad" can't tell whether the test is tautological/boilerplate, or
merely uncovered because the corpus is thin in its area. The distinction
matters (dogfood: most dead tests were *corpus-poverty artifacts*, NOT test
theatre).

Design (decided 2026-11-18): the verdict + raw reason are **MECHANICAL** — no
LLM judges whether a test is dead and no LLM writes the bulk reason. An LLM is
used only as a narrow, targeted explainer for ambiguous cases — and that
targeted-explain step is a follow-up, NOT this sprint. This sprint lands only
the mechanical explanation layer.

### Evidence reality (revised after gate-2 review)
- `dead ⟺ kills==0` ⟺ the test id appears in NO **killed** mutant's failing-set.
- `error`/`timeout` mutants ALWAYS return an **empty** failing-set
  (`runner.run_mutant` → `("error", [])` / `("timeout", [])`), so they can
  never name a test and CANNOT ground "regional participation".
- Therefore any reason built from a single test's OWN failing behavior is
  single-valued: a dead test simply never failed. To separate corpus poverty
  from a broad no-op we must use **class-region topology**, derived from
  SIBLING tests' kills — data we already collect.
- Class region = the test nodeid's prefix before the final `::` (pytest junit
  emits `classname::name`; the actual junit classname is dot-form, e.g.
  `tests.test_ai_service.TestSvc::test_x` → region `tests.test_ai_service.TestSvc`).
  **FALLBACK:** when the classname is empty the nodeid is a bare `name` with no
  `::`; treat the whole nodeid as its own region (sibling kills 0 → CASE A).

### The mechanical reason (CASE A vs CASE B)
For a dead test (kills==0), the reason is one of exactly two templates, chosen
by whether ANY other test in the SAME class region has kills:
- **CASE A — corpus poverty**: the dead test's class region contains NO
  sibling kill (no other test in its class killed anything). Reason exactly:
  `"no behavior-changing mutant landed in this test's class (corpus poverty)"`.
- **CASE B — regional no-op / redundancy**: the dead test's class region DOES
  contain sibling kills (other tests in the class killed N total), yet THIS
  test caught none. Reason:
  `"caught 0 mutants; sibling tests in this class caught N (redundant/regional
  no-op)"`.
Alive tests carry a confirmation reason: `"caught N mutants"`.

This is deterministic (same runs → same strings), uses only already-collected
`failing_ids` + nodeid class regions, touches NO error/timeout semantics, and
needs no model.

## Non-goals (YAGNI)
- NOT wiring an LLM/explainer (no new deps, no network, NFR-001). LLM prose
  explanation is a separate follow-up.
- NOT changing the dead/alive verdict, the score denominator, or
  error/timeout attribution semantics (unchanged; error/timeout failing-sets
  stay empty/unused).
- NOT touching `runner.run_mutant`'s verdict contract (JSON `killed/survived`
  tokens and the `(verdict, failing_ids)` tuple stay stable).
- NO new subcommands; extend `deadtests` output.
- NOT exposing per-site operator attribution in the reason (CASE A/B are
  class-level; per-operator prose is the LLM follow-up's job).

## User Scenarios

### User Story 1 - A dead test says why (P1)
An engineer runs `adversary deadtests` and sees a test flagged bad. The JSON
carries a one-line mechanical reason telling them which KIND of bad it is:
corpus poverty (the corpus never exercised its class) vs a redundant/regional
no-op (the class caught bugs but this test didn't).

**Acceptance Scenarios:**
1. **Given** a dead test whose class region has no sibling kills, **When** its
   entry is built, **Then** `reason` == the CASE A template.
2. **Given** a dead test whose class region HAS sibling kills (N total), **When**
   its entry is built, **Then** `reason` == the CASE B template naming N.
3. **Given** an alive test (kills=K), **When** its entry is built, **Then**
   `reason` == `"caught K mutants"`.
4. **Given** a dead test in a class region that is alone (no siblings), **When**
   built, **Then** CASE A applies (0 siblings).

## Requirements

### Functional Requirements
- **FR-001**: `build_output` MUST include a mechanical `reason` string for
  EVERY test (dead: CASE A or CASE B; alive: confirmation). Produced by a pure
  fn; deterministic; NO free-text/model.
- **FR-002**: Every `test_id` MUST be mapped to its **class region** (nodeid
  prefix before the final `::`; if there is no `::`, the whole nodeid is its
  own region) as a first-class field in the JSON entry (`class`), so the
  reason is auditable.
- **FR-003**: Reason selection MUST be a pure fn of
  `(test_id, test_kills, sibling_kills_by_class)`: kills==0 → CASE B if
  `sibling_kills(class) > 0` else CASE A; kills>0 → confirmation. Exactly the
  templates below; nothing else.
- **FR-004**: The driver (`run_deadtests`) MUST compute per-class sibling kills
  from the already-collected `(verdict, failing_ids)` runs and thread them into
  `build_output`. No change to `runner.run_mutant`'s return shape; wiring is in
  `deadtests.py`.

### Exact templates
- killed==0 and class sibling kills > 0 →
  `"caught 0 mutants; sibling tests in class caught {S}"`
- killed==0 and class sibling kills == 0 →
  `"no behavior-changing mutant landed in this test's class (corpus poverty)"`
- killed==K>0 → `"caught {K} mutants"`

### NFRs
- **NFR-001** (`adversary` package): stdlib-only imports preserved.
- **NFR-002**: All existing tests still green; new tests added.
- **NFR-003**: Reason strings deterministic (same runs → same strings); stable
  ordering maintained (dead-first, then alive, ties by test_id).

## Success Criteria
- **SC-001**: ≥3 new pure-fn tests (`tests/test_deadtests.py`) asserting `reason`
  correctness for: CASE A dead, CASE B dead, and an alive test — driven by
  synthetic class-kill maps (no subprocess).
- **SC-002**: ≥1 integration test that `run_deadtests` output JSON carries the
  mechanical `reason` + `class` field, monkeypatching `adversary.runner.run_mutant`,
  `adversary.sites.find_sites`, `DeterministicMutator`, AND
  `deadtests._baseline_test_ids` (the true non-pure deps are subprocess/pytest —
  NOT network; corrected from first draft).
- **SC-003**: full suite green (107 baseline + new); deadtests JSON on a
  synthetic two-class subject shows CASE A for one dead test, CASE B for
  another, and a clear confirmation for an alive test.
- **SC-004**: TDD observed — each new reason test written RED then GREEN.

## Review Result
STATUS: COMPLETE — round 1 FAIL deleg_06d0e24c (HIGH redesign toward
data-grounded class-region topology); round 2 PASS deleg_e8f84680 (no
HIGH/MED; 4 LOW: empty-classname fallback applied, junit dot-form note added,
CASE-A wording aligned, 107 count accepted). Ready to plan.