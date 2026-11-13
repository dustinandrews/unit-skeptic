# Adversary (Andy) — mutation-testing adversary design

## Goal
Given a codebase:
- A. Run tests. If green, continue.
- B. Andy (LLM adversary) injects a fault into source (NOT tests).
- C. Run tests. If fault caught → record, revert, go to B. If survived → potential test gap.

Output: surviving mutations = real test-suite blind spots, triaged for equivalence.

## Constraints
- Andy MUST NOT read the tests.
- Andy sandboxed (docker).
- Andy's goals must be aligned so it isn't driven to cheat.

## Design decisions (settled)
- **Andy never gets a shell.** It returns patches/snippets; the harness applies and runs them.
  → Blindness is *structural* (tests never enter its context), not just sandboxed.
- **Verdicts are mechanical**: mutant either fails ≥1 test, transpiles-fails, or survives. No LLM judges a pass/fail.
- **Everything committed to git in this repo**; results recorded for audit.

## Borrowable from LLMorpheus (MIT, cloned ~/projects/adversary/research/llmorpheus)
1. **PLACEHOLDER targeting** (src/generator/PromptSpecGenerator.ts): harness AST-locates candidate
   *sites* (if/while/do-while/for conditions, switch discriminants, call callee + args, loop headers),
   replaces the fragment with `<PLACEHOLDER>`, asks Andy for a replacement. Andy fills a blank —
   mutations always fit, context is bounded, tests never appear. Far better than free-form patch generation.
2. **Mechanical validity gate** (src/generator/MutantGenerator.ts): drop substitutions that are
   identical-to-original, syntactically invalid (babel parse; expand incomplete fragments to parent node),
   or duplicates (incl. containment). Tracks identical/invalid/duplicate counts.
3. **Ban-list = anti-cheat proxy**: blacklist substitutions containing node builtins/control
   (`process`, `require`, `setTimeout`, `setImmediate`, `delete`, `yield`, `async`, `await`, `let`,
   access modifiers, comments, unbalanced parens, invalid regex). Cheap guard against slip-in of
   I/O, side effects, hangs.
4. **Prompt asks for 3 fenced-block options + one-line "behavior changes because..." + "DONE." terminator**
   (templates/template-full.hb). Sets 3 mutants per site, cheaply. (Explanations discarded, but the
   format at least forces Andy to assert a behavior change — partial nod to equivalence.)
5. **Generation decoupled from execution**: LLM phase → mutants.json → runner phase (StrykerJS).
   Lets the dangerous run happen sandboxed, LLM fully out of the loop.
6. **Context trim**: >200-line snippet slices to ±100 lines around placeholder.
7. **Determinism/audit**: --replay for reproducibility; every prompt/completion written to disk;
   per-run dir `template_model_temp`; token-usage stats.

## Gaps LLMorpheus does NOT solve (our real work)
- **Equivalent survivors** (mutation that passes tests by not changing behavior) → the core cheat/noise
  problem. LLMorpheus reports survived but never filters equivalence.
- **Docker isolation** (LLMorpheus runs Stryker in-project; no sandbox).
- **Language**: JS/TS + Babel only. Ban-list is JS-specific.
- No feedback loop to Andy (it's stateless one-shot) — so no Andy-gaming; but also no adaptation.
  Open choice for us: stateless (like LLMorpheus) vs learning adversary.

## Open questions
- Deliverable framing: find test gaps for humans (mutation-adequacy) vs. do we need Andy to *also*
  suggest the missing test?
- Equivalence filter options: (a) human review of survivors, (b) differential output run on a
  property/smoke corpus, (c) LLM judge on survivors only (mechanical still for pass/fail).
- Sandbox runner: docker per-mutant with timeout + mem cap.
- Do we reuse StrykerJS/PIT execute phase, or write our own runner for arbitrary repos?
- How much Andy adaptivity (feedback) vs. stateless generator?
