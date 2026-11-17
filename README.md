# unit-skeptic (internally: adversary)

**The test suite's adversary.** unit-skeptic measures how well a test suite
actually catches faults, not how many tests are green.

> **Status: rough but promising.** Under active development. It works
> end-to-end on its own codebase and a small guinea-pig subject, but expect
> rough edges, API churn, and missing polish. Feedback and issues welcome.

## What it is

AI (and hasty human) development loves to ship "1235 tests green", but a green
count is theatre if the suite catches few *real* regressions. unit-skeptic
injects one realistic fault at a time into a clean, green codebase, runs the
suite, and reports:

- a **score** = fraction of injected faults the tests caught;
- a **machine-readable list of surviving faults** = the suite's actual blind spots;
- which tests never kill any fault (**dead tests**).

A suite that scores 23% catches 23% of realistic faults, regardless of how many
green tests it has.

## It eats its own dog food

We ran unit-skeptic against **its own test suite**: the mutation target was
`andy.py` (the LLM fault generator), and the subject suite was unit-skeptic's
own tests. To read the numbers, two things matter:

- The **score is the fraction of injected faults the tests caught**:
  `killed / (killed + survived)`. "Killed" means at least one test failed with
  that fault in; "survived" means every test still passed.
- The two fault corpora differ in *how many* faults they inject, so the
  absolute scores are not directly comparable. The point is not one number vs
  the other; it is what a richer, realistic fault set reveals.

| corpus | valid faults injected | tests caught | score |
|--------|----------------------|--------------|-------|
| deterministic (operator flips) | 13 | 12 | 0.92 |
| live LLM (realistic faults) | 78 | 41 | 0.53 |

Under the richer LLM corpus, **37 of 78** injected faults survived, meaning no
test failed while that fault was present. Two of the clearest blind spots:

- Flipping the transport's `"POST"` to `"GET"` **survived**. The tests check
  that "the API key stays in the header", but never assert the HTTP method,
  encoding, timeout, or endpoint, so any of those could change and break a live
  call without tripping a test.
- An `and` → `or` regression in the reply parser's dedupe/fenced-fallback path
  **survived**; duplicates, empty strings, and the snippet matching the
  original all leak through uncaught.

In plain terms: a suite showing 88 green tests still only caught about half of
the realistic faults we injected into its own code. That is the gap unit-skeptic
exists to surface, and it did exactly that to itself.

## Quick start

The package lives in `adversary/`:

```bash
cd adversary
python -m adversary.cli score --subject /path/to/subject
```

Subcommands: `score` | `equiv` | `deadtests`, each takes `--subject <dir>`.
For the live LLM fault corpus, `--mutator llm` uses an OpenRouter key (see
`adversary/.env.example`; the key travels only in the Authorization header and
`.env` is gitignored). Existing setup is Python 3.11+, stdlib-only.

## Layout

- `adversary/`, the tool: CLI + mutators + runner, its own full test suite (88).
- `guineapig/`, a deliberately weak subject with known "test theatre".
- `research/`, spike/prototype notes.
- `specs/`, sprint specs and review history (how the frontier was built).

## Full docs

See [adversary/README.md](adversary/README.md) for subcommand reference, the
mutation/adapter design, survivor JEV triage, dead-test semantics, and verdict
taxonomy.
