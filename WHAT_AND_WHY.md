# WHAT_AND_WHY.md

## PURPOSE
- Why does this project exist?
  To kill "test theatre": AI (or hasty) development proudly ships suites with many
  green tests (e.g. "1235 passed") that catch few real regressions. Coverage and
  green-count inflate confidence while actual regressions slip through.
- Who will use it?
  Engineers and AI-pipeline builders who want an honest measure of whether their
  test suite catches realistic faults — and which tests are worth keeping.
- Is it an MVP or V2?
  MVP. Phase 1 = the score. Phase 2 = dead-test detection + surviving-fault cleanup.

## Core Idea
An LLM adversary ("Andy") injects realistic faults into a clean, green codebase.
The suite score = the fraction of injected faults the tests catch. A suite that
catches 23% of realistic faults is weak regardless of how many green tests it has.

## Example End User Scenario
A team's AI agent reports "all 1235 tests green." Before trusting that, the engineer
runs Adversary. It injects 100 realistic faults; only 23 fail a test. The suite is
predictably blind to 77 real regressions — the green count was theatre.

## What Success Looks Like (Phase 1)
Given a green Python codebase, Adversary produces a calibrated, reproducible score:
"this suite catches X% of injected realistic faults," plus the list of surviving
faults as the actionable gap list — all without modifying the real repo, with Andy
blind to the tests.

## Out of Scope for MVP
- Language generality (Python only for MVP)
- Autonomous test-writing (report gaps; human fixes)
- Adaptive learning adversary (stateless sampler first)
- Docker sandboxing of the runner (local pytest subprocess first; isolation later)

## Status
Scaffolded from sprint project template. First sprint is the test-score instrument.
