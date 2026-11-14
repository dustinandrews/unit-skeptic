"""T004: `adversary equiv` end-to-end against a constructed survivors JSON.

Runs the REAL CLI (``cli.main(["equiv", ...])``) with the offline stub against
the Spike 3 verification subject. SC-001 (every label correct, exactly one
bucket), SC-003 (undecided not collapsed), SC-005 (``--help`` plus no subject
source modified when triaging).
"""
import json
import os

import pytest

from adversary import cli

SUBJECT_REL = os.path.join(
    os.path.dirname(__file__), "..", "..", "research", "spike-jev-equiv", "triage_subject.py")


def _offsets(source, needle):
    i = source.index(needle)
    return i, i + len(needle)


def _record(mod_rel, source, needle, replacement, verdict="survived"):
    s, e = _offsets(source, needle)
    return {"path": mod_rel, "start": s, "end": e,
            "orig": needle, "replacement": replacement, "verdict": verdict}


# Gold truth: (replacement-identifying needle, expected label). Equivalent /
# killable / undecided all present; labels mirror DEFAULT_OFFLINE_ANSWERS (SC-001).
VERIFICATION_CASES = [
    ("n > 0", "0 < n",     "equivalent"),  # commute — same behavior
    ("n > 0", "n < 0",     "killable"),    # flipped comparison — behavior differs
    ("n > 0", "n >= 0",    "undecided"),   # low-confidence boundary — not forced
    ("quantity >= 10", "10 <= quantity", "equivalent"),  # commute
    ("quantity >= 10", "quantity > 10",    "killable"),  # threshold shifted
]


@pytest.fixture(scope="module")
def subject_dir(tmp_path_factory):
    if not os.path.exists(SUBJECT_REL):
        pytest.skip("research/spike-jev-equiv/triage_subject.py not present")
    subject = tmp_path_factory.mktemp("subject")
    src = subject / "src"
    src.mkdir()
    (src / "__init__.py").write_text("")
    # copy the REAL verification subject as the src module (read-only below)
    (src / "triage_mod.py").write_text(open(SUBJECT_REL).read())
    return str(subject), str(src / "triage_mod.py")


def test_equiv_cli_labels_every_survivor_correct(subject_dir):
    subject, mod = subject_dir
    source = open(mod).read()

    records = [_record("triage_mod.py", source, n, r) for n, r, _ in VERIFICATION_CASES]
    sj = os.path.join(os.path.dirname(mod), "..", "..", "survivors.json")
    with open(sj, "w") as fh:
        json.dump(records, fh)
    o = os.path.join(os.path.dirname(mod), "triage.json")
    rc = cli.main(["equiv", "--subject", subject,
                   "--survivors", sj, "--out", o, "--offline"])
    assert rc == 0

    data = json.load(open(o))
    assert len(data) == len(records)
    # every label right (SC-001, ground truth)
    assert [d["label"] for d in data] == [b for _n, _r, b in VERIFICATION_CASES]
    # every survivor in exactly one bucket (SC-001 / SC-003)
    assert all(d["label"] in ("equivalent", "killable", "undecided") for d in data)
    # every survivor recorded exactly once, ordering preserved from input (FR-006)
    assert [d["start"] for d in data] == [r["start"] for r in records]


def test_equiv_does_not_modify_subject_source(subject_dir):
    subject, mod = subject_dir
    source = open(mod).read()  # snapshot
    records = [_record("triage_mod.py", source, n, r) for n, r, _ in VERIFICATION_CASES]
    sj = os.path.join(os.path.dirname(mod), "..", "..", "survivors2.json")
    with open(sj, "w") as fh:
        json.dump(records, fh)
    o = os.path.join(os.path.dirname(mod), "triage2.json")
    rc = cli.main(["equiv", "--subject", subject,
                   "--survivors", sj, "--out", o, "--offline"])
    assert rc == 0
    assert open(mod).read() == source  # subject untouched (FR-007 / SC-005)


def test_equiv_help_flag(tmp_path, capsys):
    try:
        cli.main(["equiv", "--help"])
    except SystemExit as e:
        assert e.code == 0
    out = capsys.readouterr().out
    assert "--survivors" in out and "--confidence-cutoff" in out