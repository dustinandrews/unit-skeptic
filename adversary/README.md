# Adversary — score instrument

Measures how well a test suite catches realistic faults. For a green Python
codebase it enumerates mutation sites, injects one fault at a time, runs the
suite, and reports a **score** = caught fraction, plus a machine-readable list
of surviving faults (the test-suite's blind spots).

## Quick start

```bash
python -m adversary.cli score --subject /path/to/subject
```

Example against the guinea-pig subject:

```
A: baseline green in 0.14s
B: 73 sites
score = 1.000  (killed=17, survived=0, error=0, timeout=0)
survivors written to survivors.json
```

`score = killed / (killed + survived)`; `error` and `timeout` verdicts are
excluded from the denominator (they are not valid faults). `score >= 0.8` is
the acceptance threshold.

## The Mutator adapter (swappable)

The core contract is deliberately stable so both fault generators drive the same
loop:

- **Site** = `{module, start, end, text, kind}` — an atomic mutatable region
  (one operator / expression) with CHARACTER offsets into the module source;
  `text` is `source[start:end]`.
- **Replacement unit** — each candidate from `mutate(site)` is the full
  replacement text spliced at `[start, end)`: `source[:start] + repl + source[end:]`.
  One site at a time; never whole-file diffs.
- **Interface** — `mutator.mutate(site) -> list[str]`.

Shipped implementations:
- `DeterministicMutator` (rule-based operator flips: `==`↔`!=`, `<`↔`>=`,
  `<=`↔`>`, `and`↔`or`; whole-token matching, deterministic, zero LLM cost).
- `LlmMutator` ("Andy", `adversary score --mutator llm --offline`) — blind,
  stateless LLM fault generator behind the same Protocol. Its prompt is the
  enclosing function with the site blanked to `<PLACEHOLDER>` (subject source
  only — never tests/coverage/verdicts), it returns 1..N replacement snippets,
  and the transport is an injectable seam (live OpenRouter via stdlib urllib,
  key header-only; deterministic offline stub keeps CI key/network-free).

## Survivor triage — JEV equivalence (`adversary equiv`)

Surviving faults are either **real blind spots** (tests don't catch a genuine
behavior change) or **equivalent mutants** (syntactically different,
behaviorally identical — false positives). `adversary equiv` gives every
survivor a cheap mechanical first pass: build two clean A/B code blocks and ask
the JEV decision model (`typesafe/jev-1.14`) whether they are equivalent.

```bash
adversary equiv --subject /path/to/subject --survivors survivors.json \
    [--out triage.json] [--confidence-cutoff 0.7] [--offline]
```

Each survivor gets `"label"` in {`equivalent`, `killable`, `undecided`} plus a
confidence in [0,1]. Subject source is read-only (never modified).

### A/B block builder (FR-002)

- Site **inside a function** → Function A is the enclosing `def`-with-body;
  Function B is the same function with the mutant `replacement` spliced at the
  *translated* offsets (`start - func_start`, `end - func_start`).
- Site at **module top level** → Function A is the enclosing statement block
  (or the whole module if none).

The two blocks are clean, self-contained code blocks — never a diff.

### Decision seam (FR-003) + buckets (FR-004)

Triage calls one injectable `decide(state, questions) -> normalized answers`.
The real implementation is a thin adapter over the reused
`triage-engine/src/jev/client.py` `JevClient` (imported lazily at the adapter
boundary only; the API key travels solely in the Authorization header, never in
state/questions/the body). Tests and `--offline` use a deterministic stub — no
live provider in CI.

Bucketing (single-source-of-truth thresholds in `adversary/equiv.py`):

- high-confidence `equivalent` → **equivalent**
- high-confidence `different` → **killable**
- low confidence (or no valid answer) → **undecided** — never forced into one
  of the other two, so a heavier partner model / human escalates only these.

`--confidence-cutoff` overrides the default `CONFIDENCE_CUTOFF` (0.7).

## Dead-test detection (`adversary deadtests`)

Flags tests that never kill a fault. A test's **kill count** = how many
behavior-changing mutants (parsed, `killed`) it failed on across the corpus.
A test with kill count 0 is **dead**.

```bash
adversary deadtests --subject /path/to/subject [--out dead-tests.json]
```

Output is a corpus-qualified JSON doc: top-level `"corpus": "deterministic"`
makes the label's scope explicit — a `dead` test here failed on zero
*deterministic* mutants, NOT a claim it catches no fault under a richer (LLM)
corpus. Total/dead/alive counts plus per-test `{test_id, kills, status}`
(dead first, stable order). Error/timeout mutants do not attribute (their
failures are noise, matching the score denominator). Subject is read-only.

## Modules

- `sites.py` — AST site enumeration (`Compare`, `BoolOp`, call args, constants)
  with exact character offsets.
- `mutators.py` — `Mutator` Protocol + `DeterministicMutator`.
- `runner.py` — green-gate oracle + per-mutant pytest run from a scratch shadow
  dir (the real repo is **never** modified; package `__init__.py` files are
  mirrored into the shadow so mutants actually load). Verdicts are mechanical.
- `scorer.py` — loop, score formula, survivors JSON.
- `equiv.py` — JEV equivalence triage: A/B block builder, decision seam,
  confidence bucketing, triage driver.
- `andy.py` — `LlmMutator` (Sprint 4): blind LLM fault generator + transport
  seam (live OpenRouter / offline stub) + prompt builder / reply parser.
- `deadtests.py` — pure kill-aggregation + the `run_deadtests` driver (Sprint 5).
- `cli.py` — `adversary score | equiv | deadtests --subject <dir> ...`.

## Verdict taxonomy

- `killed` — at least one test failed with this fault injected (good).
- `survived` — all tests still passed (test-suite blind spot).
- `error` — the mutant did not parse / could not run; excluded.
- `timeout` — the suite exceeded the wall clock; excluded.

## Dev

```bash
.venv/bin/python -m pytest -q -p no:cacheprovider   # 88 tests
```
