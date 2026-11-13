"""Find candidate mutation sites in a Python source file via ast.

A Site is a tuple/dict: (start_offset, end_offset, original_text, kind, repr).
The placeholder machinery blanks a site and asks the mutator to fill it.
"""
import ast


def _text_at(trees, node):
    """Return the exact source text of an AST node (from precomputed lines)."""
    return "".join(trees[node.lineno - 1:node.end_lineno])[
        node.col_offset:
        (node.end_col_offset if node.end_lineno == node.lineno else None)
    ]


def _offset(trees, lineno, col):
    """Byte/char offset of a (lineno, col) in the original source."""
    return sum(len(line) for line in trees[:lineno - 1]) + col


def find_sites(source):
    """Return list of {start, end, text, kind} sites in *source*.

    Kind is the AST node type; text is the exact original source span.
    """
    tree = ast.parse(source)
    # Split into physical lines (keeps original char spans accurate).
    lines = source.splitlines(keepends=True)
    sites = []
    for node in ast.walk(tree):
        if not hasattr(node, "lineno"):
            continue
        if isinstance(node, (ast.Compare, ast.BoolOp)):
            start = _offset(lines, node.lineno, node.col_offset)
            end = _offset(lines, node.end_lineno, node.end_col_offset)
            text = _text_at(lines, node)
            sites.append({
                "start": start,
                "end": end,
                "text": text,
                "kind": type(node).__name__,
            })
    return sites
