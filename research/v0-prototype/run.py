#!/usr/bin/env python3
"""Adversary harness — the A/B/C loop.

A. baseline: run oracle tests -> if not green, abort.
B. Andy mutates a site (source only, never tests).
C. run oracle against mutant -> mechanical verdict -> record -> revert.

Mechanical verdicts (no model judgment):
  killed   mutant applied, >=1 test failed, no error/timeout
  survived all tests passed, mutant still valid Python
  error    mutant applied but tests errored / import broke
  invalid  mutant rejected pre-run (identical, dupe, syntax)
  timeout  test run exceeded wall limit

Pure-file inside mutation: NOT allowed. Real repo is never modified; each
mutant materializes in a scratch dir shadowing src/ on PYTHONPATH.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time

import subject
import site_target
from andy import DeterministicAndy

SCRATCH = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".scratch")
RESULT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
TIMEOUT_S = 30


def apply_mutant(source, start, end, snippet):
    """Return mutated full source with *snippet* substituted at [start,end)."""
    return source[:start] + snippet + source[end:]


def is_valid_python(source):
    try:
        compile(source, "<mutant>", "exec")
        return True
    except SyntaxError:
        return False


def run_oracle(mutdir):
    """Run oracle pytest against src shadowed by mutdir. Return (rc, secs)."""
    env = dict(os.environ)
    # mutdir shadows src/ so `import engine` resolves to the mutant.
    env["PYTHONPATH"] = mutdir + os.pathsep + os.path.join(subject.SUBJECT_REPO, "src")
    t0 = time.time()
    try:
        proc = subprocess.run(
            [subject.PYTHON, "-m", "pytest", subject.oracle_abs(), "-q",
             "-p", "no:cacheprovider", "-o", "pythonpath="],
            cwd=subject.SUBJECT_REPO, env=env, capture_output=True,
            timeout=TIMEOUT_S,
        )
        return proc.returncode, time.time() - t0, ""
    except subprocess.TimeoutExpired:
        return None, time.time() - t0, "timeout"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=12, help="max sites to try")
    ap.add_argument("--make-placeholder", action="store_true",
                    help="use placeholder masking (LLM-style prompt)")
    args = ap.parse_args(argv)

    # ---- A. green gate ----
    print("A: baseline oracle...")
    t0 = time.time()
    proc = subprocess.run(
        [subject.PYTHON, "-m", "pytest", subject.oracle_abs(), "-q",
         "-p", "no:cacheprovider"],
        cwd=subject.SUBJECT_REPO, capture_output=True,
    )
    if proc.returncode != 0:
        print("ABORT: baseline not green (exit", proc.returncode, ")")
        return 1
    print(f"A: green in {time.time()-t0:.2f}s")

    source = open(subject.subject_py()).read()
    sites = site_target.find_sites(source)
    print(f"B: found {len(sites)} candidate sites")

    andy = DeterministicAndy()
    os.makedirs(RESULT_DIR, exist_ok=True)
    os.makedirs(SCRATCH, exist_ok=True)
    results = []
    seen = set()
    tried = 0

    for site in sites:
        if tried >= args.limit:
            break
        mutdir = None
        for snippet in andy.mutate(site):
            mutated = apply_mutant(source, site["start"], site["end"], snippet)
            if not is_valid_python(mutated):
                continue
            if mutated == source:  # identical substitution
                continue
            if mutated in seen:
                continue
            seen.add(mutated)
            tried += 1
            # materialize mutant in scratch dir shadowing src/
            mutdir = tempfile.mkdtemp(dir=SCRATCH, prefix="mut_")
            # copy ONLY the mutated module (src/engine.py), package name `engine`
            mut_file = os.path.join(mutdir, "engine.py")
            with open(mut_file, "w") as fh:
                fh.write(mutated)

            rc, secs, note = run_oracle(mutdir)
            if note == "timeout":
                verdict = "timeout"
            elif rc == 0:
                verdict = "survived"
            else:
                verdict = "killed"

            rec = {
                "kind": site["kind"],
                "orig": site["text"],
                "snippet": snippet,
                "start": site["start"],
                "end": site["end"],
                "verdict": verdict,
                "rc": rc,
                "secs": round(secs, 2),
            }
            results.append(rec)
            print(f"  [{verdict:8s}] {rec['orig']!r} ~> {snippet!r} "
                  f"({secs:.2f}s)")
        if mutdir:
            shutil.rmtree(mutdir, ignore_errors=True)

    out = os.path.join(RESULT_DIR, "results.json")
    with open(out, "w") as fh:
        json.dump(results, fh, indent=2)
    from collections import Counter
    print("\nsummary:", dict(Counter(r["verdict"] for r in results)))
    print("wrote", out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
