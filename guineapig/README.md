# guineapig

A pure-Python pricing package built as a **known, controllable mutation-testing
guinea pig**. It is the subject the Adversary score engine will later mutate and
grade. Its behavior is fully documented here so test-suite scores and surviving
faults can be verified against ground truth.

## Domain

A small order-pricing calculator: quantity-tier discounts, tax applicability and
rates by region, and cent rounding. No I/O, no randomness, no network — all
functions are pure and deterministic.

## How to run the suite

```bash
cd guineapig
.venv/bin/python -m pytest        # or: python -m pytest (from repo root)
```

Requires Python >= 3.12 and pytest. Runs in < 2s, green.

## Public functions (contracts)

All functions are pure and total. Invalid input raises `ValueError` (or
`TypeError` for a non-numeric where the type is meaningless).

### `tier_discount(quantity: int) -> float`
Tiered discount rate by quantity:
- `0–4` → `0.0`
- `5–9` → `0.05`
- `10+` → `0.10`

Raises `ValueError` for negative or non-int quantity.

### `apply_tier_discount(unit_price: float, quantity: int) -> float`
Total price after tier discount: `unit_price * quantity * (1 - tier_discount(quantity))`.
Raises `ValueError` for negative price or invalid quantity.

### `is_taxable(region: str, item_kind: str) -> bool`
True if an item is taxable. `item_kind == "gift"` is never taxable; regions
`OR`, `AK`, `EU` are exempt. Raises `ValueError` for empty/invalid args.

### `tax_rate(region: str) -> float`
Tax rate for a known region (`CA` 0.0825, `NY` 0.04, `WA` 0.065, `TX` 0.0625);
unknown non-empty region falls back to `0.0`. Raises `ValueError` for empty/invalid.

### `round_cents(amount: float) -> int`
Rounds a dollar amount to the nearest cent as whole cents. Half-penny rounds up
(e.g. `1.005` → `101`). Uses exact decimal arithmetic (a naive `int(amount*100)`
truncates the half-penny due to float error). Raises `TypeError` for non-numeric,
`ValueError` for negative.

## Protected boundary cases (test suite coverage)

The boundary tests in `tests/test_pricing.py` protect:
- **Tier thresholds:** quantity 0/4/5/9/10 cutoffs, upper/lower bands, zero qty.
- **Discount math:** zero qty → 0, no-discount, lower/upper band application, zero price.
- **Taxability:** gift nontaxable, exempt regions, taxable region fallback.
- **Tax rates:** known regions, unknown default fallback.
- **Rounding:** round-down, round-up, **exact half-penny edge** (`1.005`→`101`),
  whole dollars, zero.
- **Invalid input:** negative quantity/price/amount, empty region/kind, non-int
  quantity, non-numeric round_cents.

## Deliberate weak-test cohort (dead-test ground truth)

`tests/test_weak.py` contains **4 intentionally useless tests**. They pass no
matter what the pricing functions do — they exercise no real behavior. The later
dead-test detector (Phase 2) MUST flag all four:

| Test | Why it is dead |
|------|----------------|
| `test_weak_tautology_always_true` | asserts `True` |
| `test_weak_constant_against_itself` | asserts `x == x` |
| `test_weak_assert_none_is_none` | asserts `None is None` |
| `test_weak_no_behavior_called` | imports nothing from guineapig |

These are the known detectors Phase 2 must find; a detector that flags any of
these as *alive* is wrong, and one that misses them is incomplete.
