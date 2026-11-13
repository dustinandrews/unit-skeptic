"""AST site enumeration.

A Site is an atomic mutatable region in a module's source:
    {module: str, start: int, end: int, text: str, kind: str}
where start/end are CHARACTER offsets into the module source and `text` is the
exact source spanning [start, end).

Sites are found by walking the AST for the node kinds a mutator can safely flip:
Compare (a == b, n > 0), BoolOp (a and b), Call (call args), and numeric/constant
expressions.
"""
import ast


def _offset(lines, lineno, col):
    """Character offset of (lineno, col) in the original source."""
    return sum(len(line) for line in lines[:lineno - 1]) + col


def find_sites(source, module="<string>"):
    """Return list of Site dicts: {module, start, end, text, kind}."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []
    lines = source.splitlines(keepends=True)
    sites = []
    # Link each node to its parent so callers can inspect the enclosing context.
    for n in ast.walk(tree):
        for child in ast.iter_child_nodes(n):
            child.parent = n

    def add(node, kind):
        start = _offset(lines, node.lineno, node.col_offset)
        end = _offset(lines, node.end_lineno, node.end_col_offset)
        text = source[start:end]
        if text.strip():
            sites.append({
                "module": module,
                "start": start,
                "end": end,
                "text": text,
                "kind": kind,
            })

    op_symbols = [
        ("==", ast.Eq), ("!=", ast.NotEq), ("<", ast.Lt), ("<=", ast.LtE),
        (">", ast.Gt), (">=", ast.GtE), ("in", ast.In), ("not in", ast.NotIn),
        ("is", ast.Is), ("is not", ast.IsNot),
    ]

    def add_op(parent, op_node):
        """Locate an operator's source span inside its parent Compare node.

        ast operator nodes don't carry line/col info in older Pythons, so we
        locate the symbol text within the parent Compare's exact source span.
        """
        ps = _offset(lines, parent.lineno, parent.col_offset)
        pe = _offset(lines, parent.end_lineno, parent.end_col_offset)
        frag = source[ps:pe]
        for sym, cls in op_symbols:
            if isinstance(op_node, cls) and sym in frag:
                idx = frag.find(sym)
                start = ps + idx
                end = start + len(sym)
                t = source[start:end]
                if t == sym or (sym == "in" and t.strip() == "in"):
                    sites.append({
                        "module": module, "start": start, "end": end,
                        "text": source[start:end], "kind": "Op",
                    })
                return
        # Fallback: whole Compare as the atomic site.
        add(parent, "Compare")

    for node in ast.walk(tree):
        if isinstance(node, ast.Compare):
            # The whole comparison expression (e.g. "a == b").
            add(node, "Compare")
            # Each comparator operation is its own atomic site (e.g. "==").
            for op in node.ops:
                add_op(node, op)
        elif isinstance(node, ast.BoolOp):
            add(node, "BoolOp")
        elif isinstance(node, ast.Call):
            # Each argument is atomic.
            for arg in node.args:
                add(arg, "CallArg")
            for kw in node.keywords:
                add(kw.value, "CallKeyword")
        elif isinstance(node, ast.UnaryOp):
            add(node, "UnaryOp")
        elif isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)) and type(node.value) is not bool:
                # Only a constant nested inside a Compare/BoolOp/Call is an atomic
                # mutation target; a bare top-level constant (e.g. `x = 1+2`) is not.
                p = getattr(node, "parent", None)
                if isinstance(p, (ast.Compare, ast.BoolOp, ast.Call)):
                    add(node, "Const")
    return sites
