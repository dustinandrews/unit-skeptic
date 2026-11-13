"""Boundary-covering test battery for the guineapig pricing package.

This is the GOOD oracle suite for later mutation testing — it protects the
documented contracts. Deliberate weak tests live in test_weak.py (FR-007).
"""
import math
import pytest

from guineapig.pricing import (
    apply_tier_discount,
    is_taxable,
    round_cents,
    tax_rate,
    tier_discount,
)


# --- tier_discount ------------------------------------------------------------

def test_tier_zero_qty_is_zero_discount():
    assert tier_discount(0) == 0.0


def test_tier_below_cutoff_returns_zero():
    for q in (1, 2, 3, 4):
        assert tier_discount(q) == 0.0


def test_tier_lower_band():
    for q in (5, 6, 7, 8, 9):
        assert tier_discount(q) == 0.05


def test_tier_upper_band():
    for q in (10, 11, 100):
        assert tier_discount(q) == 0.10


def test_tier_cutoff_boundary_5_and_10():
    assert tier_discount(4) != tier_discount(5)
    assert tier_discount(9) != tier_discount(10)


def test_tier_negative_rejected():
    with pytest.raises(ValueError):
        tier_discount(-1)


def test_tier_non_integer_rejected():
    with pytest.raises(ValueError):
        tier_discount("5")


# --- apply_tier_discount ------------------------------------------------------

def test_apply_zero_qty_is_zero():
    assert apply_tier_discount(10.0, 0) == 0.0


def test_apply_no_discount_small_qty():
    assert math.isclose(apply_tier_discount(10.0, 3), 30.0)


def test_apply_lower_band_applied():
    assert math.isclose(apply_tier_discount(10.0, 5), 47.5)  # 5% off


def test_apply_upper_band_applied():
    assert math.isclose(apply_tier_discount(10.0, 10), 90.0)  # 10% off


def test_apply_zero_unit_price():
    assert apply_tier_discount(0.0, 10) == 0.0


def test_apply_negative_price_rejected():
    with pytest.raises(ValueError):
        apply_tier_discount(-5.0, 2)


def test_apply_negative_qty_rejected():
    with pytest.raises(ValueError):
        apply_tier_discount(5.0, -2)


# --- is_taxable ---------------------------------------------------------------

def test_gift_nontaxable():
    assert is_taxable("CA", "gift") is False


def test_regular_item_taxable_in_taxable_region():
    assert is_taxable("CA", "book") is True


def test_exempt_region_returns_false():
    assert is_taxable("OR", "book") is False


def test_empty_region_rejected():
    with pytest.raises(ValueError):
        is_taxable("", "book")


def test_empty_kind_rejected():
    with pytest.raises(ValueError):
        is_taxable("CA", "")


# --- tax_rate -----------------------------------------------------------------

def test_known_region_rate():
    assert tax_rate("CA") == 0.0825
    assert tax_rate("NY") == 0.04


def test_unknown_region_default_fallback():
    assert tax_rate("ZZ") == 0.0


def test_tax_rate_empty_region_rejected():
    with pytest.raises(ValueError):
        tax_rate("")


# --- round_cents --------------------------------------------------------------

def test_round_down():
    assert round_cents(1.234) == 123


def test_round_up():
    assert round_cents(1.235) == 124


def test_half_penny_edge_rounds_up():
    assert round_cents(1.005) == 101  # exact half-penny boundary


def test_whole_dollars():
    assert round_cents(2.0) == 200


def test_zero():
    assert round_cents(0.0) == 0


def test_negative_rejected():
    with pytest.raises(ValueError):
        round_cents(-0.5)


def test_non_numeric_rejected():
    with pytest.raises((TypeError, ValueError)):
        round_cents("abc")
