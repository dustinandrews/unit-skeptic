"""AST site enumeration: Compare/BoolOp/call-arg/constant -> Site (char start/end, text, kind)."""
import pytest

from adversary.sites import find_sites


SAMPLE = (
    "def f(a, b, n):\n"
    "    if a == b and n > 0:\n"
    "        return a\n"
    "    return round(n / 2)\n"
)


def test_enumerates_compare_and_boolop():
    sites = find_sites(SAMPLE)
    kinds = [s["kind"] for s in sites]
    assert "Compare" in kinds
    assert "BoolOp" in kinds


def test_site_has_correct_offsets_and_text():
    sites = find_sites(SAMPLE)
    compare = [s for s in sites if s["kind"] == "Compare"][0]
    assert compare["text"] == "a == b"
    assert SAMPLE[compare["start"]:compare["end"]] == compare["text"]


def test_site_offsets_include_preceding_lines():
    sites = find_sites(SAMPLE)
    # "n > 0" lives on line 2, so its start must account for the full first line.
    n_compare = [s for s in sites if "n > 0" in s["text"]]
    assert n_compare
    assert n_compare[0]["start"] >= len("def f(a, b, n):\n")
    # And the offset points exactly at the source text.
    s = n_compare[0]
    assert SAMPLE[s["start"]:s["end"]] == s["text"]


def test_no_sites_in_empty_source():
    assert find_sites("") == []


def test_no_sites_when_none_present():
    assert find_sites("x = 1 + 2\n") == []
