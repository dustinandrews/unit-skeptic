"""Andy: the mutator driver.

Interface: a driver has `mutate(site) -> list[str]` returning candidate
source snippets to substitute at the site. Andy is BLIND to tests by design —
the harness never passes test content here.

`deterministic` mutator validates plumbing at zero cost.
`llm` wraps a real model for the actual adversary once plumbing is proven.
"""
import os


class DeterministicAndy:
    """Swap comparison/bool operators in the site text (no LLM, no cost).

    Only meaningful for Compare/BoolOp sites; yields the 1-2 obvious flips so
    the harness loop (green gate -> apply -> pytest -> verdict -> record) can
    be exercised and verified before wiring a real model.
    """

    _FLIP = {
        "==": "!=", "!=": "==",
        "<": ">", ">": "<", "<=": ">=", ">=": "<=",
        "and": "or", "or": "and",
    }

    def mutate(self, site):
        text = site["text"]
        out = []
        for a, b in self._FLIP.items():
            if a in text and a != b:
                out.append(text.replace(a, b, 1))
        return out


class LlmAndy:
    """Real LLM adversary. Stateless one-shot: emit snippets for the site.

    Prompt asks for N fenced snippets replacing the placeholder with a buggy
    fragment that changes behavior vs the original. Tests never appear.
    NOTE: not yet wired to a backend; deterministic driver first.
    """

    def __init__(self, endpoint=None, key=None):
        self.endpoint = endpoint or os.getenv("ANDY_LLM_ENDPOINT")
        self.key = key or os.getenv("ANDY_LLM_KEY")

    def mutate(self, site):
        # placeholder: build prompt with code context + original fragment
        raise NotImplementedError(
            "LlmAndy not wired yet — plumbing first with DeterministicAndy."
        )
