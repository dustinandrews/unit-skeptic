"""Driver loop: green gate -> enumerate sites -> mutate -> run -> verdict -> record.

Score = killed / (killed + survived). error and timeout are excluded from the
denominator (they are not valid faults). `run_mutant_impl` is injectable for
testability (the real implementation lives in adversary.runner).
"""
import json


def compute_score(verdicts):
    """Score = killed / (killed + survived). error/timeout excluded."""
    killed = verdicts.count("killed")
    survived = verdicts.count("survived")
    if killed + survived == 0:
        return 0.0
    return killed / (killed + survived)


def run_loop(subject_dir, src_dir, sites, mutator, source,
             module_rel=None, run_mutant_impl=None, out_path=None):
    """Run the full A->C loop over sites and record verdicts.

    For each site, ask the mutator for replacement candidates; for each distinct
    candidate, splice it into the source at the site offsets, run the suite via
    run_mutant_impl, and record {path, start, end, orig, replacement, verdict}.
    Returns the records list; optionally writes survivors JSON to out_path.
    """
    if run_mutant_impl is None:
        from adversary import runner
        run_mutant_impl = lambda d, mr, ms, src_dir=src_dir: runner.run_mutant(d, mr, ms, src_dir=src_dir)
    records = []
    for site in sites:
        orig = site["text"]
        for replacement in mutator.mutate(site):
            mutated = source[:site["start"]] + replacement + source[site["end"]:]
            if mutated == source:
                continue
            verdict = run_mutant_impl(subject_dir, module_rel or "<module>", mutated)
            records.append({
                "path": site.get("module", "<string>"),
                "start": site["start"],
                "end": site["end"],
                "orig": orig,
                "replacement": replacement,
                "verdict": verdict,
            })
    if out_path:
        with open(out_path, "w") as fh:
            json.dump(records, fh, indent=2)
    return records
