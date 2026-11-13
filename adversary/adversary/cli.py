"""CLI: `adversary score --subject <dir>` — wire green gate -> mutate -> score.

DeterministicMutator is the default driver; an LlmMutator can be supplied later
through the same Mutator protocol.
"""
import argparse
import os
import sys

from adversary import runner, scorer, sites
from adversary.mutators import DeterministicMutator


def _find_py_module(subject_dir, src_rel="src"):
    """Return (src_dir, module_rel) for the first .py under <subject>/<src_rel>."""
    src_dir = os.path.join(subject_dir, src_rel)
    for root, _dirs, files in os.walk(src_dir):
        for f in sorted(files):
            if f.endswith(".py") and not f.startswith("__"):
                full = os.path.join(root, f)
                return src_dir, os.path.relpath(full, src_dir)
    return None, None


def run_score(subject_dir):
    """Green gate -> enumerate sites -> loop -> print score. Returns exit code."""
    src_dir, module_rel = _find_py_module(subject_dir)
    if module_rel is None:
        print(f"adversary: no python module under {subject_dir}/src", file=sys.stderr)
        return 1

    full = os.path.join(src_dir, module_rel)
    source = open(full).read()

    # A. green gate
    rc, secs, note = runner.run_oracle(subject_dir, src_dir)
    if note == "timeout":
        print("adversary: baseline suite timed out", file=sys.stderr)
        return 2
    if rc != 0:
        print(f"adversary: baseline not green (exit {rc})", file=sys.stderr)
        return 1
    print(f"A: baseline green in {secs:.2f}s")

    # B/C. enumerate, mutate, run, score
    site_list = sites.find_sites(source, module=module_rel)
    print(f"B: {len(site_list)} sites")
    mutator = DeterministicMutator()
    records = scorer.run_loop(subject_dir, src_dir, site_list, mutator, source,
                              module_rel=module_rel,
                              out_path=os.path.join(os.getcwd(), "survivors.json"))
    verdicts = [r["verdict"] for r in records]
    score = scorer.compute_score(verdicts)
    print(f"score = {score:.3f}  (killed={verdicts.count('killed')}, "
          f"survived={verdicts.count('survived')}, "
          f"error={verdicts.count('error')}, timeout={verdicts.count('timeout')})")
    print("survivors written to survivors.json")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(prog="adversary")
    sub = ap.add_subparsers(dest="cmd", required=True)
    ps = sub.add_parser("score", help="score a subject's test suite")
    ps.add_argument("--subject", required=True, help="path to subject repo")
    args = ap.parse_args(argv)
    if args.cmd == "score":
        return run_score(args.subject)
    return 1


if __name__ == "__main__":
    sys.exit(main())
