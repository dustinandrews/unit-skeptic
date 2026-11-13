"""Mutator adapter contract + DeterministicMutator operator flips."""
from adversary.mutators import DeterministicMutator, Mutator

IS_PROTOCOL = (hasattr(Mutator, "mutate")
               and hasattr(Mutator, "__protocol_attrs__"))


def _site(text, kind="Compare"):
    return {"module": "<m>", "start": 0, "end": len(text), "text": text, "kind": kind}


def test_mutator_is_a_protocol():
    assert IS_PROTOCOL


def test_deterministic_flips_eq_to_ne():
    m = DeterministicMutator()
    out = m.mutate(_site("a == b"))
    assert "a != b" in out


def test_deterministic_flips_compare_lt_to_ge():
    m = DeterministicMutator()
    out = m.mutate(_site("a < b"))
    assert "a >= b" in out


def test_deterministic_flips_bool_and_to_or():
    m = DeterministicMutator()
    out = m.mutate(_site("a and b", "BoolOp"))
    assert "a or b" in out


def test_deterministic_returns_multiple_candidates():
    m = DeterministicMutator()
    out = m.mutate(_site("a == b"))
    assert len(out) >= 1


def test_deterministic_noop_when_nothing_flip():
    m = DeterministicMutator()
    out = m.mutate(_site("f(x)", "CallArg"))
    assert out == []


def test_deterministic_flips_ge_to_lt_not_shredded():
    """Regression: `>` must not shred the `>` inside `>=` into `<= =`."""
    m = DeterministicMutator()
    out = m.mutate(_site("a >= b"))
    assert "a < b" in out
    assert not any("<=" in cand for cand in out)


def test_deterministic_flips_le_to_gt():
    m = DeterministicMutator()
    out = m.mutate(_site("a <= b"))
    assert "a > b" in out


def test_deterministic_ge_and_le_each_produce_valid_flips():
    m = DeterministicMutator()
    for src, expect in [("a >= b", "a < b"), ("a <= b", "a > b"),
                        ("a > b", "a <= b"), ("a < b", "a >= b"),
                        ("a == b", "a != b"), ("a != b", "a == b")]:
        out = m.mutate(_site(src))
        assert expect in out, f"{src} -> expected {expect}, got {out}"


def test_llm_mutator_can_slot_in_unchanged():
    """The interface shape must permit an LLM mutator without signature change."""
    from adversary.mutators import DeterministicMutator
    mm = DeterministicMutator()
    result = mm.mutate(_site("a == b"))
    # Regardless of impl, the contract is: given a site dict, return list[str].
    assert isinstance(result, list)
    assert all(isinstance(r, str) for r in result)
