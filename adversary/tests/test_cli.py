"""CLI: `adversary score --subject <dir>` wiring."""
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
