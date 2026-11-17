"""andy.py: LLM Andy driver (Sprint 4).

Covers FR-002 (prompt built from subject source only; PLACEHOLDER blanking),
SC-003 (structural blindness: prompt never references tests), FR-003 + key
hygiene (transport seam, offline stub), FR-004 (dedupe/non-empty/differ),
SC-001 (LlmMutator is a runtime_checkable Mutator), FR-008 (offline
reproducibility), and the CLI wiring (FR-005/006 / SC-002 / SC-004).
"""
import json
import os

from adversary import andy, cli, equiv, sites
from adversary.mutators import Mutator


# ---------------------------------------------------------------------------
# Prompt builder (FR-002 / SC-003)
# ---------------------------------------------------------------------------

SRC = (
    "def is_positive(n):\n"
    "    return n > 0\n"
)


def _site(subject_src, target="n > 0"):
    start = subject_src.index(target)
    return {"module": "m.py", "start": start, "end": start + len(target),
            "text": target, "kind": "Compare"}


def test_prompt_blanks_site_and_keeps_enclosing_function():
    site = _site(SRC)
    prompt = andy.build_prompt(SRC, site, trials=2)
    assert andy.PLACEHOLDER in prompt
    assert "def is_positive(n):" in prompt  # enclosing function present
    assert "n > 0" not in prompt  # the original region is blanked
    assert "{n}" not in prompt  # template formatted
    assert "2 distinct replacement" in prompt or "exactly 2" in prompt


def test_prompt_built_from_subject_source_only_never_refs_tests():
    """SC-003: the prompt string never contains the tests-directory sense of
    test/coverage/verdict/survivor — it references only subject code + PLACEHOLDER."""
    site = _site(SRC)
    prompt = andy.build_prompt(SRC, site, trials=1)
    for forbidden in ("test", "coverage", "verdict", "survivor", "pytest"):
        assert forbidden.lower() not in prompt.lower(), forbidden
    assert andy.PLACEHOLDER in prompt


def test_prompt_uses_equiv_block_builder_for_guineapig_site():
    gp = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                      "..", "..", "guineapig", "src",
                                      "guineapig", "pricing.py"))
    if not os.path.exists(gp):
        import pytest
        pytest.skip("guineapig subject not present")
    source = open(gp).read()
    cmp_site = [s for s in sites.find_sites(source) if s["kind"] == "Compare"][0]
    prompt = andy.build_prompt(source, dict(cmp_site), trials=1)
    assert andy.PLACEHOLDER in prompt
    assert "def tier_discount(quantity):" in prompt
    # the prompt never leaks the original site text or any test artifact
    for forbidden in ("test", "verdict", "survivor"):
        assert forbidden not in prompt


def test_build_prompt_matches_equiv_builder_output_for_kind():
    """/bug guard: the prompt's enclosing function equals what equiv's A/B
    builder produces with a PLACEHOLDER replacement (the "minus the original"
    Sprint-3 extraction)."""
    site = _site(SRC)
    blocks = equiv.build_blocks(SRC, {"start": site["start"], "end": site["end"],
                                      "replacement": andy.PLACEHOLDER})
    assert blocks["func_b"] in andy.build_prompt(SRC, site, trials=1)


# ---------------------------------------------------------------------------
# parse_reply (FR-004)
# ---------------------------------------------------------------------------

def test_parse_reply_dedupes_drops_empty_and_identity():
    reply = (
        "<snippet>n < 0</snippet>\n"
        "<snippet>n <= 0</snippet>\n"
        "<snippet>n < 0</snippet>\n"          # duplicate
        "<snippet>   </snippet>\n"            # empty
        "<snippet>n > 0</snippet>\n"          # equals orig -> identity, dropped
        "<snippet>not n > 0</snippet>\n"
    )
    cands = andy.parse_reply(reply, "n > 0")
    assert cands == ["n < 0", "n <= 0", "not n > 0"]


def test_parse_reply_fenced_fallback_when_no_tags():
    reply = '```python\nn < 0\n```'
    assert andy.parse_reply(reply, "n > 0") == ["n < 0"]


def test_parse_reply_empty_and_garbage():
    assert andy.parse_reply("", "n > 0") == []
    assert andy.parse_reply("no snippets here", "n > 0") == []


# ---------------------------------------------------------------------------
# LlmMutator (SC-001 / FR-001 / FR-004)
# ---------------------------------------------------------------------------

def test_llm_mutator_is_runtime_checkable_mutator():
    m = andy.LlmMutator(SRC, complete=lambda p: "<snippet>n < 0</snippet>")
    assert isinstance(m, Mutator)  # SC-001: satisfies the adapter Protocol


def test_llm_mutator_mutate_returns_candidates_from_complete():
    m = andy.LlmMutator(SRC, model="m/1", trials=2,
                        complete=lambda p: "<snippet>n < 0</snippet>"
                                           "<snippet>n <= 0</snippet>")
    cands = m.mutate(_site(SRC))
    assert cands == ["n < 0", "n <= 0"]


def test_llm_mutator_default_transport_offline_no_key():
    # constructing with the offline seam requires no key and no network
    m = andy.LlmMutator(SRC, trials=1, complete=andy.offline_complete)
    cands = m.mutate(_site(SRC))
    assert cands  # deterministic canned candidates, no key needed


def test_llm_mutator_never_sends_survivors_or_tests_in_complete_arg():
    captured = {}

    def spy(prompt):
        captured["prompt"] = prompt
        return "<snippet>n < 0</snippet>"

    m = andy.LlmMutator(SRC, complete=spy)
    m.mutate(_site(SRC))
    assert andy.PLACEHOLDER in captured["prompt"]
    assert "n > 0" not in captured["prompt"]  # original site blanked out
    assert "test" not in captured["prompt"]


# ---------------------------------------------------------------------------
# Offline stub (FR-008 / NFR-003)
# ---------------------------------------------------------------------------

def test_offline_complete_deterministic_and_reproducible():
    a = andy.offline_complete("...def tax_rate(region):...")
    b = andy.offline_complete("...def tax_rate(region):...")
    assert a == b  # terminal reliability: same input -> same output
    assert "<snippet>" in a


def test_offline_complete_routes_and_has_default():
    assert andy.offline_complete("def tier_discount(quantity):\n x") \
        == "<snippet>quantity > 10</snippet>"
    # no marker -> deterministic default
    assert andy.offline_complete("def unknown(foo):\n x") == andy.DEFAULT_OFFLINE_REPLY


# ---------------------------------------------------------------------------
# Real transport (FR-003 key hygiene)
# ---------------------------------------------------------------------------

def test_real_complete_puts_key_in_header_not_body_or_prompt():
    """FR-003: the OpenRouter body/prompt never carry the API key; it travels
    only in the Authorization header."""
    captured = {}

    def fake_post(url, body, headers):
        captured["url"], captured["body"], captured["headers"] = url, body, headers
        return json.dumps({"choices": [{"message": {"content": "<snippet>x</snippet>"}}]})

    key = "«redacted:sk-live-key»"
    out = andy.real_complete("probe prompt", model="m/1", api_key=key,
                             http_post=fake_post)
    assert out == "<snippet>x</snippet>"
    body = captured["body"].decode("utf-8") if isinstance(captured["body"], bytes) else captured["body"]
    assert key not in body
    assert key not in "probe prompt"
    assert captured["headers"]["Authorization"] == f"Bearer {key}"
    assert "probe prompt" in json.loads(body)["messages"][0]["content"]


def test_real_complete_requires_key():
    os.environ.pop("OPENROUTER_API_KEY", None)
    try:
        andy.real_complete("p", http_post=lambda *_: "{}")
        assert False, "expected RuntimeError when no key configured"
    except RuntimeError as e:
        assert "OPENROUTER_API_KEY" in str(e)


# ---------------------------------------------------------------------------
# CLI wiring (FR-005/006 / SC-002 / SC-004)
# ---------------------------------------------------------------------------

def _make_subject(tmp_path):
    src = tmp_path / "src" / "pkg"
    src.mkdir(parents=True, exist_ok=True)
    (src / "__init__.py").write_text("")
    (src / "mod.py").write_text("def is_positive(n):\n    return n > 0\n")
    tests = tmp_path / "tests"
    tests.mkdir(exist_ok=True)
    (tests / "test_mod.py").write_text(
        "from pkg.mod import is_positive\n"
        "def test_pos():\n    assert is_positive(5)\n")
    return str(tmp_path)


def test_cli_score_llm_offline_prints_mutator(tmp_path, capsys, monkeypatch):
    subject = _make_subject(tmp_path)
    monkeypatch.chdir(tmp_path)
    rc = cli.run_score(subject, mutator="llm", offline=True)
    assert rc == 0
    out = capsys.readouterr().out
    assert "mutator=llm" in out
    assert "score =" in out


def test_cli_score_llm_offline_attributes_survivors(tmp_path, monkeypatch):
    subject = _make_subject(tmp_path)
    monkeypatch.chdir(tmp_path)
    cli.run_score(subject, mutator="llm", offline=True)
    records = json.load(open(os.path.join(tmp_path, "survivors.json")))
    assert records  # at least one candidate produced and ran
    assert all(r["mutator"] == "llm" for r in records)
    assert all(r["model"] == andy.DEFAULT_MODEL for r in records)


def test_cli_score_default_deterministic_attributes(tmp_path, monkeypatch):
    subject = _make_subject(tmp_path)
    monkeypatch.chdir(tmp_path)
    cli.run_score(subject)  # default deterministic
    records = json.load(open(os.path.join(tmp_path, "survivors.json")))
    assert all(r["mutator"] == "deterministic" for r in records)


def test_cli_score_help_lists_new_flags(capsys):
    try:
        cli.main(["score", "--help"])
    except SystemExit as e:
        assert e.code == 0
    out = capsys.readouterr().out
    for flag in ("--mutator", "--model", "--trials-per-site", "--offline"):
        assert flag in out


def _run(*argv):
    from adversary import cli as _cli
    try:
        return _cli.main(list(argv))
    except SystemExit as e:
        return e.code


def test_cli_main_llm_offline_via_argv(tmp_path, monkeypatch):
    """SC-002 end-to-end through main(): `adversary score --subject <dir>
    --mutator llm --offline` runs to completion and prints mutator=llm."""
    subject = _make_subject(tmp_path)
    monkeypatch.chdir(tmp_path)
    rc = _run("score", "--subject", subject, "--mutator", "llm", "--offline")
    assert rc == 0


def test_andy_imports_stdlib_only():
    """NFR-001: andy.py ships no third-party runtime imports.

    Only stdlib modules (plus the in-repo adversary.equiv) may appear in
    andy.py's import set. AST-audits the source so the constraint is a
    regression guard, not true-by-inspection.
    """
    import ast
    import pathlib
    allowed = {"adversary", "json", "os", "re", "urllib"}
    tree = ast.parse(pathlib.Path(andy.__file__).read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                assert root in allowed, f"non-stdlib import in andy.py: {alias.name}"
        elif isinstance(node, ast.ImportFrom) and node.module:
            root = node.module.split(".")[0]
            assert root in allowed, f"non-stdlib import in andy.py: {node.module}"
