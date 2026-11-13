"""Runner: green-gate + scratch-dir shadowed pytest runs -> mechanical verdicts.

Verdicts: killed / survived / error / timeout. Uses a tiny inline subject for
isolation (not the guineapig package) so the runner tests stay self-contained.
"""
import os
import textwrap

from adversary import runner


def _write_subject(dirpath):
    """Write a tiny module + a passing test that imports it by name.

    Import relies on the module being importable (the runner sets PYTHONPATH);
    the test does NOT hard-insert src, so the mutant shadow can win.
    """
    src = os.path.join(dirpath, "src")
    tests = os.path.join(dirpath, "tests")
    os.makedirs(src, exist_ok=True)
    os.makedirs(tests, exist_ok=True)
    mod = os.path.join(src, "subject_mod.py")
    with open(mod, "w") as fh:
        fh.write(textwrap.dedent("""\
            def is_positive(n):
                return n > 0
        """))
    with open(os.path.join(tests, "test_subject.py"), "w") as fh:
        fh.write(textwrap.dedent("""\
            from subject_mod import is_positive
            def test_positive():
                assert is_positive(5)
        """))
    return {"dir": dirpath, "src": src}


def _module(path):
    with open(path) as fh:
        return fh.read()


def _full_module(original, replacement):
    return original.replace("return n > 0", replacement)


def _write_pkg_subject(dirpath):
    """A package-layout subject (src/pkg/mod.py) with an __init__.py.

    This is the regression case: the shadow must copy the __init__.py so the
    package stays regular and overrides the real one; otherwise the mutant
    silently never loads.
    """
    pkg = os.path.join(dirpath, "src", "pkg")
    tests = os.path.join(dirpath, "tests")
    os.makedirs(pkg, exist_ok=True)
    os.makedirs(tests, exist_ok=True)
    with open(os.path.join(pkg, "__init__.py"), "w") as fh:
        fh.write('"""pkg."""\n')
    with open(os.path.join(pkg, "mod.py"), "w") as fh:
        fh.write(textwrap.dedent("""\
            def is_positive(n):
                return n > 0
        """))
    with open(os.path.join(tests, "test_pkg.py"), "w") as fh:
        fh.write(textwrap.dedent("""\
            from pkg.mod import is_positive
            def test_positive():
                assert is_positive(5)
        """))
    return {"dir": dirpath, "src": os.path.join(dirpath, "src")}


# --- green gate ---------------------------------------------------------------

def test_green_gate_passes(tmp_path):
    subj = _write_subject(str(tmp_path))
    rc, secs, note = runner.run_oracle(subj["dir"], subj["src"])
    assert rc == 0
    assert note == ""


def test_green_gate_catches_failing_subject(tmp_path):
    subj = _write_subject(str(tmp_path))
    pt = os.path.join(subj["dir"], "tests", "test_subject.py")
    with open(pt) as fh:
        text = fh.read()
    with open(pt, "w") as fh:
        fh.write(text.replace("assert is_positive(5)", "assert not is_positive(5)"))
    rc, secs, note = runner.run_oracle(subj["dir"], subj["src"])
    assert rc != 0


# --- verdicts -----------------------------------------------------------------

def test_killed_when_mutant_breaks_a_test(tmp_path):
    subj = _write_subject(str(tmp_path))
    original = _module(os.path.join(subj["src"], "subject_mod.py"))
    mutated = _full_module(original, "return n < 0")  # is_positive(5) -> False
    verdict = runner.run_mutant(subj["dir"], "subject_mod.py", mutated, src_dir=subj["src"])
    assert verdict == "killed"


def test_survived_when_mutant_passes(tmp_path):
    subj = _write_subject(str(tmp_path))
    original = _module(os.path.join(subj["src"], "subject_mod.py"))
    mutated = _full_module(original, "return n > 0 or False")
    verdict = runner.run_mutant(subj["dir"], "subject_mod.py", mutated, src_dir=subj["src"])
    assert verdict == "survived"


def test_error_when_mutant_does_not_parse(tmp_path):
    subj = _write_subject(str(tmp_path))
    verdict = runner.run_mutant(subj["dir"], "subject_mod.py", "def is_positive(:\n", src_dir=subj["src"])
    assert verdict == "error"


def test_timeout_when_run_exceeds_wall(tmp_path):
    subj = _write_subject(str(tmp_path))
    # Whole-module mutant that loops forever.
    mutated = "def is_positive(n):\n    while True:\n        pass\n"
    verdict = runner.run_mutant(subj["dir"], "subject_mod.py", mutated,
                                src_dir=subj["src"], timeout_s=2)
    assert verdict == "timeout"


# --- package-layout regression (mutant must actually load) --------------------

def test_pkg_mutant_that_changes_behavior_is_killed(tmp_path):
    """Regression pin: a package mutant that breaks a test must be killed.

    Guards against the shadow being a namespace package (no __init__.py) which
    Python ignores in favor of the real package, so the mutant never runs.
    """
    subj = _write_pkg_subject(str(tmp_path))
    original = _module(os.path.join(subj["src"], "pkg", "mod.py"))
    mutated = original.replace("return n > 0", "return n < 0")
    assert mutated != original
    verdict = runner.run_mutant(subj["dir"], "pkg/mod.py", mutated, src_dir=subj["src"])
    assert verdict == "killed"


def test_pkg_mutant_that_keeps_behavior_is_survived(tmp_path):
    subj = _write_pkg_subject(str(tmp_path))
    original = _module(os.path.join(subj["src"], "pkg", "mod.py"))
    mutated = original.replace("return n > 0", "return n > 0 or False")
    verdict = runner.run_mutant(subj["dir"], "pkg/mod.py", mutated, src_dir=subj["src"])
    assert verdict == "survived"
