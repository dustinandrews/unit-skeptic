"""CLI: `adversary score --subject <dir>` + `adversary equiv ...`.

DeterministicMutator is the default score driver; an LlmMutator can be supplied
later through the same Mutator protocol. The equiv subcommand triages a
survivors JSON via the JEV equivalence seam (offline stub by default unless the
real adapter is wired).
"""
import argparse
import json
import os
import sys

from adversary import equiv, runner, scorer, sites
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


def run_equiv(subject_dir, survivors_path, out_path=None, confidence_cutoff=None,
              offline=False, decide=None):
    """Triage a survivors JSON against the subject's real source (FR-005/006).

    Read-only on the subject: modules are only read to build A/B blocks, never
    written (FR-007 / SC-005). `decide` is injected for testability; when
    omitted, `--offline` selects the deterministic stub, else the real JEV
    adapter. Emits a triage JSON list preserving input ordering.
    """
    with open(survivors_path) as fh:
        survivors = json.load(fh)
    src_dir = os.path.join(subject_dir, "src")

    def source_for(path):
        full = os.path.join(src_dir, path)
        if not os.path.isfile(full):
            full = path  # allow an absolute path
        return open(full).read()

    if decide is None:
        decide = equiv.offline_decide if offline else equiv.real_decide
    cutoff = confidence_cutoff if confidence_cutoff is not None else equiv.CONFIDENCE_CUTOFF
    triaged = equiv.triage(survivors, source_for, decide=decide, confidence_cutoff=cutoff)
    out_path = out_path or os.path.join(os.getcwd(), "triage.json")
    with open(out_path, "w") as fh:
        json.dump(triaged, fh, indent=2)
    from collections import Counter  # local; prints a human summary
    counts = Counter(r["label"] for r in triaged)
    print(f"triage: {len(triaged)} survivors — "
          f"equivalent={counts.get('equivalent', 0)}, "
          f"killable={counts.get('killable', 0)}, "
          f"undecided={counts.get('undecided', 0)}")
    if out_path:
        print(f"triage written to {out_path}")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(prog="adversary")
    sub = ap.add_subparsers(dest="cmd", required=True)
    ps = sub.add_parser("score", help="score a subject's test suite")
    ps.add_argument("--subject", required=True, help="path to subject repo")
    pe = sub.add_parser("equiv", help="triage survivors by JEV equivalence")
    pe.add_argument("--subject", required=True, help="path to subject repo (read-only)")
    pe.add_argument("--survivors", required=True, help="survivors JSON (scorer output)")
    pe.add_argument("--out", default=None, help="triage JSON output path (default ./triage.json)")
    pe.add_argument("--confidence-cutoff", type=float, default=None,
                    help="confidence threshold for undecided (default module constant)")
    pe.add_argument("--offline", action="store_true",
                    help="use the deterministic offline stub instead of live JEV")
    args = ap.parse_args(argv)
    if args.cmd == "score":
        return run_score(args.subject)
    if args.cmd == "equiv":
        return run_equiv(args.subject, args.survivors, out_path=args.out,
                         confidence_cutoff=args.confidence_cutoff,
                         offline=args.offline)
    return 1


if __name__ == "__main__":
    sys.exit(main())
