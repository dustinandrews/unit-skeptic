# Product plan

Keep bite-size items; sub-divide if too complex. Max five future items.

## Mission
Kill "test theatre": score how well a test suite catches realistic faults (LLM
adversary "Andy" injects faults into a green codebase; score = caught fraction;
surviving faults = the actionable gap list; dead tests = detectable noise).

## Done
### Sprint 1: guineapig
- Guinea-pig toy: pure-Python pricing package (5 functions), strong boundary suite
  (33 tests, 100% coverage) + deliberate 4-test weak cohort as Phase-2 ground truth.

### Sprint 2: score instrument MVP
- Deterministic-mutator score instrument (`adversary` package): AST site finder,
  `Mutator` adapter + `DeterministicMutator`, scratch-dir shadowing (repo never
  modified; package `__init__.py` mirrored so mutants actually load), mechanical
  verdicts (killed/survived/error/timeout), score = killed/(killed+survived),
  survivors JSON. CLI: `adversary score --subject <dir>`.
- Verified on guineapig: score **1.000** (17 killed, 0 survived), reproducible,
  repo untouched. 33 instrument tests green. `LlmMutator` slots into the same
  Mutator contract unchanged.

### Sprint 3: JEV equivalence triage
- `adversary equiv` triages surviving faults: builds A/B code blocks (enclosing
  function, original vs mutant-spliced), asks JEV (`typesafe/jev-1.14`) whether
  they're behaviorally equivalent (injectable seam reusing triage-engine
  JevClient; offline stub for CI), buckets each survivor `equivalent | killable
  | undecided` by confidence, emits triage JSON. Reproducible, read-only on the
  subject.
- Verified: 56 tests green; offline triage on the spike's verification subject
  labels all survivors correctly, reproducible, repo untouched. JEV accuracy
  de-risked by spike (12/12 exact incl. half-penny edge).

## Next (ordered)
1. Sprint 4 — LLM "Andy" driver (swappable, stateless) producing richer faults,
   blind to tests, sandboxed; lands after equivalence triage so its noisy
   survivor flood is filterable.
2. Sprint 5 — Dead-test detection (Phase 2): flag tests that never kill a fault.
