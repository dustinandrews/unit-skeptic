"""Mutator adapter contract.

Site primitive (canonical): a `site` is a dict {module, start, end, text, kind}
where start/end are CHARACTER offsets into the module source and `text` is the
exact source spanning [start, end). A site is an atomic mutatable region (one
operator / constant / name / expression occurrence) found via AST walking (see
adversary.sites).

Replacement unit (canonical): each candidate returned by `mutate(site)` is the
full replacement source text to splice at [start, end), i.e.
    source[:start] + replacement + source[end:]
is the mutated module. A mutator replaces ONE site at a time; it never returns
whole-file diffs.

This contract is stable so an LLM-based mutator can implement it unchanged.
"""
from typing import Protocol, runtime_checkable


@runtime_checkable
class Mutator(Protocol):
    """Given a site, return candidate replacement source strings."""

    def mutate(self, site):
        """Return list[str] of replacement text candidates for `site`."""
        raise NotImplementedError


class DeterministicMutator:
    """Rule-based operator flips (zero LLM cost). Fully deterministic.

    For a Compare site's text, flip a comparison operator to a behavior-changing
    counterpart. For a BoolOp site, flip `and` <-> `or`. No randomness.
    """

    _OPS = {
        "==": "!=", "!=": "==",
        "<": ">=", "<=": ">",
        ">": "<=", ">=": "<",
        "and": "or",
    }

    def mutate(self, site):
        text = site["text"]
        out = []
        for a, b in self._OPS.items():
            if a in text and a != b:
                out.append(text.replace(a, b, 1))
        return out
