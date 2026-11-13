"""DELIBERATE weak/pointless tests (FR-007).

These pass trivially no matter what the pricing functions do — they call no real
behavior, or assert a tautology. They exist so the later dead-test detector (Phase
2) has verifiable ground truth: all four below SHOULD be flagged as dead/useless
because they never exercise the code under test. Keep this file's purpose obvious.
"""
import pytest


def test_weak_tautology_always_true():
    assert True


def test_weak_constant_against_itself():
    x = 42
    assert x == x


def test_weak_assert_none_is_none():
    assert None is None


def test_weak_no_behavior_called():
    # Imports nothing from guineapig; would pass even if pricing were deleted.
    assert "the quick brown fox".startswith("the")
