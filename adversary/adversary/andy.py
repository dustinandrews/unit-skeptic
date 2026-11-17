"""LlmMutator: LLM-proposed realistic faults (the "Andy" adversary driver).

Andy is a second ``Mutator`` implementation behind the SAME adapter contract
(``mutate(site) -> list[str]``). It proposes faults an LLM believes a
developer would actually introduce, so the score measures realistic faults
rather than just operator flips.

Blind by design
---------------
Andy is a *blind generator*; the harness is the optimizer. Its entire input is
one site + its enclosing function (from subject source ONLY) built by
``build_prompt``. Tests, coverage, verdicts, and survivors never appear in the
prompt (structurally) and there is no feedback loop across runs (stateless
one-shot per site).

PLACEHOLDER-fill, bounded mutations
-----------------------------------
The prompt blanks the target region to ``<PLACEHOLDER>`` inside the enclosing
function (reusing Sprint-3 ``equiv.build_blocks`` extraction, minus the
original text). Andy returns 1..N replacement strings between ``<snippet>``
tags; each is spliced at the site by the harness exactly like a deterministic
candidate. Every mutant stays atomic, splice-revert safe, mechanically
verifiable. Candidates are deduped, non-empty, and must differ from the
site's original text (FR-004).

Noise is absorbed by existing gates: non-compiling candidates -> the runner's
parse-gate ``error`` verdict (excluded from the denominator); duplicates ->
deduped here; equivalents -> JEV triage (Sprint 3).

Transport seam (FR-003)
-----------------------
A single injectable ``complete(prompt) -> str`` seam. The real
implementation calls an OpenRouter chat-completions endpoint via stdlib
urllib (NFR-001, no SDK) with a configurable ``--model``; the offline runtime
uses a deterministic scripted stub (no network, no key) so CI stays offline
(NFR-003). The API key is read from env (never a literal, never in prompts),
and travels ONLY in the Authorization header.
"""
import json
import os
import re
import urllib.request

from adversary import equiv


def _load_env_file(dotenv_path):
    """STM-load a .env file into os.environ (stdlib; NFR-001 forbids python-dotenv).

    Reads KEY=VALUE lines (ignoring comments/blank), only setting vars not
    already present so a real exported env wins. Returns dict of loaded pairs.
    """
    loaded = {}
    try:
        with open(dotenv_path) as fh:
            for raw in fh:
                line = raw.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, val = line.partition("=")
                key = key.strip()
                if key and key not in os.environ:
                    os.environ[key] = val.strip().strip('"').strip("'")
                    loaded[key] = os.environ[key]
    except FileNotFoundError:
        pass
    return loaded


# Load the project .env at import (next to the adversary/ package dir) so live
# Andy runs pick up OPENROUTER_API_KEY without exporting it per-shell. Export
# wins over .env; module-level load keeps it available to real_complete and the
# key-hygiene tests. NFR-001: stdlib only.
_ENV_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
_load_env_file(_ENV_PATH)

# Default model id for live runs (FR-005); "openrouter/auto" routes to a
# sensible default on the OpenRouter proxy.
DEFAULT_MODEL = "openrouter/auto"

PLACEHOLDER = "<PLACEHOLDER>"

OPENROUTER_ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"

# System/user prompt. The goal is a *realistic fault a developer might
# introduce*, NEVER "foil the tests" (goal alignment: survival is not success;
# equivalents are JEV-triaged downstream). The enclosing function below has
# the target region blanked to <PLACEHOLDER>.
PROMPT_TEMPLATE = (
    "You are a senior developer. Below is a function with one region replaced "
    "by <PLACEHOLDER>. Propose exactly {n} distinct replacement snippet(s) for "
    "that region, each a realistic, behavior-changing bug a developer might "
    "accidentally introduce there (wrong operator, wrong constant, off-by-one, "
    "negated condition, swapped operands, added/dropped term, wrong branch, "
    "wrong default, ...). Only plain code inside <snippet>...</snippet> tags, "
    "one snippet per tag pair, no explanations.\n\n```python\n{enclosing}\n```"
)

# one <snippet>/</snippet> tag pair, non-greedy across newlines
_SNIPPET_TAG = re.compile(r"<snippet>(.*?)</snippet>", re.DOTALL)
# fallback path: a triple-backtick python fenced block (real models sometimes
# ignore tag instructions), a fenced block carries one replacement.
_FENCE = re.compile(r"```(?:python)?\s*(.*?)```", re.DOTALL)


# ---------------------------------------------------------------------------
# Prompt builder (FR-002): subject source ONLY
# ---------------------------------------------------------------------------

def build_prompt(source, site, trials=1):
    """Build Andy's prompt from subject source ONLY.

    ``site`` is a site record from ``sites.find_sites`` (module, start, end,
    text, kind). The target region is blanked to ``<PLACEHOLDER>`` inside the
    enclosing function by reusing the Sprint-3 A/B block builder with a
    placeholder replacement, so the model only ever sees the surrounding code
    plus a blanked site — never tests, coverage, verdicts, or survivors.
    """
    blocks = equiv.build_blocks(source, dict(site, replacement=PLACEHOLDER))
    enclosing = blocks["func_b"]  # enclosing function, site blanked
    return PROMPT_TEMPLATE.format(n=trials, enclosing=enclosing)


def parse_reply(reply, orig):
    """Turn a model reply into deduped candidate replacement strings (FR-004).

    Accepts ``<snippet>...</snippet>`` tag pairs (and fenced fallback). Every
    candidate is non-empty and differs from the site's original text
    ``orig``; identical strings collapse to one.
    """
    if not reply:
        return []
    cands = []
    for raw in _SNIPPET_TAG.findall(reply):
        s = raw.strip()
        if s and s != orig and s not in cands:
            cands.append(s)
    if not cands:  # fenced fallback when no tag pairs were honored
        for block in _FENCE.findall(reply):
            s = block.strip()
            if s and s != orig and s not in cands:
                cands.append(s)
    return cands


# ---------------------------------------------------------------------------
# Transport seam (FR-003)
# ---------------------------------------------------------------------------

def _http_post(url, body, headers):
    """Stdlib HTTP POST for the OpenRouter chat-completions endpoint."""
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read().decode("utf-8")


def real_complete(prompt, model=DEFAULT_MODEL, api_key=None,
                  endpoint=OPENROUTER_ENDPOINT, http_post=None):
    """Real OpenRouter completion. Injectable ``http_post`` for testability.

    The API key is read from env (falling back to an explicit ``api_key``)
    and travels ONLY in the Authorization header — never in the prompt/body
    (FR-003 / key hygiene like the JEV adapter).
    """
    key = api_key or os.getenv("OPENROUTER_API_KEY")
    if not key:
        raise RuntimeError("OPENROUTER_API_KEY not set (required for a live Andy run)")
    body = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
    }).encode("utf-8")
    post = http_post or _http_post
    resp = post(endpoint, body, {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    })
    data = json.loads(resp)
    return data["choices"][0]["message"]["content"]


# Deterministic offline stand-in (used by ``--offline`` and integration). The
# region is blanked in the prompt, so routing keys are distinguishing substrings
# of the ENCLOSING function (the header/surrounding code, which is present).
# Mirrors Sprint-3 ``equiv``'s offline routing pattern.
DEFAULT_OFFLINE_REPLIES = {
    "def tier_discount(quantity):": "<snippet>quantity > 10</snippet>",
    "def apply_tier_discount(unit_price, quantity):":
        "<snippet>unit_price * quantity * (1 + rate)</snippet>",
    "def is_taxable(region, item_kind):":
        "<snippet>region in exempt_regions</snippet>",
    "def tax_rate(region):":
        "<snippet>rates.get(region, 0.01)</snippet>",
    "def round_cents(amount):":
        "<snippet>ROUND_DOWN</snippet>",
}
DEFAULT_OFFLINE_REPLY = "<snippet>return 0</snippet>"


def offline_complete(prompt, replies=None):
    """Scripted deterministic stand-in for Andy (no network, no key).

    Routes the enclosing-function marker that appears in the prompt to a canned
    replacement snippet; no match -> DEFAULT_OFFLINE_REPLY. Same input ->
    same output (FR-008), so the pipeline is exercisable end-to-end in CI.
    """
    replies = DEFAULT_OFFLINE_REPLIES if replies is None else replies
    for marker, reply in replies.items():
        if marker in prompt:
            return reply
    return DEFAULT_OFFLINE_REPLY


# ---------------------------------------------------------------------------
# The mutator
# ---------------------------------------------------------------------------

def make_complete(model=DEFAULT_MODEL, offline=False):
    """Return the ``complete(prompt) -> str`` seam for a run's transport."""
    return lambda prompt: offline_complete(prompt) if offline else real_complete(prompt, model=model)


class LlmMutator:
    """Blind LLM fault generator behind the ``Mutator`` protocol.

    ``mutate(site) -> list[str]`` matches the deterministic adapter exactly, so
    ``scorer.run_loop`` drives it with zero structural changes (FR-001 /
    SC-001). ``source`` (the full module source) is injected at construction so
    Andy can build the enclosing-function prompt; it has no other context.
    """

    def __init__(self, source, complete=None, model=DEFAULT_MODEL, trials=1):
        self.source = source
        self.model = model
        self.trials = max(1, int(trials))
        self._complete = complete if complete is not None else make_complete(model)

    def mutate(self, site):
        prompt = build_prompt(self.source, site, self.trials)
        reply = self._complete(prompt)
        return parse_reply(reply, site["text"])
