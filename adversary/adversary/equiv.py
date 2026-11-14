"""JEV equivalence triage for survivors.

For each surviving fault, build two clean A/B code blocks — the enclosing
function/statement as-written (Function A) and the same region with the mutant
replacement spliced at the *translated* site offsets (Function B) — then ask a
JEV decision model whether the two are behaviorally equivalent. Bucket each
survivor ``equivalent | killable | undecided`` by confidence. Emits a triage
JSON (FR-001).

Design notes
------------
- **A/B block builder** (FR-002): a site inside a function yields the enclosing
  def-with-body as Function A; a top-level site yields the enclosing statement
  block (or the whole module). Splice offsets are translated to the container's
  local span (``start - container_start``, ``end - container_start``).
- **Decision seam** (FR-003): triage calls a single injectable
  ``decide(state, questions) -> normalized answers``. The real implementation
  wraps ``triage-engine/src/jev/client.py`` ``JevClient`` at the adapter
  boundary only (lazy import); the API key is resolved by JevClient from env or
  key file and travels ONLY in the Authorization header, never in state or
  questions. Tests inject an offline stub — no live provider in CI.
- **Confidence bucketing** (FR-004): high-confidence ``equivalent`` ->
  ``equivalent``; high-confidence ``different`` -> ``killable``; low confidence
  (or a missing/invalid choice) -> ``undecided``. ``undecided`` never collapses
  to the other two buckets (SC-003). Thresholds are module constants, single
  source of truth, overridable by the caller/CLI.
"""
import ast
import os
import sys

DEFAULT_MODEL = "typesafe/jev-1.14"

# Confidence cutoff: below this, a survivor is too uncertain to trust and goes
# to ``undecided`` (never forced into equivalent/killable). Overridable via CLI.
CONFIDENCE_CUTOFF = 0.7

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

LABELS = ("equivalent", "killable", "undecided")


# ---------------------------------------------------------------------------
# A/B block builder (FR-002)
# ---------------------------------------------------------------------------

def _char_offset(lines, lineno, col):
    """Character offset of (lineno, col) in the original source (as sites._offset)."""
    return sum(len(line) for line in lines[:lineno - 1]) + col


def _node_span(lines, node):
    return (_char_offset(lines, node.lineno, node.col_offset),
            _char_offset(lines, node.end_lineno, node.end_col_offset))


def _enclosing_function(tree, lines, start, end):
    """Innermost FunctionDef/AsyncFunctionDef whose span fully contains [start, end)."""
    best = None
    best_span = None
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            ns, ne = _node_span(lines, node)
            if ns <= start and end <= ne:
                if best is None or (ne - ns) < best_span:
                    best, best_span = node, ne - ns
    return best


def _enclosing_statement(tree, lines, start, end):
    """Innermost ast.stmt whose span fully contains [start, end)."""
    best = None
    best_span = None
    for node in ast.walk(tree):
        if isinstance(node, ast.stmt):
            ns, ne = _node_span(lines, node)
            if ns <= start and end <= ne:
                if best is None or (ne - ns) < best_span:
                    best, best_span = node, ne - ns
    return best


def build_blocks(source, site):
    """Return {func_a, func_b, local_start, local_end, kind}.

    ``site`` is a survivor record with ``start``/``end`` (absolute char offsets
    into ``source``), ``orig``, and ``replacement``. ``func_b`` is ``func_a``
    with ``replacement`` spliced at the site's LOCAL offsets
    (``local_start = start - container_start``). ``kind`` is ``function``
    (site inside a def), ``statement`` (top-level enclosing block), or
    ``module`` (whole module fallback on parse failure / no container).
    """
    lines = source.splitlines(keepends=True)
    try:
        tree = ast.parse(source)
    except SyntaxError:
        func_a = source
        func_b = source[:site["start"]] + site["replacement"] + source[site["end"]:]
        return {"func_a": func_a, "func_b": func_b,
                "local_start": site["start"], "local_end": site["end"], "kind": "module"}

    fn = _enclosing_function(tree, lines, site["start"], site["end"])
    if fn is not None:
        fs, fe = _node_span(lines, fn)
        func_a = source[fs:fe]
        ls, le = site["start"] - fs, site["end"] - fs
        func_b = func_a[:ls] + site["replacement"] + func_a[le:]
        return {"func_a": func_a, "func_b": func_b,
                "local_start": ls, "local_end": le, "kind": "function"}

    stmt = _enclosing_statement(tree, lines, site["start"], site["end"])
    if stmt is not None:
        ss, se = _node_span(lines, stmt)
        func_a = source[ss:se]
        ls, le = site["start"] - ss, site["end"] - ss
        func_b = func_a[:ls] + site["replacement"] + func_a[le:]
        return {"func_a": func_a, "func_b": func_b,
                "local_start": ls, "local_end": le, "kind": "statement"}

    func_a = source
    func_b = source[:site["start"]] + site["replacement"] + source[site["end"]:]
    return {"func_a": func_a, "func_b": func_b,
            "local_start": site["start"], "local_end": site["end"], "kind": "module"}


def build_state(name, block_a, block_b):
    """Clean two-block prompt context (no diff): the shape the spike validated 12/12."""
    return "\n".join([
        f"### CASE: {name}",
        "Function A (original):",
        "```python",
        block_a,
        "```",
        "Function B (mutated):",
        "```python",
        block_b,
        "```",
    ])


# ---------------------------------------------------------------------------
# Decision seam (FR-003)
# ---------------------------------------------------------------------------

def make_payload(context, questions, model=DEFAULT_MODEL):
    """The exact request body the adapter hands JEV: {model, state, questions}.

    Parity with ``JevClient.build_decisions_body``; pure, no I/O. The API key
    is NEVER part of this body — it only ever appears in an Authorization
    header added by the transport.
    """
    return {"model": model, "state": context, "questions": questions}


def real_decide(context, questions, model=DEFAULT_MODEL, http_post=None):
    """Adapter for ``triage-engine/src/jev/client.py`` ``JevClient`` (thin).

    Imported lazily at the adapter boundary so importing ``adversary.equiv``
    never pulls in triage-engine or touches the network. Key hygiene is
    inherited from JevClient: the key is read from env/key file and sent only
    in the Authorization header, never in ``context``/``questions``/the body.
    """
    sys.path.insert(0, os.path.expanduser("~/projects/triage-engine/src"))
    from jev.client import JevClient  # boundary import
    client = JevClient(http_post=http_post, model=model)
    return client.decide(context, questions, model=model)


# Deterministic offline stand-in for JEV (used by ``adversary equiv --offline``
# and integration; tests inject their own scripted decider).
# Maps a distinguishing substring of the A/B context -> (choice, confidence).
# Each key must appear in exactly ONE of the constructed verification cases'
# A/B contexts, so first-match routing is unambiguous. Ground truth for the
# T004 integration set is literally these choices (SC-001 verifies the triage
# *pipeline* — block building, state, labeling, bucketing — given a decision
# source; JEV's own reasoning was the spike's separate 12/12 live result).
DEFAULT_OFFLINE_ANSWERS = {
    "return 0 < n":   {"choice": "equivalent", "confidence": 0.99},
    "return n < 0":   {"choice": "different", "confidence": 0.99},
    "return n >= 0":  {"choice": "different", "confidence": 0.50},
    "10 <= quantity": {"choice": "equivalent", "confidence": 0.99},
    "quantity > 10":  {"choice": "different", "confidence": 0.99},
}


def offline_decide(context, questions, answers=None):
    """Scripted deterministic stand-in. ``answers`` maps a substring of the
    A/B context -> {choice, confidence}. No match -> low-confidence ``{}``
    (triage buckets that ``undecided``)."""
    answers = DEFAULT_OFFLINE_ANSWERS if answers is None else answers
    for key, ans in answers.items():
        if key in context:
            return {"equivalence": {"choice": ans["choice"],
                                    "confidence": ans["confidence"]}}
    return {"equivalence": {"choice": None, "confidence": 0.0}}


# ---------------------------------------------------------------------------
# Confidence bucketing + triage driver (FR-004)
# ---------------------------------------------------------------------------

def _answer(norm):
    """The first normalized answer carrying a ``choice`` (spike's extract_choice shape)."""
    for qraw in (norm or {}).values():
        if isinstance(qraw, dict) and "choice" in qraw:
            return qraw
    return {}


def bucket_label(choice, confidence, confidence_cutoff):
    """Map a (choice, confidence) to exactly one of the three buckets.

    Low confidence -> undecided regardless of choice; a missing/invalid choice
    -> undecided. ``undecided`` NEVER collapses to equivalent/killable (SC-003).
    """
    if confidence < confidence_cutoff:
        return "undecided"
    if choice == "equivalent":
        return "equivalent"
    if choice == "different":
        return "killable"
    return "undecided"


def triage(survivors, source_for, decide=None, confidence_cutoff=CONFIDENCE_CUTOFF,
           questions=None, state_builder=build_state):
    """Triage every survivor record; return a list of triage records.

    ``source_for(path) -> str`` returns the module source for each survivor's
    ``path``. ``decide(state, questions)`` is the injectable seam; the real
    ``real_decide`` is the default. Output preserves input ordering and is
    deterministic (FR-006). Each survivor adds ``label`` in {equivalent,
    killable, undecided} and ``confidence`` in [0,1] (FR-001).
    """
    if decide is None:
        decide = real_decide
    questions = questions if questions is not None else EQUIV_QUESTION
    out = []
    for rec in survivors:
        source = source_for(rec["path"])
        blocks = build_blocks(source, rec)
        name = f"{rec['path']}#{rec['start']}"
        ctx = state_builder(name, blocks["func_a"], blocks["func_b"])
        norm = decide(ctx, questions)
        ans = _answer(norm)
        choice = ans.get("choice")
        confidence = ans.get("confidence", 0.0) or 0.0
        label = bucket_label(choice, confidence, confidence_cutoff)
        out.append({
            "path": rec["path"], "start": rec["start"], "end": rec["end"],
            "orig": rec["orig"], "replacement": rec["replacement"],
            "verdict": rec["verdict"],
            "label": label, "confidence": round(float(confidence), 4),
        })
    return out