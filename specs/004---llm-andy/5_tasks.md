# Tasks — LLM Andy Driver

- [x] T001 `andy.build_prompt`: subject-source-only prompt, target region blanked
      to `<PLACEHOLDER>`, enclosing function included (reuse `equiv.build_blocks`).
- [x] T002 `andy.parse_reply`: extract `<snippet>`/fenced candidates; dedupe,
      drop empty + identity (FR-004).
- [x] T003 transport seam: `real_complete` (OpenRouter, stdlib urllib, key in
      header only), `offline_complete` (deterministic stub), injectable `http_post`.
- [x] T004 `LlmMutator`: Protocol-conformant `mutate(site)`; injected source +
      `complete`/`model`/`trials`.
- [x] T005 `scorer.run_loop` `record_attrs` (survivors gain `mutator`/`model`).
- [x] T006 CLI: `--mutator | --model | --trials-per-site | --offline`; score line
      + JSON attribution; default deterministic (FR-005/FR-006).
- [x] T007 tests: blindness (SC-003), parse, mutator (SC-001), offline
      reproducibility (FR-008), key hygiene (FR-003), CLI end-to-end (SC-002).
- [x] T008 verify: 76 tests green; offline guineapig run; deterministic
      backward-compat unchanged.
- [x] T009 doc: PRODUCT_PLAN.md + TECH_STACK.md updated; commit on
      `sprint-4-llm-andy`.
