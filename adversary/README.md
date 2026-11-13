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

The core contract is deliberately stable so a future LLM "Andy" driver slots in
without an interface change:

- **Site** = `{module, start, end, text, kind}` — an atomic mutatable region
  (one operator / expression) with CHARACTER offsets into the module source;
  `text` is `source[start:end]`.
- **Replacement unit** — each candidate from `mutate(site)` is the full
  replacement text spliced at `[start, end)`: `source[:start] + repl + source[end:]`.
  One site at a time; never whole-file diffs.
- **Interface** — `mutator.mutate(site) -> list[str]`.

Shipped implementation: `DeterministicMutator` (rule-based operator flips:
`==`↔`!=`, `<`↔`>=`, `<=`↔`>`, `and`↔`or`; whole-token matching, deterministic,
zero LLM cost). An `LlmMutator` implements the same Protocol unchanged.

## Modules

- `sites.py` — AST site enumeration (`Compare`, `BoolOp`, call args, constants)
  with exact character offsets.
- `mutators.py` — `Mutator` Protocol + `DeterministicMutator`.
- `runner.py` — green-gate oracle + per-mutant pytest run from a scratch shadow
  dir (the real repo is **never** modified; package `__init__.py` files are
  mirrored into the shadow so mutants actually load). Verdicts are mechanical.
- `scorer.py` — loop, score formula, survivors JSON.
- `cli.py` — `adversary score --subject <dir>`.

## Verdict taxonomy

- `killed` — at least one test failed with this fault injected (good).
- `survived` — all tests still passed (test-suite blind spot).
- `error` — the mutant did not parse / could not run; excluded.
- `timeout` — the suite exceeded the wall clock; excluded.

## Dev

```bash
.venv/bin/python -m pytest -q -p no:cacheprovider   # 33 tests
```
