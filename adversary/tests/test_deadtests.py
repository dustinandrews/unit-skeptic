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


def test_run_deadtests_threads_src_rel_tests_rel_python(tmp_path, monkeypatch):
    """Sprint 7: run_deadtests forwards --src-rel/--tests-rel/--python.

    Review finding (deleg_11db05f4): the deadtests threading was implemented
    but untested. Verify src_rel resolves src_dir, and tests_rel/python reach
    both runner.run_mutant and _baseline_test_ids by capturing their kwargs.
    """
    import textwrap
    from adversary import deadtests, runner

    src = tmp_path / "src"
    src.mkdir(parents=True)
    (src / "mod.py").write_text("def is_positive(n):\n    return n > 0\n")
    tests = tmp_path / "tests"
    tests.mkdir()
    (tests / "test_mod.py").write_text(
        textwrap.dedent("""\
            from mod import is_positive
            def test_positive():
                assert is_positive(5)
        """))

    calls = {"mutant": [], "baseline": []}

    def fake_run_mutant(subject_dir, module_rel, mutated, **kw):
        calls["mutant"].append(kw)
        return ("survived", [])

    def fake_baseline(subject_dir, src_dir, **kw):
        calls["baseline"].append(kw)
        return ["mod::test_positive"]

    monkeypatch.setattr(runner, "run_mutant", fake_run_mutant)
    monkeypatch.setattr(deadtests, "_baseline_test_ids", fake_baseline)

    doc = deadtests.run_deadtests(str(tmp_path), src_rel="src",
                                  tests_rel="src/tests", python="/v/bin/python")

    assert json.loads(doc)["total"] == 1
    # run_mutant got the threaded flags + a src_dir resolved from src_rel.
    assert calls["mutant"], "expected run_mutant to be invoked"
    assert all(kw["tests_rel"] == "src/tests" for kw in calls["mutant"])
    assert all(kw["python"] == "/v/bin/python" for kw in calls["mutant"])
    assert all(kw["src_dir"] == str(src) for kw in calls["mutant"])
    # _baseline_test_ids threaded tests_rel/python (the hardcoded seam).
    assert calls["baseline"], "expected _baseline_test_ids to be invoked"
    assert calls["baseline"][0]["tests_rel"] == "src/tests"
    assert calls["baseline"][0]["python"] == "/v/bin/python"


# ---------------------------------------------------------------------------
# Dead-test explanation (Sprint 9, mechanical; class-region topology)
# ---------------------------------------------------------------------------

def test_class_region_prefix_before_final_ddot():
    """Sprint 9: nodeid class region = prefix before the FINAL ::."""
    assert deadtests._class_region("tests.test_svc.TestSvc::test_a") == "tests.test_svc.TestSvc"
    assert deadtests._class_region("tests.test_svc::test_b") == "tests.test_svc"
    # nested (file::Class::name) — only strip the final component.
    assert deadtests._class_region("m.py::C::test_x") == "m.py::C"


def test_class_region_fallback_when_no_ddot():
    """Sprint 9 (L1): a bare nodeid with no :: is its own region."""
    assert deadtests._class_region("tests.test_solo") == "tests.test_solo"


def test_reason_case_A_corpus_poverty():
    """Sprint 9: dead test, class region has no sibling kills -> CASE A."""
    totals = {"tests.test_a": 0, "tests.test_b": 2}
    r = deadtests.reason("tests.test_a::t1", 0, totals)
    assert r == "no behavior-changing mutant landed in this test's class (corpus poverty)"


def test_reason_case_B_regional_noop():
    """Sprint 9: dead test, class region HAS sibling kills -> CASE B names N."""
    totals = {"tests.test_svc": 3}
    r = deadtests.reason("tests.test_svc::t_dead", 0, totals)
    assert r == "caught 0 mutants; sibling tests in class caught 3"


def test_reason_alive_confirmation():
    """Sprint 9: alive test -> confirmation with its kill count."""
    r = deadtests.reason("tests.test_svc::t_strong", 2, {"tests.test_svc": 2})
    assert r == "caught 2 mutants"


def test_classify_emits_class_and_reason():
    """Sprint 9: classify wires class + reason for each entry."""
    kill_map = {
        "tests.test_cls::t_strong": 2,
        "tests.test_cls::t_weak": 0,   # sibling (t_strong) has kills -> CASE B
        "tests.test_other::t_lone": 0,  # no sibling kills -> CASE A
    }
    c = deadtests.classify(kill_map)
    assert c["tests.test_cls::t_strong"]["class"] == "tests.test_cls"
    assert c["tests.test_cls::t_strong"]["status"] == "alive"
    assert c["tests.test_cls::t_weak"]["reason"] == \
        "caught 0 mutants; sibling tests in class caught 2"
    assert c["tests.test_other::t_lone"]["reason"] == \
        "no behavior-changing mutant landed in this test's class (corpus poverty)"


def test_run_deadtests_emits_mechanical_reasons(tmp_path, monkeypatch):
    """Sprint 9 (SC-002): run_deadtests JSON carries class-reason mechanical
    explanations. We patch the true non-pure deps (subprocess/pytest): run_mutant,
    sites.find_sites, DeterministicMutator, _baseline_test_ids.
    """
    import textwrap
    from adversary import deadtests, runner, sites
    from adversary.mutators import DeterministicMutator

    src = tmp_path / "src"
    src.mkdir(parents=True)
    (src / "mod.py").write_text("def is_positive(n):\n    return n > 0\n")
    tests = tmp_path / "tests"
    tests.mkdir()
    (tests / "test_mod.py").write_text(
        textwrap.dedent("""\
            class TestStrong:
                def test_a(self):
                    assert True
                def test_b(self):
                    assert True
            class TestLone:
                def test_c(self):
                    assert True
        """))

    # Fake a driver: return a consistent (verdict, failing_ids) trace with a
    # two-class topology: t_a and t_b both kill something in TestStrong; t_c
    # (TestLone) never fails -> CASE A. t_b also fails on fewer -> still alive.
    fail_strong_a = ["tests.test_mod.TestStrong::test_a"]
    fail_strong_b = ["tests.test_mod.TestStrong::test_a",
                     "tests.test_mod.TestStrong::test_b"]

    calls = {"mutant": []}

    def fake_run_mutant(subject_dir, module_rel, mutated, **kw):
        calls["mutant"].append(1)
        i = len(calls["mutant"])
        if i == 1:
            return ("killed", fail_strong_a)
        return ("killed", fail_strong_b)

    def fake_sites(source, **kw):
        # two sites so run_deadtests iterates twice
        return [{"start": 0, "end": 1, "text": ">", "kind": "Cmp"},
                {"start": 1, "end": 2, "text": ">", "kind": "Cmp"}]

    monkeypatch.setattr(runner, "run_mutant", fake_run_mutant)
    monkeypatch.setattr(sites, "find_sites", fake_sites)
    monkeypatch.setattr(DeterministicMutator, "mutate",
                        lambda self, site: [">="])
    monkeypatch.setattr(deadtests, "_baseline_test_ids",
                        lambda *a, **k: list(fail_strong_a) + list(fail_strong_b) +
                        ["tests.test_mod.TestLone::test_c"])

    doc = json.loads(deadtests.run_deadtests(str(tmp_path)))
    by_id = {t["test_id"]: t for t in doc["tests"]}

    assert by_id["tests.test_mod.TestStrong::test_a"]["kills"] == 2
    assert by_id["tests.test_mod.TestStrong::test_a"]["reason"] == "caught 2 mutants"
    assert by_id["tests.test_mod.TestStrong::test_b"]["status"] == "alive"
    assert by_id["tests.test_mod.TestLone::test_c"]["status"] == "dead"
    assert by_id["tests.test_mod.TestLone::test_c"]["class"] == "tests.test_mod.TestLone"
    assert by_id["tests.test_mod.TestLone::test_c"]["reason"] == \
        "no behavior-changing mutant landed in this test's class (corpus poverty)"
    assert all("class" in t and "reason" in t for t in doc["tests"])
