"""Dead-test detection (Sprint 5).

Flags tests that never kill any fault. A test's **kill count** is the number
of KILLED mutants (parseable, behavior-changing runs) on which it failed.
Error/timeout mutants contribute NO attribution — their failures are parse or
wall noise, not behavior (matches the score denominator). A test with
kill count 0 is **dead** in the corpus used; every entry also carries a
mechanical one-line `reason` (Sprint 9) derived from class-region sibling-kill
topology — CASE A (corpus poverty: no behavior-changing mutant landed in the
test's class) vs CASE B (regional no-op/redundancy: siblings in the class
killed, this test did not), or a confirmation for alive tests.

Pure aggregation here (independent, testable); the driver that walks sites and
runs mutants lives next to it (`run_deadtests`) and feeds these fns.
"""
import json

CORPUS = "deterministic"


def aggregate_kills(runs):
    """Sum per-test kill counts from `(verdict, failing_ids)` traces.

    Only `killed` verdicts attribute; error/timeout/survived contribute
    nothing (a survived mutant has no failures anyway; error/timeout failures
    are noise, per FR-002).
    """
    counts = {}
    for verdict, failing_ids in runs:
        if verdict != "killed":
            continue
        for tid in failing_ids:
            counts[tid] = counts.get(tid, 0) + 1
    return counts


def _class_region(test_id):
    """Sprint 9: nodeid class region = prefix before the final ``::``.

    pytest junit emits ``classname::name``; the classname may itself contain
    ``::`` (a path + class), so only the final component is the test name. When
    there is no ``::`` (decorated/parametrized bare nodeids) the whole nodeid is
    its own region — sibling kills 0, so such a dead test reads CASE A.
    """
    if "::" in test_id:
        return test_id.rsplit("::", 1)[0]
    return test_id


def class_kill_totals(kill_map):
    """Sum kills per class region (a test's siblings = class_total - own kills)."""
    totals = {}
    for tid, kills in kill_map.items():
        region = _class_region(tid)
        totals[region] = totals.get(region, 0) + kills
    return totals


def reason(test_id, kills, class_totals):
    """Mechanical one-line reason (Sprint 9), from collected kill data only.

    Dead (kills==0): CASE B if this test's class region holds sibling kills
    (regional no-op / redundancy), else CASE A (corpus poverty). Alive: a
    confirmation with the kill count. Pure + deterministic (NFR-003).
    """
    if kills > 0:
        return f"caught {kills} mutants"
    region = _class_region(test_id)
    siblings = class_totals.get(region, 0) - kills  # kills is 0 here
    if siblings > 0:
        return f"caught 0 mutants; sibling tests in class caught {siblings}"
    return "no behavior-changing mutant landed in this test's class (corpus poverty)"


def classify(kill_map):
    """Map test_id -> {test_id, kills, status, class, reason}."""
    totals = class_kill_totals(kill_map)
    out = {}
    for tid, kills in kill_map.items():
        out[tid] = {
            "test_id": tid,
            "kills": kills,
            "status": "dead" if kills == 0 else "alive",
            "class": _class_region(tid),
            "reason": reason(tid, kills, totals),
        }
    return out


def build_output(kill_map):
    """FR-003: corpus-qualified JSON doc, dead-first, stable order, totals."""
    classified = classify(kill_map)
    items = sorted(
        classified.values(),
        # dead first, then alive; ties by test_id for a stable order.
        key=lambda item: (0 if item["status"] == "dead" else 1, item["test_id"]),
    )
    counts = [i["status"] for i in items]
    return {
        "corpus": CORPUS,
        "total": len(items),
        "dead": counts.count("dead"),
        "alive": counts.count("alive"),
        "tests": items,
    }


def to_json(kill_map, out_path=None):
    """Serialize build_output; write to out_path if given. Returns the JSON text."""
    doc = build_output(kill_map)
    text = json.dumps(doc, indent=2)
    if out_path:
        with open(out_path, "w") as fh:
            fh.write(text)
    return text


def run_deadtests(subject_dir, out_path=None, src_rel="src", tests_rel="tests",
                  python=None):
    """Walk sites + deterministic mutants, attribute kills per test, emit JSON.

    Green-gate -> enumerate sites via DeterministicMutator -> run each distinct
    candidate through runner.run_mutant WITH a junit report (absolute, outside
    the subject) -> aggregate kills (error/timeout not attributed) ->
    build_output. Returns the JSON text; writes to out_path if given.
    """
    import os
    import shutil
    import tempfile

    from adversary import runner, sites
    from adversary.mutators import DeterministicMutator

    src_dir = os.path.join(subject_dir, src_rel)
    # Locate the first module under src (same convention as the score CLI).
    module_rel = None
    for root, _dirs, files in os.walk(src_dir):
        for f in sorted(files):
            if f.endswith(".py") and not f.startswith("__"):
                module_rel = os.path.relpath(os.path.join(root, f), src_dir)
                break
        if module_rel:
            break
    if module_rel is None:
        raise RuntimeError(f"no python module under {subject_dir}/{src_rel}")

    source = open(os.path.join(src_dir, module_rel)).read()

    mutator = DeterministicMutator()
    runs = []
    for site in sites.find_sites(source, module=module_rel):
        orig = site["text"]
        for replacement in mutator.mutate(site):
            mutated = source[: site["start"]] + replacement + source[site["end"]:]
            if mutated == source:
                continue
            # junit report must be absolute and outside the subject.
            junit_dir = tempfile.mkdtemp(prefix="adv_junit_")
            try:
                junit = os.path.join(junit_dir, "report.xml")
                result = runner.run_mutant(subject_dir, module_rel, mutated,
                                           src_dir=src_dir, tests_rel=tests_rel,
                                           python=python, junit_path=junit)
            finally:
                shutil.rmtree(junit_dir, ignore_errors=True)
            if isinstance(result, tuple):
                runs.append(result)

    kill_map = aggregate_kills(runs)
    # Zero-kill tests must appear as dead: they never produced a failing junit,
    # so enumerate the full test list from a clean baseline run and seed zeros.
    all_tests = _baseline_test_ids(subject_dir, src_dir, tests_rel=tests_rel,
                                   python=python)
    for tid in all_tests:
        kill_map.setdefault(tid, 0)
    return to_json(kill_map, out_path)


def _baseline_test_ids(subject_dir, src_dir, tests_rel="tests", python=None):
    """Full test id list from a clean green-gate junit run (stdlib+ET only)."""
    import os
    import shutil
    import tempfile
    import xml.etree.ElementTree as ET

    from adversary import runner
    junit_dir = tempfile.mkdtemp(prefix="adv_baseline_")
    try:
        junit = os.path.join(junit_dir, "baseline.xml")
        # Run the suite once, emitting junit, from an absolute path outside the
        # subject (SC-004); ignore rc (baseline expected green).
        env = dict(os.environ)
        env["PYTHONPATH"] = os.path.abspath(src_dir) + os.pathsep + env.get("PYTHONPATH", "")
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        import subprocess
        import sys
        subprocess.run(
            [python or sys.executable, "-m", "pytest", tests_rel, "-q", "-p",
             "no:cacheprovider", "-o", "pythonpath=",
             "--junitxml=" + os.path.abspath(junit)],
            cwd=subject_dir, env=env, capture_output=True, timeout=runner.DEFAULT_TIMEOUT_S)
        root = ET.parse(os.path.abspath(junit)).getroot()
    finally:
        shutil.rmtree(junit_dir, ignore_errors=True)
    return runner._junit_all_ids(root)
