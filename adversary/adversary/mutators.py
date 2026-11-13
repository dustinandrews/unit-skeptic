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
import re


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

    Operators are matched as whole tokens (longest-first), so a `>` inside a
    `>=` is never shredded into a malformed `<= =`.
    """

    _OPS = {
        ">=": "<", "<=": ">",
        "==": "!=", "!=": "==",
        ">": "<=", "<": ">=",
        "and": "or",
    }
    # Longest operators first so regex alternation prefers `>=` over `>`.
    _TOKEN = re.compile("|".join(re.escape(k) for k in _OPS))

    def mutate(self, site):
        text = site["text"]
        out = []
        seen = set()
        for match in self._TOKEN.finditer(text):
            token = match.group(0)
            if token in seen:
                continue
            seen.add(token)
            flip = self._OPS[token]
            # Emit a candidate flipping THIS token occurrence.
            cand = text[:match.start()] + flip + text[match.end():]
            if cand != text:
                out.append(cand)
        return out
