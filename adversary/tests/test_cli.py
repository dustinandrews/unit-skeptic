"""CLI: `adversary score --subject <dir>` wiring."""
import json
import os
import textwrap

from adversary import cli


def _make_subject(tmp_path):
    """Reusable subject: src/pkg/mod.py + tests that import pkg.mod by name."""
    src = tmp_path / "src" / "pkg"
    src.mkdir(parents=True, exist_ok=True)
    (src / "__init__.py").write_text("")
    (src / "mod.py").write_text(textwrap.dedent("""\
        def is_positive(n):
            return n > 0
    """))
    tests = tmp_path / "tests"
    tests.mkdir(exist_ok=True)
    (tests / "test_mod.py").write_text(textwrap.dedent("""\
        from pkg.mod import is_positive
        def test_positive():
            assert is_positive(5)
    """))
    return str(tmp_path), str(src / "mod.py")


def test_cli_score_requires_subject(tmp_path, capsys):
    try:
        cli.main(["score"])
    except SystemExit as e:
        assert e.code != 0
    else:
        out = capsys.readouterr()
        assert "subject" in out.err


def test_cli_score_runs_and_prints(tmp_path):
    subject_dir, mod_path = _make_subject(tmp_path)
    rc = cli.run_score(subject_dir)
    assert rc == 0


# ---------------------------------------------------------------------------
# `adversary equiv` (T003 / FR-005 / FR-006)
# ---------------------------------------------------------------------------

def _make_subject_with_src(tmp_path):
    """Subject with a src module + a survivors JSON with two in-function survivors."""
    subject = tmp_path / "subj"
    src = subject / "src"
    src.mkdir(parents=True, exist_ok=True)
    (src / "__init__.py").write_text("")
    mod = src / "m.py"
    mod.write_text("def is_positive(n):\n    return n > 0\n")
    body = mod.read_text()
    i = body.index("n > 0")
    survivors = [
        {"path": "m.py", "start": i, "end": i + 5, "orig": "n > 0",
         "replacement": "n < 0", "verdict": "survived"},
        {"path": "m.py", "start": i, "end": i + 5, "orig": "n > 0",
         "replacement": "0 < n", "verdict": "survived"},
    ]
    sj = tmp_path / "survivors.json"
    json.dump(survivors, open(sj, "w"))
    return str(subject), str(sj)


def test_equiv_requires_subject_and_survivors(capsys):
    for argv in (["equiv"], ["equiv", "--subject", "x"], ["equiv", "--survivors", "y"]):
        try:
            cli.main(argv)
        except SystemExit as e:
            assert e.code != 0, f"expected error for {argv}"
        else:
            assert False, f"expected SystemExit for {argv}"


def test_equiv_emits_triage_json_with_labels(tmp_path):
    subject, sj = _make_subject_with_src(tmp_path)
    out = str(tmp_path / "triage.json")
    # offline stub: replacement "n < 0" -> different(hc) killable; "0 < n" -> equivalent
    rc = cli.run_equiv(subject, sj, out_path=out, offline=True)
    assert rc == 0
    data = json.load(open(out))
    assert [r["label"] for r in data] == ["killable", "equivalent"]
    assert all(r["label"] in ("equivalent", "killable", "undecided") for r in data)


def test_equiv_reproducible_and_ordering_preserved(tmp_path):
    subject, sj = _make_subject_with_src(tmp_path)
    o1 = str(tmp_path / "a.json")
    o2 = str(tmp_path / "b.json")
    cli.run_equiv(subject, sj, out_path=o1, offline=True)
    cli.run_equiv(subject, sj, out_path=o2, offline=True)
    assert json.load(open(o1)) == json.load(open(o2))  # reproducible (FR-006)
    survivors = json.load(open(sj))
    t1 = json.load(open(o1))
    # input ordering preserved
    assert [r["path"] for r in t1] == [r["path"] for r in survivors]
    assert [r["start"] for r in t1] == [r["start"] for r in survivors]


def test_equiv_help(tmp_path, capsys):
    try:
        cli.main(["equiv", "--help"])
    except SystemExit as e:
        assert e.code == 0
    out = capsys.readouterr().out
    assert "--survivors" in out and "--subject" in out
