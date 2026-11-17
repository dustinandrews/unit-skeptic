"""deadtests.py: dead-test detection (Sprint 5).

Pure aggregation fns: aggregate_kills (error/timeout not attributed),
classify (dead = kills == 0), build_output (FR-003 corpus-qualified JSON).
T002."""

import json

from adversary import deadtests


def _runs():
    """Sample (verdict, failing_ids) traces for aggregation tests."""
    return [
        ("killed", ["tests.test_pricing::t1"]),
        ("killed", ["tests.test_pricing::t1", "tests.test_pricing::t2"]),
        ("survived", []),
        ("error", ["tests.test_pricing::t9"]),  # error must NOT attribute
        ("timeout", ["tests.test_pricing::t10"]),  # timeout must NOT attribute
    ]


def test_aggregate_kills_counts_per_test():
    """T002: kills are summed per test; error/timeout contribute nothing."""
    counts = deadtests.aggregate_kills(_runs())
    assert counts["tests.test_pricing::t1"] == 2
    assert counts["tests.test_pricing::t2"] == 1
    # t9 (error), t10 (timeout) must not appear at all.
    assert "tests.test_pricing::t9" not in counts
    assert "tests.test_pricing::t10" not in counts


def test_classify_dead_by_zero_kills():
    """T002: a test with zero kills is dead; with kills >= 1 is alive."""
    kill_map = {"tests.test_pricing::t1": 2, "tests.test_pricing::t2": 0}
    classified = deadtests.classify(kill_map)
    assert classified["tests.test_pricing::t1"]["status"] == "alive"
    assert classified["tests.test_pricing::t2"]["status"] == "dead"


def test_build_output_json_shape():
    """T002: FR-003 shape — corpus-qualified, dead-first stable order, totals."""
    kill_map = {"t_strong_a": 3, "t_weak_x": 0, "t_strong_b": 1}
    out = deadtests.build_output(kill_map)
    # Top-level corpus qualifier (dead-in-this-corpus, not a global claim).
    assert out["corpus"] == "deterministic"
    assert out["total"] == 3
    assert out["dead"] == 1
    # Dead tests come first; within a group, stable (sorted) order.
    ids = [item["test_id"] for item in out["tests"]]
    assert ids[0] == "t_weak_x"
    assert set(ids[1:]) == {"t_strong_a", "t_strong_b"}
    assert all(item["kills"] == kill_map[item["test_id"]] for item in out["tests"])
    assert all(item["status"] in ("dead", "alive") for item in out["tests"])
    # build_output result serializes cleanly to JSON (machine-readable).
    json.dumps(out)
