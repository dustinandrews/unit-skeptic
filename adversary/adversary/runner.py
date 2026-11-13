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

DEFAULT_TIMEOUT_S = 30


def _pytest(cmd, subject_dir, env, timeout_s):
    t0 = time.time()
    try:
        proc = subprocess.run(cmd, cwd=subject_dir, env=env,
                              capture_output=True, timeout=timeout_s)
        return proc, time.time() - t0
    except subprocess.TimeoutExpired:
        return None, time.time() - t0


def run_oracle(subject_dir, src_dir, tests_rel="tests", timeout_s=DEFAULT_TIMEOUT_S):
    """Run the subject's pytest suite against a clean src. Return (rc, secs, note)."""
    env = dict(os.environ)
    env["PYTHONPATH"] = os.path.abspath(src_dir) + os.pathsep + env.get("PYTHONPATH", "")
    proc, secs = _pytest(
        [sys.executable, "-m", "pytest", tests_rel, "-q", "-p",
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
               tests_rel="tests", timeout_s=DEFAULT_TIMEOUT_S):
    """Run the subject suite against a mutated copy of one module.

    `module_rel` is the module's path RELATIVE to `src_dir` (e.g.
    "subject_mod.py" or "guineapig/pricing.py"). The mutant is written to a
    scratch dir that mirrors module_rel, and PYTHONPATH is
    scratch:src_dir so the mutant shadows the real module. Any `__init__.py`
    files enclosing module_rel are copied into the shadow so package dirs stay
    REGULAR packages (a namespace shadow won't override a real package).

    Returns a mechanical verdict: killed / survived / error / timeout.
    """
    try:
        ast.parse(mutated_source)
    except SyntaxError:
        return "error"
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
        proc, _ = _pytest(
            [sys.executable, "-m", "pytest", tests_rel, "-q", "-p",
             "no:cacheprovider", "-o", "pythonpath="],
            subject_dir, env, timeout_s,
        )
        if proc is None:
            return "timeout"
        return "survived" if proc.returncode == 0 else "killed"
    finally:
        shutil.rmtree(scratch, ignore_errors=True)
