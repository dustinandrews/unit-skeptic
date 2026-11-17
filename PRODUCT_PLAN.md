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

### Sprint 4: LLM "Andy" driver
- `adversary/andy.py`: `LlmMutator`, second `Mutator` behind the same
  `mutate(site) -> list[str]` contract, so `scorer.run_loop` is untouched. Blind
  one-shot per site: prompt = enclosing function with target region blanked to
  `<PLACEHOLDER>` (subject source only, reusing Sprint-3 block builder); never
  tests/coverage/verdicts/survivors.
- Injectable `complete(prompt) -> str` seam: OpenRouter via stdlib urllib
  (configurable `--model`, key in header only), deterministic offline stub for
  CI. CLI `--mutator llm [--model --trials-per-site --offline]`; default stays
  deterministic (backward compatible). Survivors + score line carry
  `mutator`/`model`.
- Verified: 77 tests green. Offline end-to-end on guineapig prints
  `mutator=llm model=openrouter/auto` and runs the full A→C loop; deterministic
  run unchanged (score 1.000, 17 killed, 0 survived).

### Sprint 5: Dead-test detection
- `adversary deadtests --subject <dir> [--out <file>]`: per-test kill
  attribution via pytest `--junitxml` + stdlib XML parse (error/timeout not
  attributed, matching the score denominator). Extends `runner.run_mutant` with
  an optional absolute `junit_path` (parsed before scratch cleanup; default
  keeps the verdict-string contract). Output = corpus-qualified JSON
  (`"corpus": "deterministic"`, `dead` = zero kills in this corpus, not a
  global claim).
- Verified: 88 tests green. On guineapig: all 4 deliberate weak tests dead,
  20 of 29 strong tests kill ≥ 1 mutant (the other 9 assert constants /
  rejection paths the operator-only corpus cannot reach, correct
  corpus-scoped behavior, flagged honestly by the qualifier).
- Cross-sprint value: the tool caught what a naive "dead = not needed" reading
  would miss, corpus scope matters; a test that never fails under
  operator flips may still be a real guard against LLM/constant faults.

## Next (ordered)
Sprint 6 ACTIVE: **fix Andy's own test gaps** the live-LLM dogfood exposed
([2026-11-18 agreed]): add transport assertions (HTTP method, encoding, timeout,
endpoint) to `test_real_complete_*` and the parser dedupe/fenced-fallback tests
for `andy.parse_reply`, using the recorded live-corpus survivors as the proof.
Goal: drive the instrument's self-score back up and close the concrete blind
spots the tool itself found.

Parked after Sprint 6 (ordered):
- Dead-test *explanation* (why a test is dead: tautology vs unreachable
  corpus). Design decided ([2026-11-18]): verdict + raw reason are MECHANICAL
  (summarize already-collected kill data: which sites/operators a dead test
  never covered) with NO LLM; an LLM is used only as a narrow, targeted
  explainer for ambiguous cases (convert "missed operators at lines A–B" into
  plain-language prose). Avoids an LLM broadly judging tests it never ran.
- LLM/Andy corpus for dead-tests (richer faults would clear the 9
  constant-asserting tests).
- Real-repo pilot (run the instrument against a larger live codebase).
