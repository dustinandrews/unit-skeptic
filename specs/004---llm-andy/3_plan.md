# Implementation Plan — LLM Andy Driver

## Approach
Add `adversary/andy.py` as a second `Mutator` behind the existing
`mutate(site) -> list[str]` contract so `scorer.run_loop` is structurally
unchanged. Andy's prompt is built from subject source ONLY (enclosing function
with the target region blanked to `<PLACEHOLDER>`, reusing Sprint-3
`equiv.build_blocks`), keeping the model blind to tests/coverage/verdicts.
Transport is an injectable `complete(prompt) -> str` seam (real = OpenRouter via
stdlib urllib; offline = deterministic scripted stub for CI). Wire CLI flags;
default stays deterministic (backward compatible); attribute output with
`mutator`/`model`.

## Steps
1. `andy.py`: `build_prompt` (subject-source-only, PLACEHOLDER blanking),
   `parse_reply` (tag/fence extract, dedupe, non-empty, != orig), transport seam
   (`real_complete` OpenRouter, key in header only; `offline_complete`
   deterministic), `LlmMutator` (Protocol-conformant).
2. `scorer.run_loop`: add `record_attrs` so survivors gain `mutator`/`model`
   (backward compatible, optional).
3. `cli.run_score` + args: `--mutator deterministic|llm --model --trials-per-site
   --offline`; score line/JSON attribution.
4. Tests: `test_andy.py` (prompt blindness SC-003, parse, mutator SC-001,
   offline reproducibility FR-008, key hygiene, CLI SC-002/SC-004).
5. Verify: full suite green; offline end-to-end on guineapig; deterministic
   backward-compat unchanged.
6. Update PRODUCT_PLAN.md + TECH_STACK.md; commit.

## Risks / decisions
- Offline stub routes on the enclosing-function marker present in the prompt
  (region is blanked, so the original token is not available to the stub);
  non-compiling canned candidates absorb into the existing parse-gate `error`
  verdict — by design.
- `SC-004` (byte-identical default): the deterministic path computes identical
  score/verdicts; the score line gains a `mutator=` attribution per FR-006.
