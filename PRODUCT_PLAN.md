# Product plan

Keep bite-size items; sub-divide if too complex. Max five future items.

## Mission
Kill "test theatre": score how well a test suite catches realistic faults (LLM
adversary "Andy" injects faults into a green codebase; score = caught fraction;
surviving faults = the actionable gap list; dead tests = detectable noise).

## Done (sprint 1: guineapig)
- Guinea-pig toy: pure-Python pricing package (5 functions), strong boundary suite
  (33 tests, 100% coverage) + deliberate 4-test weak cohort as Phase-2 ground truth.

## Next (ordered)
1. Sprint 2 — Score instrument MVP: deterministic mutator → mechanical verdicts →
   score + surviving-fault list against guineapig (zero-LLM, reproducible).
2. Sprint 3 — LLM Andy driver (swappable, stateless) producing richer faults.
3. Sprint 4 — Equivalence triage on survivors (the real work beyond LLMorpheus).
4. Sprint 5 — Dead-test detection (Phase 2): flag tests that never kill a fault.
