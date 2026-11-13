"""Pure pricing functions for the guineapig mutation-testing toy.

All functions are pure and total. Invalid input raises ValueError (or TypeError
for a non-numeric where the type is meaningless). Contracts documented here are
the ground truth the boundary test suite protects.
"""
from decimal import Decimal


def tier_discount(quantity):
    """Tiered discount rate by quantity. Thresholds: 0-4 -> 0.0, 5-9 -> 0.05, 10+ -> 0.10."""
    if not isinstance(quantity, int) or quantity < 0:
        raise ValueError("quantity must be a non-negative int")
    if quantity >= 10:
        return 0.10
    if quantity >= 5:
        return 0.05
    return 0.0


def apply_tier_discount(unit_price, quantity):
    """Total price after tier discount: unit_price * quantity * (1 - tier_discount)."""
    if not isinstance(unit_price, (int, float)) or unit_price < 0:
        raise ValueError("unit_price must be a non-negative number")
    if not isinstance(quantity, int) or quantity < 0:
        raise ValueError("quantity must be a non-negative int")
    rate = tier_discount(quantity)
    return unit_price * quantity * (1 - rate)


def is_taxable(region, item_kind):
    """True if an item is taxable. Gifts are nontaxable; OR/AK/EU exempt regions are not taxable."""
    if not region or not isinstance(region, str):
        raise ValueError("region must be a non-empty str")
    if not item_kind or not isinstance(item_kind, str):
        raise ValueError("item_kind must be a non-empty str")
    exempt_regions = {"OR", "AK", "EU"}
    if item_kind == "gift":
        return False
    return region not in exempt_regions


def tax_rate(region):
    """Tax rate for a region, with default 0.0 fallback for unknown regions."""
    if not region or not isinstance(region, str):
        raise ValueError("region must be a non-empty str")
    rates = {"CA": 0.0825, "NY": 0.04, "WA": 0.065, "TX": 0.0625}
    return rates.get(region, 0.0)


def round_cents(amount):
    """Round a dollar amount to nearest cent, returning whole cents (int). Half-penny rounds up."""
    if isinstance(amount, bool) or not isinstance(amount, (int, float)):
        raise TypeError("amount must be a number")
    if amount < 0:
        raise ValueError("amount must be non-negative")
    # Exact decimal arithmetic avoids float error at the half-penny boundary
    # (e.g. 1.005 * 100 == 100.4999... in float, which must round to 101).
    cents = Decimal(str(amount)) * 100
    return int(cents.quantize(Decimal("1"), rounding="ROUND_HALF_UP"))
