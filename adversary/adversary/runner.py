"""Runner: green-gate + scratch-dir shadowed pytest runs -> mechanical verdicts.

The real subject repo is NEVER modified. Each mutant is materialized into a
scratch dir that mirrors the module's relative path, and the subject's test
suite runs against that shadow (PYTHONPATH shadow-first, pytest `pythonpath`
disabled so the mutant actually loads). Verdicts are mechanical.
"""
import ast
import os
import shutil
import subprocess
import sys
import tempfile
import time
import xml.etree.ElementTree as ET

DEFAULT_TIMEOUT_S = 120


def _junit_failing_ids(root):
    """Return nodeids of tests that FAILED or ERRORED, in document order.

    Nodeid is reconstructed as ``classname::name`` (pytest junit emits
    ``<testcase classname="..." name="...">``). A testcase with no
    failure/error child passed (not included).
    """
    ids = []
    for tc in root.iter("testcase"):
        failed = tc.find("failure") is not None or tc.find("error") is not None
        if failed:
            cls = tc.get("classname", "")
            name = tc.get("name", "")
            ids.append(f"{cls}::{name}" if cls else name)
    return ids


def _junit_all_ids(root):
    """Return nodeids of ALL testcases (passed or failed), in document order.

    Used to enumerate the complete test list from the green-gate run so that
    tests with zero kills (dead tests) still appear in the output with a row.
    """
    ids = []
    for tc in root.iter("testcase"):
        cls = tc.get("classname", "")
        name = tc.get("name", "")
        ids.append(f"{cls}::{name}" if cls else name)
    return ids


def _pytest(cmd, subject_dir, env, timeout_s):
    t0 = time.time()
    try:
        proc = subprocess.run(cmd, cwd=subject_dir, env=env,
                              capture_output=True, timeout=timeout_s)
        return proc, time.time() - t0
    except subprocess.TimeoutExpired:
        return None, time.time() - t0


def run_oracle(subject_dir, src_dir, tests_rel="tests", python=None,
               timeout_s=DEFAULT_TIMEOUT_S):
    """Run the subject's pytest suite against a clean src. Return (rc, secs, note)."""
    env = dict(os.environ)
    env["PYTHONPATH"] = os.path.abspath(src_dir) + os.pathsep + env.get("PYTHONPATH", "")
    py = python or sys.executable
    proc, secs = _pytest(
        [py, "-m", "pytest", tests_rel, "-q", "-p",
         "no:cacheprovider", "-o", "pythonpath="],
        subject_dir, env, timeout_s,
    )
    if proc is None:
        return None, secs, "timeout"
    return proc.returncode, secs, ""


def _copy_pkg_inits(scratch, module_rel, src_dir):
    """Copy enclosing package __init__.py files into the shadow dir.

    For each ancestor directory of module_rel (e.g. "guineapig"), if src_dir
    has a corresponding __init__.py, write it into the scratch shadow so that
    directory is a regular package there too.
    """
    parts = module_rel.split(os.sep)
    for i in range(1, len(parts)):
        rel_dir = os.path.join(*parts[:i])
        src_init = os.path.join(src_dir, rel_dir, "__init__.py")
        if os.path.isfile(src_init):
            dst_init = os.path.join(scratch, rel_dir, "__init__.py")
            os.makedirs(os.path.dirname(dst_init), exist_ok=True)
            shutil.copyfile(src_init, dst_init)


def run_mutant(subject_dir, module_rel, mutated_source, src_dir=None,
               tests_rel="tests", python=None, timeout_s=DEFAULT_TIMEOUT_S,
               junit_path=None):
    """Run the subject suite against a mutated copy of one module.

    `module_rel` is the module's path RELATIVE to `src_dir` (e.g.
    "subject_mod.py" or "guineapig/pricing.py"). The mutant is written to a
    scratch dir that mirrors module_rel, and PYTHONPATH is
    scratch:src_dir so the mutant shadows the real module. Any `__init__.py`
    files enclosing module_rel are copied into the shadow so package dirs stay
    REGULAR packages (a namespace shadow won't override a real package).

    Returns a mechanical verdict: killed / survived / error / timeout.

    When `junit_path` is set (absolute path for per-test attribution), the
    pytest run also emits a junit report there and the verdict becomes a
    tuple ``(verdict, failing_ids)`` where failing_ids are the nodeids
    (classname::name) of the tests that failed/errored — parsed BEFORE the
    scratch cleanup. Without `junit_path` the plain verdict string is
    returned (backward-compatible with the score loop). The env sets
    PYTHONDONTWRITEBYTECODE=1 so pytest cannot drop __pycache__/*.pyc into
    the tracked subject (SC-004 robustness).
    """
    try:
        ast.parse(mutated_source)
    except SyntaxError:
        return ("error", []) if junit_path else "error"
    scratch = tempfile.mkdtemp(prefix="adv_mutant_")
    try:
        dst = os.path.join(scratch, module_rel)
        os.makedirs(os.path.dirname(dst) or scratch, exist_ok=True)
        with open(dst, "w") as fh:
            fh.write(mutated_source)
        # Copy enclosing __init__.py files so shadow package dirs are regular.
        if src_dir:
            _copy_pkg_inits(scratch, module_rel, src_dir)
        env = dict(os.environ)
        path = [os.path.abspath(scratch)]
        if src_dir:
            path.append(os.path.abspath(src_dir))
        env["PYTHONPATH"] = os.pathsep.join(path) + os.pathsep + env.get("PYTHONPATH", "")
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        py = python or sys.executable
        cmd = [py, "-m", "pytest", tests_rel, "-q", "-p",
               "no:cacheprovider", "-o", "pythonpath="]
        if junit_path is not None:
            # Must be absolute: a relative path resolves against the CALLING
            # process cwd (not the subject), silently polluting whatever dir
            # the caller happened to run from (SC-004). Reject it outright.
            if not os.path.isabs(junit_path):
                raise ValueError(f"junit_path must be absolute: {junit_path!r}")
            cmd += ["--junitxml=" + junit_path]
        proc, _ = _pytest(cmd, subject_dir, env, timeout_s)
        if proc is None:
            return ("timeout", []) if junit_path else "timeout"
        verdict = "survived" if proc.returncode == 0 else "killed"
        if junit_path is None:
            return verdict
        # Parse BEFORE scratch rmtree (post-hoc read would be deleted).
        failing = []
        if os.path.isfile(os.path.abspath(junit_path)):
            try:
                failing = _junit_failing_ids(ET.parse(os.path.abspath(junit_path)).getroot())
            except ET.ParseError:
                failing = []
        return (verdict, failing)
    finally:
        shutil.rmtree(scratch, ignore_errors=True)
