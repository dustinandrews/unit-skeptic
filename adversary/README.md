# unit-skeptic (internally: adversary)

**The test suite's adversary.** unit-skeptic measures how well a test suite
actually catches faults, not how many tests are green.

> **Status: rough but promising.** This is under active development. It works
> end-to-end on its own codebase and a small guinea-pig subject, but expect
> rough edges, API churn, and missing polish. Feedback and issues welcome.

## What it is

AI (and hasty human) development loves to ship "1235 tests green", but a green
count is theatre if the suite catches few *real* regressions. unit-skeptic
injects one realistic fault at a time into a clean, green codebase, runs the
suite, and reports:

- a **score** = fraction of injected faults the tests caught;
- a **machine-readable list of escaping faults** = the suite's actual blind spots;
- which tests catch nothing (**bad tests**).

A suite that scores 23% catches 23% of realistic faults, regardless of how many
green tests it has.

## It eats its own dog food

We ran unit-skeptic against **its own test suite**: the mutation target was
`andy.py` (the LLM fault generator), and the subject suite was unit-skeptic's
own tests. To read the numbers, three words matter:

- **caught** (a "good" test): at least one test failed while that fault was
  injected — the suite did its job.
- **escape** (a "bad" blind spot): no test failed; the fault slipped
  through. That is a missed bug.
- The **score** is the fraction of injected faults the tests caught:
  `caught / (caught + escapes)` (internally `killed / (killed + survived)`).
- The tool can generate faults two ways, and they are not equally demanding:
  - the **deterministic corpus** makes simple mechanical edits, flipping one
    operator or boolean at a time (e.g. `==` into `!=`, `and` into `or`);
  - the **live LLM corpus** ("Andy") asks a model to replace each code region
    with the kind of subtle, realistic change a developer might actually make,
    which tends to produce faults that are harder for a test suite to notice.
- The two corpora also differ in *how many* faults they inject, so the absolute
  scores are not directly comparable. The point is not one number vs the other;
  it is what the richer, more realistic corpus reveals about blind spots.

| corpus | valid faults injected | tests caught | score |
|--------|----------------------|--------------|-------|
| deterministic (simple operator flips) | 13 | 12 | 0.92 |
| live LLM (realistic code edits) | 78 | 41 | 0.53 |

Under the richer LLM corpus, **37 of 78** injected faults escaped — no test
failed while that fault was present. Two of the clearest blind spots:

- Flipping the transport's `"POST"` to `"GET"` **escaped**. The tests check
  that "the API key stays in the header", but never assert the HTTP method,
  encoding, timeout, or endpoint, so any of those could change and break a live
  call without tripping a test.
- An `and` → `or` regression in the reply parser's dedupe/fenced-fallback path
  **escaped**; duplicates, empty strings, and the snippet matching the
  original all leak through uncaught.

In plain terms: a suite showing 88 green tests still only caught about half of
the realistic faults we injected into its own code. That is the gap unit-skeptic
exists to surface, and it did exactly that to itself.

## Quick start

```bash
python -m adversary.cli score --subject /path/to/subject
```

Existing setup is Python 3.11+, stdlib-only (no runtime third-party deps). For
the live LLM corpus you additionally need an OpenRouter key (see below).

Subcommands: `score` | `equiv` | `deadtests`. Each takes `--subject <dir>`.

## Live LLM corpus ("Andy")

The default `DeterministicMutator` flips operators (`==`↔`!=`, `<`↔`>=`,
`and`↔`or`, …). For more realistic faults, the `--mutator llm` driver ("Andy") is
a blind, stateless LLM fault generator; its prompt is the enclosing function
with the target region blanked, drawn from subject source only (never tests,
coverage, verdicts, or survivors).

```bash
python -m adversary.cli score --subject /path/to/subject --mutator llm \
    --model openrouter/auto [--offline]
```

### Key configuration

Copy the example and fill in your key, or export it:

```bash
cp .env.example .env      # then edit .env
# or
export OPENROUTER_API_KEY=sk-or-...
```

The key travels **only** in the `Authorization` header, never in the prompt,
request body, or surviving-fault output. `.env` is gitignored; commit
`.env.example`, never `.env`.

## Score & verdicts

```
score = caught / (caught + escapes)
```

(Internally the records carry `killed`/`survived`; "caught" = `killed`,
"escapes" = `survived`.)

`error` (mutant didn't parse / couldn't run) and `timeout` are excluded from the
denominator; they are not valid faults. `score >= 0.8` is the acceptance
threshold.

| verdict | meaning |
|---------|---------|
| `killed` → **caught** | ≥1 test failed with this fault injected (a good test caught it) |
| `survived` → **escape** | all tests still passed; the fault slipped through (missed bug) |
| `error` | mutant invalid / un-runnable; excluded |
| `timeout` | suite exceeded wall clock; excluded |

## Scoring real, non-flat repos

By default `score` assumes a self-contained `src/` + `tests/` subject and runs
pytest with the tool's own interpreter. Real repos often don't fit that shape:
tests may live under `src/tests`, and the subject has its own virtualenv whose
compiled dependencies the tool's interpreter can't load. Three flags relax
those assumptions (each defaults to the current behavior):

```
python -m adversary.cli score --subject /path/to/subject \
    --src-rel src/email_router \   # dir under --subject holding source (default src)
    --tests-rel src/tests \        # dir under --subject holding tests (default tests)
    --python /path/to/venv/bin/python   # interpreter for pytest runs (default sys.executable)
```

Example (a real mail-summary service whose package lives at `src/email_router`
and whose tests live at `src/tests`): `score --subject <repo> --src-rel
src/email_router --tests-rel src/tests --python <repo>/venv/bin/python`.
`equiv` and `deadtests` accept the same flags they need (`--src-rel` on all
three; `--tests-rel`/`--python` additionally on `score` and `deadtests`, which
run the suite). Omit a flag to keep the corresponding default.

## More

- **`adversary equiv`**, cheap mechanical first-pass triage of escaped faults
  into `equivalent` / `killable` / `undecided` via two clean A/B code blocks to a
  JEV decision model (so equivalent-mutant false positives aren't charged to
  the score). Subject is read-only.
- **`adversary deadtests`**, flags tests that catch nothing ("bad tests";
  corpus-qualified: a test is `dead` under the *deterministic* corpus unless a
  richer LLM corpus would kill it).

See the per-command docs below for full usage.

---

*(The detailed design docs follow, sites/mutators/runner internals, the JEV
triage A/B block builder and decision bucketing, and dead-test semantics.)*

## The Mutator adapter (swappable)

The core contract is deliberately stable so both fault generators drive the same
loop:

- **Site** = `{module, start, end, text, kind}`, an atomic mutatable region
  (one operator / expression) with CHARACTER offsets into the module source;
  `text` is `source[start:end]`.
- **Replacement unit**, each candidate from `mutate(site)` is the full
  replacement text spliced at `[start, end)`: `source[:start] + repl + source[end:]`.
  One site at a time; never whole-file diffs.
- **Interface**, `mutator.mutate(site) -> list[str]`.

Shipped implementations:
- `DeterministicMutator` (rule-based operator flips: `==`↔`!=`, `<`↔`>=`,
  `<=`↔`>`, `and`↔`or`; whole-token matching, deterministic, zero LLM cost).
- `LlmMutator` ("Andy"), blind, stateless LLM fault generator behind the same
  Protocol, with an injectable transport seam (live OpenRouter via stdlib
  urllib, key header-only; deterministic offline stub keeps CI key/network-free).

## Survivor triage, JEV equivalence (`adversary equiv`)

Escaped faults are either **real blind spots** (tests don't catch a genuine
behavior change) or **equivalent mutants** (syntactically different,
behaviorally identical, false positives). `adversary equiv` gives every escape a
cheap mechanical first pass: build two clean A/B code blocks and ask the JEV
decision model (`typesafe/jev-1.14`) whether they are equivalent.

```bash
adversary equiv --subject /path/to/subject --survivors survivors.json \
    [--out triage.json] [--confidence-cutoff 0.7] [--offline]
```

Each escape gets `"label"` in {`equivalent`, `killable`, `undecided`} plus a
confidence in [0,1]. Subject source is read-only (never modified).

### A/B block builder (FR-002)

- Site **inside a function** → Function A is the enclosing `def`-with-body;
  Function B is the same function with the mutant `replacement` spliced at the
  *translated* offsets (`start - func_start`, `end - func_start`).
- Site at **module top level** → Function A is the enclosing statement block
  (or the whole module if none).

The two blocks are clean, self-contained code blocks, never a diff.

### Decision seam (FR-003) + buckets (FR-004)

Triage calls one injectable `decide(state, questions) -> normalized answers`.
The real implementation is a thin adapter over the reused
`triage-engine/src/jev/client.py` `JevClient` (imported lazily at the adapter
boundary only; the API key travels solely in the Authorization header, never in
state/questions/the body). Tests and `--offline` use a deterministic stub, no
live provider in CI.

Bucketing (single-source-of-truth thresholds in `adversary/equiv.py`):

- high-confidence `equivalent` → **equivalent**
- high-confidence `different` → **killable**
- low confidence (or no valid answer) → **undecided**, never forced into one
  of the other two, so a heavier partner model / human escalates only these.

`--confidence-cutoff` overrides the default `CONFIDENCE_CUTOFF` (0.7).

## Dead-test detection (`adversary deadtests`)

Flags tests that never catch a bug. A test's **kill count** = how many
behavior-changing mutants (parsed, `killed`) it failed on across the corpus.
A test with kill count 0 is **bad** (catches nothing).

```bash
adversary deadtests --subject /path/to/subject [--out dead-tests.json]
```

Output is a corpus-qualified JSON doc: top-level `"corpus": "deterministic"`
makes the label's scope explicit, a `dead` test here failed on zero
*deterministic* mutants, NOT a claim it catches no fault under a richer (LLM)
corpus. Total/dead/alive counts plus per-test `{test_id, kills, status}`
(dead first, stable order). Error/timeout mutants do not attribute (their
failures are noise, matching the score denominator). Subject is read-only.

## Modules

- `sites.py`, AST site enumeration (`Compare`, `BoolOp`, call args, constants)
  with exact character offsets.
- `mutators.py`, `Mutator` Protocol + `DeterministicMutator`.
- `runner.py`, green-gate oracle + per-mutant pytest run from a scratch shadow
  dir (the real repo is **never** modified; package `__init__.py` files are
  mirrored into the shadow so mutants actually load). Verdicts are mechanical.
- `scorer.py`, loop, score formula, survivors JSON.
- `equiv.py`, JEV equivalence triage: A/B block builder, decision seam,
  confidence bucketing, triage driver.
- `andy.py`, `LlmMutator`: blind LLM fault generator + transport seam (live
  OpenRouter / offline stub) + prompt builder / reply parser.
- `deadtests.py`, pure kill-aggregation + the `run_deadtests` driver.
- `cli.py`, `adversary score | equiv | deadtests --subject <dir> ...`.

## Dev

```bash
.venv/bin/python -m pytest -q -p no:cacheprovider   # 114 tests
```
