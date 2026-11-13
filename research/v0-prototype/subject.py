"""Subject under mutation: triage-engine.

Keeps the real repo untouched. Each mutant is materialized in a scratch dir,
and pytest runs against the mutant via PYTHONPATH priority (mutant dir shadows
src/engine.py) so `import engine` resolves to the mutant.
"""
import os

SUBJECT_REPO = os.path.expanduser("~/projects/triage-engine")
SUBJECT_FILE = os.path.join(SUBJECT_REPO, "src", "engine.py")
ORACLE = ["tests", "test_engine.py"]  # relative to repo root
PYTHON = os.path.join(SUBJECT_REPO, ".venv", "bin", "python")


def oracle_abs():
    return os.path.join(SUBJECT_REPO, *ORACLE)


def subject_py():
    return SUBJECT_FILE
