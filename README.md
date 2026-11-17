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

We ran unit-skeptic against **its own test suite** (mutation target: `andy.py`,
the LLM fault generator). The deterministic corpus scored **0.923**; the live
LLM corpus scored **0.526**, and the survivors exposed real gaps:

- Flipping the transport's `"POST"` to `"GET"` **survived**, the tests guard
  "API key stays in the header" but never check the HTTP method, encoding,
  timeout, or endpoint. Every one of those would genuinely break a live call.
- An `and` → `or` regression in the reply parser's dedupe/fenced-fallback path
  **survived**; dupes, empties, and the original snippet leak through
  uncaught.

The tool found its own test suite was weaker than its 88-green count suggested.
That is exactly the job it does for you.

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
