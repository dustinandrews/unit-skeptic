# Feature Specification: LLM Andy Driver

**Branch**: `sprint-4-llm-andy`
**Created**: 2026-11-14
**Status**: Draft

## Purpose
Make the fault generator *realistic*, not just rule-based. Sprint 2's
`DeterministicMutator` proves the pipeline; Andy is a second `Mutator`
implementation behind the SAME adapter contract (`mutate(site) -> list[str]`)
that proposes faults an LLM believes a developer would actually introduce.
Swapped in via a CLI flag; everything downstream (splice, scratch-run,
mechanical verdict, score, survivors JSON, JEV triage) is untouched.

## Core design invariants (the "important to get right" part)

1. **Andy is a blind generator; the harness is the optimizer.** Andy's entire
   input is one site + its enclosing function (from subject source). It has NO
   access to tests, coverage, verdicts, or survivors — structurally: the
   harness never includes them in context, and there is no feedback loop even
   across runs (stateless one-shot per site).
2. **PLACEHOLDER-fill, bounded mutations.** The harness blanks the target site
   to `<PLACEHOLDER>` inside the enclosing function; Andy returns 1..N
   replacement strings. Each is spliced at the site by the harness exactly like
   a deterministic candidate. Every mutant stays atomic, splice-revert safe,
   mechanically verifiable.
3. **Goal alignment: no reward for survival.** The prompt asks "produce a
   realistic fault a developer might introduce at this region" — NEVER "foil
   the tests." Surviving isn't success; JEV triage (Sprint 3) labels
   equivalents and they are filtered downstream.
4. **Noise is absorbed by existing gates.** Non-compiling → parse-gate is
   already in the runner (`error`, excluded from denominator). Duplicates →
   dedupe in the mutator. Equivalents → JEV triage.

## User Scenarios *(mandatory)*

### User Story 1 - Engineer runs the score with realistic faults (P1)
Given a green codebase, an engineer runs the same score command they already
know, with one extra flag, and gets a score from LLM-proposed faults.

**Acceptance Scenarios:**
1. **Given** `adversary score --subject <dir> --mutator llm --model <id>`,
   **When** it runs, **Then** the A..C loop executes as today but mutation
   candidates come from Andy; the output includes the same lines (baseline
   green, sites, score, survivors path) plus which mutator/model ran.
2. **Given** the deterministic run (default) and an Andy run, **When** both
   complete, **Then** either may produce different verdict counts — the point
   is realism, not a fixed number.

### User Story 2 - Engineer can run Andy offline / in CI (P2)
CI and tests must not depend on a live LLM.

**Acceptance Scenarios:**
1. **Given** `--mutator llm --offline`, **When** the score runs, **Then** Andy
   is served by a deterministic scripted stub (no network, no key) returning
   canned replacement strings, so the pipeline is exercisable end-to-end.

## Functional Requirements
- **FR-001**: `LlmMutator` implements the existing `Mutator` Protocol
  (`mutate(site) -> list[str]`) unchanged; `scorer.run_loop` and `cli`
  require NO structural change beyond a `--mutator`/`--model` selection.
- **FR-002**: Andy's prompt input is built from subject source ONLY: the
  enclosing function (reusing the Sprint-3 A/B block builder extraction, minus
  the `<PLACEHOLDER>` blanking of the target region) — never tests, coverage,
  verdicts, or survivors.
- **FR-003**: Transport is an injectable `complete(prompt) -> str` seam (same
  pattern as the Sprint-3 JEV decision seam). Real implementation calls an
  OpenRouter chat-completions endpoint with a configurable `--model`; offline
  stub is deterministic. Key read indirectly (env/file), never a literal,
  never in prompts.
- **FR-004**: Candidates are deduped (identical strings within a site collapse
  to one), non-empty, and MUST differ from the site's original text (identity
  `mutated == source` is already skipped by the runner anyway).
- **FR-005**: CLI: `adversary score --subject <dir> [--mutator deterministic|llm]
  [--model <id>] [--trials-per-site <n>] [--offline]`. Default `--mutator
  deterministic` (backward compatible; no flag = today's behavior).
- **FR-006**: The score line gains `mutator=<name> model=<id>` so output is
  attributable; survivors JSON record gains `"mutator"` and `"model"` fields.
- **FR-007**: Subject is read-only; mutants materialize in the existing scratch
  shadow (runner already enforces; Andy never writes anything itself).
- **FR-008**: Reproducible with the offline stub (same input → same output);
  live-LLM runs are inherently non-deterministic and are NOT required to be
  byte-reproducible (documented).

## Non-Functional / Constraints
- **NFR-001**: No new third-party runtime deps: stdlib HTTP (urllib) behind
  the injected seam, mirroring the JEV adapter (no SDK).
- **NFR-002**: Cost-aware: default `--trials-per-site 1`; each candidate
  costs one LLM call + one suite run, so the default is ONE model call per
  site.
- **NFR-003**: CI stays offline: tests use the scripted stub only (no live
  LLM, no key).

## Success Criteria
- **SC-001**: `LlmMutator` is a `runtime_checkable` instance of the `Mutator`
  Protocol; `scorer.run_loop` drives it with zero changes.
- **SC-002**: With the offline stub, `adversary score --subject ../guineapig
  --mutator llm --offline` runs to completion and prints `mutator=llm`.
- **SC-003**: Blindness is structural: the prompt builder code path contains
  NO reference to test files, and a test asserts the prompt string never
  contains the word "test" in the tests-directory sense against a fixture.
- **SC-004**: `--mutator deterministic` with no other flags behaves byte-
  identically to today's output shape (backward compatible).
- **SC-005**: A live Andy run (verification note, not a gate) on guineapig
  produces a score and survivors; recorded as evidence. CI stays offline.

## Out of Scope (this sprint)
- Adaptive/chaining Andy (feedback from survivors into later prompts) —
  stateless one-shot only, by design.
- Multi-site whole-function mutations (PLACEHOLDER-fill is single-site by
  design; multi-site is future work).
- Docker sandboxing of Andy (the model has no shell by construction — it only
  returns strings through the seam; sandboxing becomes relevant when Andy gets
  a REPL, which it doesn't).
- Dead-test detection (Sprint 5).

## Review Result
STATUS: Draft — pending spec review.
