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

from adversary import andy, deadtests, equiv, runner, scorer, sites
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


def run_score(subject_dir, mutator="deterministic", model=None, trials=1,
              offline=False, src_rel="src", tests_rel="tests", python=None,
              max_workers=1):
    """Green gate -> enumerate sites -> loop -> print score. Returns exit code.

    ``--mutator`` selects the fault generator: ``deterministic`` (default,
    backward compatible) or ``llm`` (Andy). For ``llm``, ``model`` selects the
    OpenRouter model id and ``offline`` swaps the transport for a deterministic
    scripted stub so the pipeline runs with no network/key (FR-005 / SC-002).

    ``--src-rel``/``--tests-rel``/``--python`` (Sprint 7) relax the rigid
    ``src/``+``tests/``+own-interpreter assumptions for real repos.
    """
    src_dir, module_rel = _find_py_module(subject_dir, src_rel)
    if module_rel is None:
        print(f"adversary: no python module under {subject_dir}/{src_rel}",
              file=sys.stderr)
        return 1

    full = os.path.join(src_dir, module_rel)
    source = open(full).read()

    # A. green gate
    rc, secs, note = runner.run_oracle(subject_dir, src_dir, tests_rel=tests_rel,
                                       python=python)
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
    if mutator == "llm":
        model_id = model or andy.DEFAULT_MODEL
        gen = andy.LlmMutator(source, model=model_id, trials=trials,
                              complete=andy.offline_complete if offline else None)
    else:
        mutator, model_id = "deterministic", model or ""
        gen = DeterministicMutator()
    record_attrs = {"mutator": mutator, "model": model_id}
    if python:
        record_attrs["python"] = os.path.basename(python)
    impl = lambda d, mr, ms: runner.run_mutant(d, mr, ms, src_dir=src_dir,
                                               tests_rel=tests_rel, python=python)
    records = scorer.run_loop(subject_dir, src_dir, site_list, gen, source,
                              module_rel=module_rel,
                              run_mutant_impl=impl,
                              out_path=os.path.join(os.getcwd(), "survivors.json"),
                              record_attrs=record_attrs, max_workers=max_workers)
    verdicts = [r["verdict"] for r in records]
    score = scorer.compute_score(verdicts)
    attribution = f"mutator={mutator}"
    if model_id:
        attribution += f" model={model_id}"
    print(f"score = {score:.3f}  (caught={verdicts.count('killed')}, "
          f"escapes={verdicts.count('survived')}, "
          f"error={verdicts.count('error')}, timeout={verdicts.count('timeout')})"
          f"  {attribution}")
    print("escapes (missed bugs) written to survivors.json")
    return 0


def run_equiv(subject_dir, survivors_path, out_path=None, confidence_cutoff=None,
              offline=False, decide=None, src_rel="src"):
    """Triage a survivors JSON against the subject's real source (FR-005/006).

    Read-only on the subject: modules are only read to build A/B blocks, never
    written (FR-007 / SC-005). `decide` is injected for testability; when
    omitted, `--offline` selects the deterministic stub, else the real JEV
    adapter. Emits a triage JSON list preserving input ordering.
    """
    with open(survivors_path) as fh:
        survivors = json.load(fh)
    src_dir = os.path.join(subject_dir, src_rel)

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
    print(f"triage: {len(triaged)} escapes triaged — "
          f"equivalent={counts.get('equivalent', 0)}, "
          f"killable={counts.get('killable', 0)}, "
          f"undecided={counts.get('undecided', 0)}")
    if out_path:
        print(f"triage written to {out_path}")
    return 0


def run_deadtests(subject_dir, out_path=None, src_rel="src", tests_rel="tests",
                  python=None):
    """Flag tests that never kill a fault (Sprint 5, FR-001/SC-001)."""
    # Loads only by importing the runner-driven pure aggregation inline to
    # avoid a heavy import up-front.
    out_path = out_path or os.path.join(os.getcwd(), "dead-tests.json")
    json_text = deadtests.run_deadtests(subject_dir, out_path=out_path,
                                        src_rel=src_rel, tests_rel=tests_rel,
                                        python=python)
    doc = json.loads(json_text)
    print(f"bad tests (catch nothing): {doc['dead']} of {doc['total']}  (corpus={doc['corpus']})")
    print(f"written to {out_path}")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(prog="adversary")
    sub = ap.add_subparsers(dest="cmd", required=True)
    ps = sub.add_parser("score", help="score a subject's test suite")
    ps.add_argument("--subject", required=True, help="path to subject repo")
    ps.add_argument("--mutator", choices=("deterministic", "llm"),
                    default="deterministic",
                    help="fault generator: deterministic (default) or llm (Andy)")
    ps.add_argument("--model", default=None,
                    help="OpenRouter model id for --mutator llm (default %s)" % andy.DEFAULT_MODEL)
    ps.add_argument("--trials-per-site", type=int, default=1,
                    help="candidates per site for --mutator llm (default 1)")
    ps.add_argument("--offline", action="store_true",
                    help="use the deterministic scripted stub (no network/key) for --mutator llm")
    ps.add_argument("--src-rel", default="src",
                    help="dir (under --subject) holding the source to score (default src)")
    ps.add_argument("--tests-rel", default="tests",
                    help="dir (under --subject) holding the test suite (default tests)")
    ps.add_argument("--python", default=None,
                    help="interpreter for pytest subprocesses (default sys.executable; "
                         "point at the subject's venv for non-flat repos)")
    ps.add_argument("--max-workers", type=int, default=1,
                    help="run mutant sites across N threads (default 1); speeds up "
                         "large real-repo subjects (suite runs release the GIL)")
    pe = sub.add_parser("equiv", help="triage escaped bugs by JEV equivalence")
    pe.add_argument("--subject", required=True, help="path to subject repo (read-only)")
    pe.add_argument("--survivors", required=True, help="survivors/escapes JSON (scorer output)")
    pe.add_argument("--out", default=None, help="triage JSON output path (default ./triage.json)")
    pe.add_argument("--confidence-cutoff", type=float, default=None,
                    help="confidence threshold for undecided (default module constant)")
    pe.add_argument("--offline", action="store_true",
                    help="use the deterministic offline stub instead of live JEV")
    pe.add_argument("--src-rel", default="src",
                    help="dir (under --subject) holding the source (default src)")
    pd = sub.add_parser("deadtests", help="flag tests that never catch a bug")
    pd.add_argument("--subject", required=True, help="path to subject repo (read-only)")
    pd.add_argument("--out", default=None, help="dead-tests JSON output path (default ./dead-tests.json)")
    pd.add_argument("--src-rel", default="src",
                    help="dir (under --subject) holding the source (default src)")
    pd.add_argument("--tests-rel", default="tests",
                    help="dir (under --subject) holding the test suite (default tests)")
    pd.add_argument("--python", default=None,
                    help="interpreter for pytest subprocesses (default sys.executable)")
    args = ap.parse_args(argv)
    if args.cmd == "score":
        return run_score(args.subject, mutator=args.mutator, model=args.model,
                         trials=args.trials_per_site, offline=args.offline,
                         src_rel=args.src_rel, tests_rel=args.tests_rel,
                         python=args.python, max_workers=args.max_workers)
    if args.cmd == "equiv":
        return run_equiv(args.subject, args.survivors, out_path=args.out,
                         confidence_cutoff=args.confidence_cutoff,
                         offline=args.offline, src_rel=args.src_rel)
    if args.cmd == "deadtests":
        return run_deadtests(args.subject, out_path=args.out, src_rel=args.src_rel,
                             tests_rel=args.tests_rel, python=args.python)
    return 1


if __name__ == "__main__":
    sys.exit(main())
