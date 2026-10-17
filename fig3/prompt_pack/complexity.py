"""Simple code metrics for a generated script: python complexity.py code.py -> JSON."""
import ast, json, sys
src = open(sys.argv[1]).read(); tree = ast.parse(src)
lines = [l for l in src.splitlines() if l.strip() and not l.strip().startswith('#')]
funcs = [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
branches = sum(isinstance(n, (ast.If, ast.For, ast.While, ast.Try, ast.With, ast.IfExp, ast.BoolOp)) for n in ast.walk(tree))
imports = sorted({(a.name if isinstance(n, ast.Import) else (n.module or '')).split('.')[0]
                  for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom)) for a in n.names})
consts = [t.id for n in tree.body if isinstance(n, ast.Assign) for t in n.targets if isinstance(t, ast.Name) and t.id.isupper()]
consts += [n.target.id for c in tree.body if isinstance(c, ast.ClassDef) for n in c.body
           if isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name)]  # dataclass-style parameters
raises = sum(isinstance(n, ast.Raise) for n in ast.walk(tree))
print(json.dumps(dict(code_lines=len(lines), functions=len(funcs), branches=branches, imports=imports,
                      named_parameters=len(consts), raise_statements=raises), indent=1))
