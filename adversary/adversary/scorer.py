"""Driver loop: green gate -> enumerate sites -> mutate -> run -> verdict -> record.

Score = killed / (killed + survived). error and timeout are excluded from the
denominator (they are not valid faults). `run_mutant_impl` is injectable for
testability (the real implementation lives in adversary.runner).
"""
import json
from concurrent.futures import ThreadPoolExecutor


def compute_score(verdicts):
    """Score = killed / (killed + survived). error/timeout excluded."""
    killed = verdicts.count("killed")
    survived = verdicts.count("survived")
    if killed + survived == 0:
        return 0.0
    return killed / (killed + survived)


def _run_site(site, subject_dir, src_dir, module_rel, source, mutator,
              run_mutant_impl, record_attrs):
    """Run one site's mutation candidates; returns the record list for it."""
    records = []
    orig = site["text"]
    for replacement in mutator.mutate(site):
        mutated = source[:site["start"]] + replacement + source[site["end"]:]
        if mutated == source:
            continue
        verdict = run_mutant_impl(subject_dir, module_rel or "<module>", mutated)
        rec = {
            "path": site.get("module", "<string>"),
            "start": site["start"],
            "end": site["end"],
            "orig": orig,
            "replacement": replacement,
            "verdict": verdict,
        }
        rec.update(record_attrs)
        records.append(rec)
    return records


def run_loop(subject_dir, src_dir, sites, mutator, source,
             module_rel=None, run_mutant_impl=None, out_path=None,
             record_attrs=None, max_workers=1):
    """Run the full A->C loop over sites and record verdicts.

    For each site, ask the mutator for replacement candidates; for each distinct
    candidate, splice it into the source at the site offsets, run the suite via
    run_mutant_impl, and record {path, start, end, orig, replacement, verdict}.
    Returns the records list; optionally writes survivors JSON to out_path.

    With max_workers>1 the sites are processed on a ThreadPoolExecutor (the
    default runner work is a subprocess pytest, so the GIL is free during the
    wait — real parallelism). Records are emitted in site order regardless of
    completion order, so a max_workers=N run yields the same record sequence
    as a serial one. Thread-safety of run_mutant_impl is the caller's
    responsibility; the default subprocess implementation is concurrency-safe.
    """
    if run_mutant_impl is None:
        from adversary import runner
        run_mutant_impl = lambda d, mr, ms, src_dir=src_dir: runner.run_mutant(d, mr, ms, src_dir=src_dir)
    record_attrs = record_attrs or {}
    max_workers = max(1, int(max_workers or 1))
    if max_workers == 1 or len(sites) <= 1:
        # Serial is the default and must stay byte-identical with prior runs.
        records = []
        for site in sites:
            records.extend(_run_site(site, subject_dir, src_dir, module_rel,
                                     source, mutator, run_mutant_impl, record_attrs))
    else:
        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            futures = [pool.submit(_run_site, site, subject_dir, src_dir,
                                   module_rel, source, mutator, run_mutant_impl,
                                   record_attrs) for site in sites]
            # Preserve input (site) order in results, not completion order.
            records = [rec for fut in futures for rec in fut.result()]
    if out_path:
        with open(out_path, "w") as fh:
            json.dump(records, fh, indent=2)
    return records
