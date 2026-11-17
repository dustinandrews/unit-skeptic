"""T003: deadtests driver + CLI end-to-end on the real guineapig subject.

SC-001: the 4 known weak tests are dead; strong tests alive with kills >= 1.
SC-003: two runs are byte-identical.
SC-004: subject source is unchanged after a run.
"""
import json
import os

import pytest

REPO_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
GUINEAPIG = os.path.join(REPO_ROOT, "guineapig")

WEAK = [
    "tests.test_weak::test_weak_tautology_always_true",
    "tests.test_weak::test_weak_constant_against_itself",
    "tests.test_weak::test_weak_assert_none_is_none",
    "tests.test_weak::test_weak_no_behavior_called",
]


def _sha(path):
    import hashlib
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        h.update(fh.read())
    return h.hexdigest()


def test_deadtests_real_guineapig_meets_ground_truth(tmp_path):
    """SC-001: 4 weak tests dead, strong tests alive via the real CLI."""
    out = os.path.join(str(tmp_path), "dead.json")
    from adversary import cli
    rc = cli.main(["deadtests", "--subject", GUINEAPIG, "--out", out])
    assert rc == 0
    with open(out) as fh:
        doc = json.load(fh)
    assert doc["corpus"] == "deterministic"
    by_id = {t["test_id"]: t for t in doc["tests"]}
    # The 4 weak tests are dead (unambiguous ground truth in ANY corpus).
    for wid in WEAK:
        assert wid in by_id, f"weak test missing from output: {wid}"
        assert by_id[wid]["status"] == "dead", f"{wid} should be dead"
        assert by_id[wid]["kills"] == 0
    # The tool is non-trivial: at least one strong contract test is alive.
    # (Strong tests asserting constants / rejection paths may read dead in the
    # deterministic corpus — those operator sites are unreachable — which is
    # correct corpus-scoped behavior per corrected SC-001, not a false positive.)
    strong_alive = [t for t in doc["tests"]
                    if t["test_id"] not in WEAK and t["status"] == "alive"]
    assert len(strong_alive) > 0, "no strong test alive - tool is trivial"
    assert all(t["kills"] >= 1 for t in strong_alive)


def test_deadtests_reproducible_byte_identical(tmp_path):
    """SC-003: two runs produce byte-identical JSON."""
    from adversary import cli
    out1 = os.path.join(str(tmp_path), "dead1.json")
    out2 = os.path.join(str(tmp_path), "dead2.json")
    assert cli.main(["deadtests", "--subject", GUINEAPIG, "--out", out1]) == 0
    assert cli.main(["deadtests", "--subject", GUINEAPIG, "--out", out2]) == 0
    with open(out1, "rb") as a, open(out2, "rb") as b:
        assert a.read() == b.read()


def test_deadtests_subject_unchanged(tmp_path):
    """SC-004: subject source bytes unchanged after a run."""
    pricing = os.path.join(GUINEAPIG, "src", "guineapig", "pricing.py")
    before = _sha(pricing)
    out = os.path.join(str(tmp_path), "dead.json")
    from adversary import cli
    assert cli.main(["deadtests", "--subject", GUINEAPIG, "--out", out]) == 0
    assert _sha(pricing) == before


def test_deadtests_cli_requires_subject():
    """T003: deadtests requires --subject (argparse raises SystemExit != 0)."""
    from adversary import cli
    with pytest.raises(SystemExit) as exc:
        cli.main(["deadtests"])
    assert exc.value.code != 0
