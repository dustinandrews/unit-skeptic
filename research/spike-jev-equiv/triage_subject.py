"""Survivor-triage verification subject (Sprint 3, T004 / SC-001, SC-005).

Pure functions mirroring the JEV spike's A/B cases so the constructed survivor
set's gold truth = the spike's labeled set. Serves ONLY as a self-contained
target for `adversary equiv --offline`; it is not a real application subject.
"""


def is_positive(n):
    return n > 0


def tier_discount(quantity):
    if quantity >= 10:
        return 0.10
    if quantity >= 5:
        return 0.05
    return 0.0


def tax_rate(region):
    rates = {"CA": 0.0825, "NY": 0.04}
    return rates.get(region, 0.0)