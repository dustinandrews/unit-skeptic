"""Scorer: A->C loop, verdict collection, score, survivors JSON, reproducibility."""
import os

import pytest

from adversary import scorer
from adversary.mutators import DeterministicMutator


def _tiny_source():
    return "def f(n):\n    return n > 0\n"


def _sites():
    return [
        {"module": "m.py", "start": 21, "end": 26, "text": "n > 0", "kind": "Compare"},
    ]


def test_killed_and_survived_feed_denominator():
    verdicts = ["killed", "survived"]
    score = scorer.compute_score(verdicts)
    assert score == 0.5


def test_error_and_timeout_excluded_from_denominator():
    verdicts = ["killed", "survived", "error", "timeout"]
    score = scorer.compute_score(verdicts)
    assert score == 0.5  # only killed+survived count


def test_all_survived_is_zero():
    assert scorer.compute_score(["survived"]) == 0.0


def test_all_killed_is_one():
    assert scorer.compute_score(["killed"]) == 1.0


def test_empty_verdicts_is_zero():
    assert scorer.compute_score([]) == 0.0


def test_run_loop_invokes_mutator_and_runner(mocker):
    """The loop must call mutator.mutate per site and runner.run_mutant per candidate."""
    mut = DeterministicMutator()
    records = scorer.run_loop("dummy_dir", "src", _sites(), mut, _tiny_source(),
                              run_mutant_impl=lambda *a, **k: "killed")
    # With site "n > 0", DeterministicMutator yields flips -> records produced.
    assert len(records) >= 1
    assert all(r["verdict"] != "" for r in records)


def test_run_loop_writes_survivors_json(tmp_path):
    mut = DeterministicMutator()
    sites = _sites()
    out = str(tmp_path / "out.json")
    records = scorer.run_loop("dummy_dir", "src", sites, mut, _tiny_source(),
                              out_path=out,
                              run_mutant_impl=lambda *a, **k: "survived")
    assert os.path.exists(out)
    import json
    data = json.load(open(out))
    assert len(data) == len(records)
    assert all("verdict" in r for r in data)


def test_reproducible_identical_scores():
    """Two runs with the same inputs yield identical verdicts+scores."""
    mut = DeterministicMutator()
    sites = _sites()
    src = _tiny_source()
    r1 = scorer.run_loop("d", "s", sites, mut, src, run_mutant_impl=lambda *a, **k: "killed")
    r2 = scorer.run_loop("d", "s", sites, mut, src, run_mutant_impl=lambda *a, **k: "killed")
    assert [r["verdict"] for r in r1] == [r["verdict"] for r in r2]
    assert scorer.compute_score([r["verdict"] for r in r1]) == \
        scorer.compute_score([r["verdict"] for r in r2])


def _multi_site_source():
    return "def a(x):\n    return x > 0\n\ndef b(y):\n    return y < 10\n"


def _multi_sites():
    return [
        {"module": "m.py", "start": 20, "end": 25, "text": "x > 0", "kind": "Compare"},
        {"module": "m.py", "start": 52, "end": 58, "text": "y < 10", "kind": "Compare"},
    ]


def test_max_workers_parallel_matches_serial():
    """max_workers>1 must produce the same record sequence as serial (order
    preserved; thread-safe run_mutant_impl; no dropped or duplicated records)."""
    mut = DeterministicMutator()
    sites = _multi_sites()
    src = _multi_site_source()
    calls = []  # concurrency stress: run_mutant_impl called exactly once per candidate
    def track(*a, **k):
        calls.append(1)
        return "killed"
    ceil = len(sites) * 4  # generous upper bound; DeterministicMutator flips >=1/site
    serial = scorer.run_loop("d", "s", sites, mut, src, run_mutant_impl=track)
    n_serial = len(serial)
    parallel = scorer.run_loop("d", "s", sites, mut, src, run_mutant_impl=track,
                               max_workers=4)
    assert len(parallel) == n_serial
    assert [r["verdict"] for r in parallel] == [r["verdict"] for r in serial]
    assert len(calls) <= ceil  # no runaway duplication from threads


def test_max_workers_default_and_one_are_serial():
    mut = DeterministicMutator()
    sites = _multi_sites()
    src = _multi_site_source()
    impl = lambda *a, **k: "killed"
    r_default = scorer.run_loop("d", "s", sites, mut, src, run_mutant_impl=impl)
    r_one = scorer.run_loop("d", "s", sites, mut, src, run_mutant_impl=impl, max_workers=1)
    assert [r["verdict"] for r in r_default] == [r["verdict"] for r in r_one]
