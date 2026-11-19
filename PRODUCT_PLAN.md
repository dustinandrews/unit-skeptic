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

### Sprint 6: Andy self-test hardening
- Ran the live-LLM Andy mutator against the tool's own `andy.py` (dogfood):
  score **0.526** (41 killed / 37 survived / 4 error) vs deterministic 0.923 —
  the richer corpus exposed real transport blind spots.
- Hardened the suite (test-side only, no source changes): 4 new tests kill the
  surviving mutations G1 (HTTP verb `"POST"`→`"GET"`), G3 (timeout 60→0), G4
  (endpoint swap), G5 (fenced-fallback dedupe `and`→`or`); plus FR-002
  `Content-Type: application/json` + body round-trip assertion. Transport
  internals verified by patching `andy.urllib.request.urlopen` (verb/timeout
  live inside `_http_post`, invisible to the injected-fake seam).
- Finding: G2 (`body.encode("utf-8")`→`"ascii"`) is an **EQUIVALENT mutant**
  under `json.dumps(ensure_ascii=True)` — byte-identical output, no test can
  kill it; documented, not a test gap (what `adversary equiv` triage is for).
- Verified: **92 tests green** (88 + 4); deterministic self-score 0.923 → 0.929
  (13 killed vs 12; remaining survivor = `.env` loader `key and ... not in
  os.environ` `and`→`or` — new gap outside this sprint's kill set, recorded
  for follow-up).

### Sprint 7: Repo-flexible subjects
- Real-repo pilot on `~/projects/AIEmailSummary` (user-suggested, [2026-11-18]):
  full suite **303 green**, but `score` couldn't run it — three rigid
  assumptions (tests at `<subject>/tests`, own `sys.executable`, first module
  under `<subject>/src`) fit only self-contained toy subjects.
- Added explicit flags (defaults preserve every prior behavior): `--src-rel`
  (source dir under `--subject`, default `src`), `--tests-rel` (suite dir,
  default `tests`), `--python` (interpreter for pytest subprocesses, default
  `sys.executable`). Threaded through `runner`, `scorer` (caller-owned closure,
  signature unchanged), `cli`, and `deadtests` (incl. its baseline id
  enumeration). Non-default `--python` is recorded as `attrs.python` in
  survivors.json for reproducibility. Error strings interpolate the effective
  `src_rel`.
- Verified: **100 tests green** (92 + 8 new, incl. a nested-`src/tests`
  synthetic subject and a captured-subprocess `--python` check); default-flag
  guineapig run bit-identical (73 sites, score 1.000).

## Next (ordered)
Sprint 8 candidates (parked, none active):
- Dead-test *explanation* (why a test is dead: tautology vs unreachable
  corpus). Design decided ([2026-11-18]): verdict + raw reason are MECHANICAL
  (summarize already-collected kill data: which sites/operators a dead test
  never covered) with NO LLM; an LLM is used only as a narrow, targeted
  explainer for ambiguous cases (convert "missed operators at lines A–B" into
  plain-language prose). Avoids an LLM broadly judging tests it never ran.
- LLM/Andy corpus for dead-tests (richer faults would clear the 9
  constant-asserting tests).
- Score the AIEmailSummary suite end-to-end with the Sprint 7 flags (the pilot
  now has the tool flexibility to run it; exercise a real large repo).
- New `.env`-loader survivor revealed in S6 dogfood (`key and ... not in
  os.environ` `and`→`or` would break "export wins over .env") — test-side fix
  for the tool's own suite.
