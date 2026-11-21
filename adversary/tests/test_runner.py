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


# --- T001: per-test kill attribution via junit -----------------------------------

def test_run_mutant_with_junit_returns_failing_ids(tmp_path):
    """T001: with junit_path set, run_mutant returns (verdict, failing_ids).

    A behavior-changing mutant -> ("killed", [nodeid]) and the junit file
    exists; a surviving mutant -> ("survived", []).
    """
    subj = _write_subject(str(tmp_path))
    original = _module(os.path.join(subj["src"], "subject_mod.py"))
    junit = os.path.join(str(tmp_path), "junit_killed.xml")

    mutated = _full_module(original, "return n < 0")  # kills test_positive
    verdict, failing = runner.run_mutant(subj["dir"], "subject_mod.py", mutated,
                                         src_dir=subj["src"], junit_path=junit)
    assert verdict == "killed"
    assert "tests.test_subject::test_positive" in failing
    assert os.path.isfile(junit)

    junit2 = os.path.join(str(tmp_path), "junit_surv.xml")
    const = _full_module(original, "return n > 0 or False")  # survives
    verdict2, failing2 = runner.run_mutant(subj["dir"], "subject_mod.py", const,
                                           src_dir=subj["src"], junit_path=junit2)
    assert verdict2 == "survived"
    assert failing2 == []


def test_run_mutant_without_junit_keeps_string_verdict(tmp_path):
    """T001: default (no junit_path) keeps the verdict-string contract.

    The score loop must be untouched: run_mutant returns a plain string.
    """
    subj = _write_subject(str(tmp_path))
    original = _module(os.path.join(subj["src"], "subject_mod.py"))
    mutated = _full_module(original, "return n < 0")
    verdict = runner.run_mutant(subj["dir"], "subject_mod.py", mutated, src_dir=subj["src"])
    assert verdict == "killed"
    assert isinstance(verdict, str)


def test_run_mutant_junit_path_absolute_required(tmp_path):
    """T001: a relative junit path is REJECTED (no silent cwd pollution).

    A relative path resolves against the CALLING process cwd (not the subject,
    not the scratch), which would silently write the junit report wherever the
    caller happened to run from — the exact SC-004 hazard. Reject outright so
    the caller must pass a deliberate absolute path.
    """
    subj = _write_subject(str(tmp_path))
    original = _module(os.path.join(subj["src"], "subject_mod.py"))
    mutated = _full_module(original, "return n < 0")
    import pytest
    with pytest.raises(ValueError):
        runner.run_mutant(subj["dir"], "subject_mod.py", mutated,
                          src_dir=subj["src"], junit_path="rel_junit.xml")
    # Nothing written anywhere relative to the subject or caller cwd.
    assert not os.path.exists(os.path.join(subj["dir"], "rel_junit.xml"))
    assert not os.path.exists(os.path.join(subj["src"], "rel_junit.xml"))


def _write_subject_with_nested_tests(dirpath):
    """Subject with tests under src/tests (not root tests/) — SC-002.

    Real repos (e.g. AIEmailSummary) keep tests inside the source tree. The
    runner must be told --tests-rel src/tests; the default (tests) finds
    nothing and pytest exits non-green (no tests collected).
    """
    src = os.path.join(dirpath, "src")
    tests = os.path.join(src, "tests")
    os.makedirs(os.path.join(src, "mod.py") and src, exist_ok=True)
    os.makedirs(tests, exist_ok=True)
    with open(os.path.join(src, "mod.py"), "w") as fh:
        fh.write("def is_positive(n):\n    return n > 0\n")
    with open(os.path.join(tests, "test_mod.py"), "w") as fh:
        fh.write("from mod import is_positive\n"
                 "def test_positive():\n    assert is_positive(5)\n")
    return {"dir": dirpath, "src": src}


def test_src_layout_mutant_actually_loads_and_kills(tmp_path):
    """Regression: src-layout (package-qualified) mutant must actually load.

    Reproduces the false-0.000 bug: with `src/email_router/ai_service.py`
    imported as `email_router.ai_service`, pytest auto-prepends `src` to
    sys.path via rootdir inference, so the old minimal shadow never ran the
    mutant and every mutant *appeared* to survive. The full-tree mirror +
    cwd=scratch must resolve the mutant so a behavior-changing edit is killed.
    """
    src = os.path.join(str(tmp_path), "src")
    pkg = os.path.join(src, "email_router")
    tests = os.path.join(src, "tests")
    os.makedirs(pkg, exist_ok=True)
    os.makedirs(tests, exist_ok=True)
    with open(os.path.join(pkg, "__init__.py"), "w") as fh:
        fh.write('"""email_router."""\n')
    with open(os.path.join(pkg, "ai_service.py"), "w") as fh:
        fh.write("def ok():\n    return 'x'\n")
    with open(os.path.join(tests, "test_ai_service.py"), "w") as fh:
        fh.write("from email_router.ai_service import ok\n"
                 "def test_ok():\n    assert ok() == 'x'\n")
    original = open(os.path.join(pkg, "ai_service.py")).read()
    mutated = original.replace("return 'x'", "return 'y'")  # breaks test_ok
    # tests_rel=src/tests (nested), src_rel=src/email_router like the real repo.
    verdict = runner.run_mutant(str(tmp_path), "ai_service.py", mutated,
                                src_dir=pkg, tests_rel="src/tests")
    assert verdict == "killed"


# --- repo-flexibility (Sprint 7) --------------------------------------------

def test_oracle_default_tests_misses_nested_tests(tmp_path):
    """SC-002 RED: default tests_rel='tests' finds no tests under src/tests.

    pytest exits non-zero (5, no tests collected) because there is no root
    tests/ dir, only src/tests/.
    """
    subj = _write_subject_with_nested_tests(str(tmp_path))
    rc, _secs, note = runner.run_oracle(subj["dir"], subj["src"])
    assert rc != 0
    assert note == ""


def test_oracle_tests_rel_src_tests_reaches_green(tmp_path):
    """SC-002 GREEN: --tests-rel src/tests makes the nested-tests subject green."""
    subj = _write_subject_with_nested_tests(str(tmp_path))
    rc, _secs, note = runner.run_oracle(subj["dir"], subj["src"], tests_rel="src/tests")
    assert rc == 0
    assert note == ""


def test_oracle_uses_supplied_python_interpreter(tmp_path, monkeypatch):
    """SC-003: run_oracle drives the pytest subprocess under the given --python.

    No production code records sys.executable; exercise the subprocess command
    directly by capturing what runner.subprocess.run is asked to launch.
    """
    captured = {}
    class FakeProc:
        returncode = 0
    def fake_run(cmd, **kwargs):
        captured["cmd"] = cmd
        return FakeProc()
    monkeypatch.setattr(runner.subprocess, "run", fake_run)
    subj = _write_subject(str(tmp_path))
    rc, _secs, note = runner.run_oracle(subj["dir"], subj["src"], python="/venv/bin/python")
    assert rc == 0
    assert captured["cmd"][0] == "/venv/bin/python"
    assert captured["cmd"][1:3] == ["-m", "pytest"]


def test_mutant_uses_supplied_python_interpreter(tmp_path, monkeypatch):
    """SC-003: run_mutant drives the pytest subprocess under the given --python.

    The first-mutant subprocess must also honor --python (the oracle alone is
    not enough; the mutation loop runs pytest per candidate).
    """
    captured = {}
    class FakeProc:
        returncode = 0
    def fake_run(cmd, **kwargs):
        captured.setdefault("cmds", []).append(cmd)
        return FakeProc()
    monkeypatch.setattr(runner.subprocess, "run", fake_run)
    subj = _write_subject(str(tmp_path))
    original = _module(os.path.join(subj["src"], "subject_mod.py"))
    mutated = _full_module(original, "return n > 0 and True")  # survives
    verdict = runner.run_mutant(subj["dir"], "subject_mod.py", mutated,
                                src_dir=subj["src"], python="/venv/bin/python")
    assert verdict == "survived"
    assert captured["cmds"], "expected a pytest subprocess to be launched"
    assert captured["cmds"][0][0] == "/venv/bin/python"
    assert captured["cmds"][0][1:3] == ["-m", "pytest"]


def test_junit_nodeid_reconstruction():
    """T001: nodeid = classname::name (plan-review finding #7).

    Pinned against real pytest junit output (verified on guineapig):
    <testcase classname="tests.test_pricing" name="test_..."> -> nodeid
    "tests.test_pricing::test_...". This test exercises the private
    reconstruction helper over a sampled junit doc.
    """
    import xml.etree.ElementTree as ET
    root = ET.fromstring(
        '<testsuite><testcase classname="tests.test_pricing" name="test_zero"/>'
        '<testcase classname="tests.test_pricing" name="test_killed"><failure/></testcase>'
        '<testcase classname="tests.test_pricing" name="test_errored"><error/></testcase>'
        '</testsuite>')
    ids = runner._junit_failing_ids(root)
    # test_zero passed (no failure/error child) -> not in the failing list;
    # test_killed (<failure/>) and test_errored (<error/>) are included.
    assert ids == ["tests.test_pricing::test_killed",
                   "tests.test_pricing::test_errored"]
