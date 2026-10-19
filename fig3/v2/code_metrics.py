"""Readability and debuggability measures of the scripts returned in row B (and the pipelines of row C).

Secondary measures (PROTOCOL_V2 section 7 defines F1 as primary); standard library only, from the stored files, so they
can be recomputed at any time. Writes fig3/v2/code_metrics.csv, one row per script.
Usage: PYTHONPATH=. python fig3/v2/code_metrics.py

Measures (all static; none says whether the code is correct):
  loc               non-blank, non-comment lines
  comment_ratio     comment lines / loc
  n_functions, mean_func_lines, max_func_lines   size of the functions (smaller = easier to read and test)
  max_complexity    largest cyclomatic complexity of any function (1 + branches: if, for, while, except, and/or, ifexp,
                    comprehension conditions)
  typed_share       functions with a return annotation / functions
  docstring_share   functions with a docstring / functions
  n_constants       module-level UPPER_CASE names (named parameters at the top)
  magic_numbers     numeric literals inside functions other than 0, 1, 2, -1 (hidden parameters)
  n_raise           raise statements (input validation, informative errors)
  silent_except     except blocks that only pass/continue or catch everything (silent fallbacks)
  has_main_guard    `if __name__ == "__main__"`
"""
import ast
import csv
import json
import tokenize
import io

from common.paths import REPO_ROOT

RUNS = REPO_ROOT / "fig3" / "v2" / "runs"
OUT = REPO_ROOT / "fig3" / "v2" / "code_metrics.csv"
OK_NUMBERS = {0, 1, 2, -1}
BRANCH = (ast.If, ast.For, ast.While, ast.ExceptHandler, ast.IfExp, ast.With, ast.Assert)


def comment_lines(source: str) -> int:
    return sum(1 for t in tokenize.generate_tokens(io.StringIO(source).readline) if t.type == tokenize.COMMENT)


def complexity(func: ast.AST) -> int:
    n = 1
    for node in ast.walk(func):
        if isinstance(node, BRANCH) and not isinstance(node, (ast.With, ast.Assert)):
            n += 1
        elif isinstance(node, ast.BoolOp):
            n += len(node.values) - 1
        elif isinstance(node, ast.comprehension):
            n += 1 + len(node.ifs)
    return n


def silent(handler: ast.ExceptHandler) -> bool:
    only_pass = all(isinstance(s, (ast.Pass, ast.Continue)) for s in handler.body)
    catch_all = handler.type is None or (isinstance(handler.type, ast.Name) and handler.type.id in ("Exception", "BaseException"))
    return only_pass or catch_all


def measure(path) -> dict:
    source = path.read_text()
    tree = ast.parse(source)
    lines = [l for l in source.splitlines() if l.strip() and not l.strip().startswith("#")]
    funcs = [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    sizes = [n.end_lineno - n.lineno + 1 for n in funcs]
    magic = 0
    for f in funcs:
        for n in ast.walk(f):
            if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)) and not isinstance(n.value, bool):
                magic += n.value not in OK_NUMBERS
    consts = [t.id for n in tree.body if isinstance(n, (ast.Assign, ast.AnnAssign))
              for t in (n.targets if isinstance(n, ast.Assign) else [n.target])
              if isinstance(t, ast.Name) and t.id.isupper()]
    handlers = [n for n in ast.walk(tree) if isinstance(n, ast.ExceptHandler)]
    guard = any(isinstance(n, ast.If) and "__name__" in ast.dump(n.test) for n in tree.body)
    nf = len(funcs)
    return {"loc": len(lines), "comment_ratio": round(comment_lines(source) / max(len(lines), 1), 3),
            "n_functions": nf, "mean_func_lines": round(sum(sizes) / nf, 1) if nf else 0, "max_func_lines": max(sizes, default=0),
            "max_complexity": max((complexity(f) for f in funcs), default=0),
            "typed_share": round(sum(f.returns is not None for f in funcs) / nf, 2) if nf else 0,
            "docstring_share": round(sum(ast.get_docstring(f) is not None for f in funcs) / nf, 2) if nf else 0,
            "n_constants": len(consts), "magic_numbers": magic,
            "n_raise": sum(isinstance(n, ast.Raise) for n in ast.walk(tree)),
            "silent_except": sum(silent(h) for h in handlers), "has_main_guard": int(guard)}


def main() -> None:
    rows = []
    for run in sorted(RUNS.glob("*")):
        script = run / "code_as_returned.py"
        if not (run / "meta.json").exists():
            continue
        if not script.exists():
            script = run / "agent_folder" / "pipeline.py"
        if not script.exists():
            continue
        meta = json.loads((run / "meta.json").read_text())
        rows.append({"scenario_id": run.name, "row": meta["row"], "condition": meta["condition"], "task": meta["task"],
                     "replicate": meta["replicate"], **measure(script)})
    with OUT.open("w", newline="") as handle:
        w = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    print(len(rows), "scripts ->", OUT.relative_to(REPO_ROOT))


if __name__ == "__main__":
    main()
