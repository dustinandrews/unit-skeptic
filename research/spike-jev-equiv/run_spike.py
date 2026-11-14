"""Tech spike: how good is JEV at mutant-equivalence triage?

Drives the REAL JevClient (reused from triage-engine/src/jev/client.py) against
labeled equivalence ground truth drawn from the guineapig pricing functions.
Presentation is two CLEAN labeled code blocks (Function A = original, Function B
= mutant) -- NO diff format -- and a single `choice` question: equivalent or
different.

Reads the OpenRouter key from ~/orchestrator-openrouter-api-key.txt (JEV key
hygiene: indirect file read, never a literal). Outputs a per-case table and
precision/recall/accuracy summary for the `equivalent` label.

Usage:  python run_spike.py          (live JEV call, needs key + network)
        python run_spike.py --dry    (print the exact payloads, no network)
"""
import json
import os
import sys
import urllib.request

sys.path.insert(0, os.path.expanduser("~/projects/triage-engine/src"))
from jev.client import JevClient, DEFAULT_MODEL  # noqa: E402


def live_http_post(url, body, headers=None):
    """Minimal stdlib urllib transport JevClient expects: returns {"json": ...}."""
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers or {}, method="POST")
    with urllib.request.urlopen(req, timeout=60) as resp:
        return {"json": json.loads(resp.read().decode("utf-8"))}


# ---------------------------------------------------------------------------
# Ground truth. Each case: (name, function_A_source, function_B_source, expected)
#   expected in {"equivalent", "different"}
# Functions are shown in FULL so JEV has real context, not a bare expression.
# ---------------------------------------------------------------------------

def _is_positive(n):
    return n > 0


IS_POS = """def is_positive(n):
    return n > 0"""

EQ_IS_POS_COMMUTE = """def is_positive(n):
    return 0 < n"""

DIFF_IS_POS_FLIP = """def is_positive(n):
    return n < 0"""

TIER = """def tier_discount(quantity):
    if quantity >= 10:
        return 0.10
    if quantity >= 5:
        return 0.05
    return 0.0"""

EQ_TIER_BOUND = """def tier_discount(quantity):
    if quantity >= 10:
        return 0.10
    if quantity >= 5:
        return 0.05
    return 0"""

DIFF_TIER_BOUND = """def tier_discount(quantity):
    if quantity > 10:
        return 0.10
    if quantity > 5:
        return 0.05
    return 0.0"""

TAXABLE = """def is_taxable(region, item_kind):
    if item_kind == "gift":
        return False
    return region not in {"OR", "AK", "EU"}"""

EQ_TAXABLE_COMMUTE = """def is_taxable(region, item_kind):
    if "gift" == item_kind:
        return False
    return region not in {"AK", "EU", "OR"}"""

DIFF_TAXABLE_NO_GIFT = """def is_taxable(region, item_kind):
    if item_kind == "gift":
        return True
    return region not in {"OR", "AK", "EU"}"""

DIFF_TAXABLE_NEGATED = """def is_taxable(region, item_kind):
    if item_kind == "gift":
        return False
    return region in {"OR", "AK", "EU"}"""

TAX_RATE = """def tax_rate(region):
    rates = {"CA": 0.0825, "NY": 0.04, "WA": 0.065, "TX": 0.0625}
    return rates.get(region, 0.0)"""

EQ_TAX_RATE_DEFAULT = """def tax_rate(region):
    rates = {"CA": 0.0825, "NY": 0.04, "WA": 0.065, "TX": 0.0625}
    return rates.get(region, 0)"""

DIFF_TAX_RATE_DEFAULT = """def tax_rate(region):
    rates = {"CA": 0.0825, "NY": 0.04, "WA": 0.065, "TX": 0.0625}
    return rates.get(region, 0.1)"""


# Truncation to whole cents (drops the fraction).
ROUND_TRUNC = """def round_cents(amount):
    cents = int(amount * 100)
    return cents"""

# Transcribed identically -> equivalent.
EQ_ROUND_TRANSCRIBE = """def round_cents(amount):
    cents = int(amount * 100)
    return cents"""

# The REAL guineapig round_cents: Decimal arithmetic, half-penny rounds UP.
# Genuinely different from truncation: 1.005 -> 101 here vs 100 there.
DIFF_ROUND_HALF = """from decimal import Decimal
def round_cents(amount):
    cents = Decimal(str(amount)) * 100
    return int(cents.quantize(Decimal("1"), rounding="ROUND_HALF_UP"))"""

# no-op `and True` trivially equivalent -- should be called equivalent.
EQ_AND_TRUE = """def is_positive(n):
    return n > 0 and True"""

CASES = [
    ("is_positive.commute", IS_POS, EQ_IS_POS_COMMUTE, "equivalent"),
    ("tier.bound", TIER, EQ_TIER_BOUND, "equivalent"),
    ("taxable.set_order+commute", TAXABLE, EQ_TAXABLE_COMMUTE, "equivalent"),
    ("tax_rate.default_0.0_vs_0", TAX_RATE, EQ_TAX_RATE_DEFAULT, "equivalent"),
    ("is_positive.flip", IS_POS, DIFF_IS_POS_FLIP, "different"),
    ("tier.boundary_shift", TIER, DIFF_TIER_BOUND, "different"),
    ("taxable.gift_exempt_removed", TAXABLE, DIFF_TAXABLE_NO_GIFT, "different"),
    ("taxable.negated_exempt", TAXABLE, DIFF_TAXABLE_NEGATED, "different"),
    ("tax_rate.default_0.1", TAX_RATE, DIFF_TAX_RATE_DEFAULT, "different"),
    # --- subtle tier ---
    ("round_cents.int_vs_round", ROUND_TRUNC, EQ_ROUND_TRANSCRIBE, "equivalent"),
    ("round_cents.int_vs_half_round", ROUND_TRUNC, DIFF_ROUND_HALF, "different"),
    ("is_positive.and_true", IS_POS, EQ_AND_TRUE, "equivalent"),
]


EQUIV_QUESTION = {
    "equivalence": {
        "type": "choice",
        "criteria": {
            "equivalent": "Function A and Function B compute exactly the same result for every possible input.",
            "different": "Function A and Function B differ in behavior for at least one input (a different result, different return type, or different error raised).",
        },
        "instructions": "Are these two functions behaviorally equivalent?",
    },
}


def build_state(name, src_a, src_b):
    return "\n".join([
        f"### CASE: {name}",
        "Function A (original):",
        "```python",
        src_a,
        "```",
        "Function B (mutated):",
        "```python",
        src_b,
        "```",
    ])


def extract_choice(norm):
    """Pull the picked `choice` from a normalized JEV answer set."""
    for qname, qraw in (norm or {}).items():
        if isinstance(qraw, dict) and "choice" in qraw:
            return qraw.get("choice")
    return None


def main():
    dry = "--dry" in sys.argv
    client = JevClient(http_post=None if dry else live_http_post)
    results = []
    for name, a, b, expected in CASES:
        state = build_state(name, a, b)
        payload = {"model": DEFAULT_MODEL, "state": state, "questions": EQUIV_QUESTION}
        if dry:
            results.append((name, expected, "[dry] payload only"))
            continue
        norm = client.decide(state, EQUIV_QUESTION)
        got = extract_choice(norm)
        results.append((name, expected, got))

    # table
    print(f"{'case':38} {'expected':11} {'jev':11} {'match'}")
    print("-" * 78)
    tp = fp = tn = fn = 0
    for name, expected, got in results:
        if got is None:
            got = "<none>"
        match = "OK" if got == expected else ("MISS" if got in ("equivalent", "different", "<none>") else "?")
        if match == "MISS":
            match = "!!"
        print(f"{name:38} {expected:11} {got:11} {match}")
        # confusion on the "equivalent" label
        if expected == "equivalent":
            if got == "equivalent":
                tp += 1
            else:
                fn += 1
        else:
            if got == "different":
                tn += 1
            elif got == "equivalent":
                fp += 1
    total = len(results)
    acc = (tp + tn) / total if total else 0
    prec = tp / (tp + fp) if (tp + fp) else float("nan")
    rec = tp / (tp + fn) if (tp + fn) else float("nan")
    print("-" * 78)
    print(f"accuracy={acc:.2f}  precision(equiv)={prec:.2f}  recall(equiv)={rec:.2f}  "
          f"tp={tp} fp={fp} tn={tn} fn={fn} / {total}")
    if dry:
        print("(dry run: rerun without --dry for live JEV calls)")


if __name__ == "__main__":
    main()
