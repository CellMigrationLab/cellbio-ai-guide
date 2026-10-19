"""Row A, second check: do the library functions, classes and keywords used in the code blocks of the replies exist in the
installed versions (Cellpose 4.2.1.1, scikit-image, SciPy, NumPy, pandas, tifffile, ...)? Static: nothing in the replies is run.

For every call whose object can be resolved in an installed module the script checks that the attribute exists, that
keyword arguments are accepted by the signature (unless the function takes **kwargs) and, for regionprops_table, that the
property names exist. Calls on modules that are not installed (for example StarDist) or on objects it cannot trace are
counted as unverified, not as correct. Writes fig3/v2/advice_api_check.csv. The flagged items must be read by a person:
a flag means "not found in the installed version", which is what an outdated or invented call looks like.
Usage: PYTHONPATH=. python fig3/v2/advice_api_check.py
"""
import ast
import csv
import importlib
import inspect
import json
import re

import numpy as np

from common.paths import REPO_ROOT

RUNS = REPO_ROOT / "fig3" / "v2" / "runs"
OUT = REPO_ROOT / "fig3" / "v2" / "advice_api_check.csv"
SKIP_ROOTS = {"os", "sys", "pathlib", "argparse", "json", "csv", "logging", "typing", "dataclasses", "__future__", "time",
              "warnings", "math", "collections", "itertools", "functools", "re", "datetime", "shutil", "subprocess"}


def try_import(name):
    try:
        return importlib.import_module(name)
    except Exception:
        return None


class Checker(ast.NodeVisitor):
    def __init__(self):
        self.objs = {}                    # local name -> python object (module, class or instance class)
        self.checked = 0
        self.unverified = []
        self.flags = []

    def visit_Import(self, node):
        for a in node.names:
            mod = try_import(a.name)
            top = a.asname or a.name.split(".")[0]
            self.objs[top] = mod if a.asname else try_import(a.name.split(".")[0])
            if mod is None and a.name.split(".")[0] not in SKIP_ROOTS:
                self.unverified.append(f"import {a.name}")

    def visit_ImportFrom(self, node):
        if node.level or not node.module:
            return
        mod = try_import(node.module)
        for a in node.names:
            name = a.asname or a.name
            if mod is None:
                self.objs[name] = None
                if node.module.split(".")[0] not in SKIP_ROOTS:
                    self.unverified.append(f"from {node.module} import {a.name}")
                continue
            if hasattr(mod, a.name):
                self.objs[name] = getattr(mod, a.name)
            else:
                sub = try_import(f"{node.module}.{a.name}")
                if sub is not None:
                    self.objs[name] = sub
                else:
                    self.objs[name] = None
                    self.flags.append(f"import not found: from {node.module} import {a.name}")

    def resolve(self, node):
        """Object for a Name / Attribute chain, or None; flags a missing attribute of an installed object."""
        if isinstance(node, ast.Name):
            return self.objs.get(node.id)
        if isinstance(node, ast.Attribute):
            base = self.resolve(node.value)
            if base is None:
                return None
            if hasattr(base, node.attr):
                return getattr(base, node.attr)
            if inspect.isclass(base) or inspect.ismodule(base):
                self.flags.append(f"not found in installed version: {ast.unparse(node)}")
            return None
        if isinstance(node, ast.Call):                   # instance of a resolved class: x = Class(...)
            f = self.resolve(node.func)
            return f if inspect.isclass(f) else None
        return None

    def visit_Assign(self, node):
        self.generic_visit(node)
        if isinstance(node.value, ast.Call) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            f = self.resolve(node.value.func)
            if inspect.isclass(f):
                self.objs[node.targets[0].id] = f      # the variable holds an instance of this class

    def visit_Call(self, node):
        self.generic_visit(node)
        n_flags = len(self.flags)
        f = self.resolve(node.func)
        if len(self.flags) > n_flags:
            return
        if f is None or not callable(f):
            root = node.func
            while isinstance(root, (ast.Attribute, ast.Call)):
                root = root.value if isinstance(root, ast.Attribute) else root.func
            if isinstance(root, ast.Name) and root.id in self.objs and self.objs[root.id] is None:
                self.unverified.append(ast.unparse(node.func))
            return
        self.checked += 1
        try:
            sig = inspect.signature(f)
        except (TypeError, ValueError):
            return
        params = sig.parameters
        if not any(p.kind == p.VAR_KEYWORD for p in params.values()):
            for kw in node.keywords:
                if kw.arg and kw.arg not in params:
                    self.flags.append(f"unknown keyword '{kw.arg}' for {ast.unparse(node.func)}")
        if ast.unparse(node.func).endswith("regionprops_table"):
            for kw in node.keywords:
                if kw.arg == "properties" and isinstance(kw.value, (ast.Tuple, ast.List)):
                    from skimage.measure import regionprops_table
                    lab = np.zeros((6, 6), int); lab[1:4, 1:4] = 1
                    for el in kw.value.elts:
                        if isinstance(el, ast.Constant) and isinstance(el.value, str):
                            try:
                                regionprops_table(lab, properties=(el.value,))
                            except Exception:
                                self.flags.append(f"regionprops property not found: {el.value}")


def main() -> None:
    rows = []
    for run in sorted(RUNS.glob("advice_*")):
        reply = " ".join(t.get("reply") or "" for t in json.loads((run / "turns.json").read_text()))
        blocks = re.findall(r"```(?:python|py)\n(.*?)```", reply, flags=re.S)
        flags, unverified, checked, syntax = [], [], 0, 0
        for code in blocks:
            try:
                tree = ast.parse(code)
            except SyntaxError:
                syntax += 1
                continue
            c = Checker()
            c.visit(tree)
            flags += c.flags; unverified += c.unverified; checked += c.checked
        meta = json.loads((run / "meta.json").read_text())
        rows.append({"scenario_id": run.name, "task": meta["task"], "condition": meta["condition"], "python_blocks": len(blocks),
                     "blocks_with_syntax_error": syntax, "calls_checked": checked, "unverified": len(set(unverified)),
                     "flags": " | ".join(sorted(set(flags))), "unverified_items": " | ".join(sorted(set(unverified))[:6])})
    with OUT.open("w", newline="") as handle:
        w = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    print(len(rows), "replies ->", OUT.relative_to(REPO_ROOT))


if __name__ == "__main__":
    main()
