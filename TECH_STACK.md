# Tech Stack, Adversary

## Language
- Python 3.12+ (`requires-python = ">=3.12"`)

## Guinea-pig subject (sprint 1)
- `guineapig/`: pure-Python pricing package (5 functions), stdlib + pytest only.
- Test suite: 33 tests (29 boundary + 4 deliberate weak), 100% line coverage, < 2s.

## Equivalence triage (sprint 3, shipped)
- `adversary equiv`: A/B block builder (enclosing function, both in-function and
  top-level-site cases, translated offsets), injectable decision seam (real
  adapter wraps triage-engine `src/jev/client.py` JevClient; deterministic
  offline stub for CI), 3-bucket confidence bucketing (equivalent/killable/
  undecided), triage JSON output. Reads survivors JSON + subject source only.

## Dead-test detection (sprint 5, shipped)
- `adversary deadtests --subject <dir> [--out <file>]`: per-test kill
  attribution via pytest `--junitxml` + `xml.etree` (stdlib). `runner.run_mutant`
  gained optional absolute `junit_path` (parses failing nodeids before scratch
  cleanup; default keeps verdict-string contract); env sets
  `PYTHONDONTWRITEBYTECODE=1`. Output = corpus-qualified JSON via
  `deadtests.py` pure fns (`aggregate_kills`/`classify`/`build_output`).

## LLM Andy driver (sprint 4, shipped)
- `adversary/andy.py`: `LlmMutator`, second `Mutator` implementation behind the
  same adapter contract (`mutate(site) -> list[str]`), driving `scorer.run_loop`
  with zero structural change. Blind by design: prompt built from subject source
  ONLY (enclosing function, target region blanked to `<PLACEHOLDER>` via the
  Sprint-3 `equiv.build_blocks` extraction); tests/coverage/verdicts/survivors
  never appear.
- Injectable `complete(prompt) -> str` transport seam: real impl calls the
  OpenRouter chat-completions endpoint via stdlib urllib (no SDK, NFR-001); key
  read from env, travels only in the Authorization header (FR-003). Deterministic
  scripted offline stub for CI (NFR-003). Candidates deduped/non-empty/must-differ
  (FR-004).
- CLI: `adversary score --subject <dir> [--mutator deterministic|llm]
  [--model <id>] [--trials-per-site <n>] [--offline]`. Default `deterministic`
  is backward compatible. Survivors JSON + score line gain `mutator`/`model`
  (FR-006).

## Score instrument (sprint 2, shipped)
- `adversary/`: standalone package (own pyproject + venv). Modules: `sites.py`
  (AST site finder with char offsets), `mutators.py` (`Mutator` Protocol +
  `DeterministicMutator`), `runner.py` (green gate + scratch pytest shadow),
  `scorer.py` (score + survivors JSON), `cli.py`.
- Deterministic operator mutator first; LLM "Andy" driver slots into the same
  `Mutator` contract later.
- Mechanical verdicts (killed/survived/error/timeout), no model judgment of pass/fail.
- Scratch-dir mutation isolation, real repo never modified; package `__init__.py`
  mirrored into the shadow so mutants actually load. Local pytest subprocess
  (docker sandbox deferred, sprint 3+).

## Self-test hardening (sprint 6, shipped)
- Live-LLM dogfood of `andy.py`: score 0.526 (41 killed / 37 survived / 4 error)
  vs deterministic 0.923 — richer corpus exposed real transport blind spots.
- Test-side only (no source changes): 4 new tests in `tests/test_andy.py` kill
  G1 (verb `"POST"`→`"GET"`), G3 (timeout 60→0), G4 (endpoint swap), G5
  (fenced-fallback dedupe `and`→`or`); plus FR-002 `Content-Type` + body
  round-trip assertion. Verb/timeout verified by patching
  `andy.urllib.request.urlopen` (they live inside `_http_post`, invisible to
  the injected-fake seam).
- G2 (`encode("utf-8")`→`"ascii"`) = EQUIVALENT under `json.dumps(ensure_ascii=True)`;
  documented, not killable (byte-identical output).
- 92 tests green; deterministic self-score 0.923 → 0.929 (13/14 kills; the one
  survivor = `.env` loader `and`→`or`, new gap for follow-up; now 100 after
  Sprint 7's flag tests).

## Repo flexibility (sprint 7, shipped)
- `score`/`equiv`/`deadtests` gain `--src-rel` (default `src`); `score` and
  `deadtests` also gain `--tests-rel` (default `tests`) and `--python`
  (interpreter for pytest subprocesses, default `sys.executable`). Defaults
  preserve all prior behavior; flags let real repos (tests under `src/tests`,
  own venv python) be scored. `--python` non-default is recorded as
  `attrs.python` in survivors.json. All plumbing; no change to mutation or
  scoring semantics. 101 tests green.

## Real-repo scoring, runner shadowing fix, vocabulary (post-S7)
- AIEmailSummary scored end-to-end: **0.846** (11 caught / 2 escapes) on 310
  green tests; `--src-rel src/email_router --tests-rel src/tests --python
  <venv>/bin/python`.
- Runner shadowing fix (`ee84314`): minimal PYTHONPATH shadows never loaded
  mutants in src-layout repos (pytest force-prepends `subject/src`); runner now
  mirrors the whole subject tree into scratch + runs pytest cwd=scratch so
  mutants actually load. 104 tests green.
- Human-facing vocabulary (user-directed): **caught / escape / good / bad**
  tests (was killed / survived / dead). Internal JSON tokens unchanged.

## Dependencies
- Guinea-pig: none beyond stdlib + pytest.
- Instrument: stdlib (AST, subprocess, tempfile, json) + pytest for dev.

## Process
- Short-sprint method (`~/projects/.SPRINT_METHOD.md`), 10 gates, specs/ artifacts.
