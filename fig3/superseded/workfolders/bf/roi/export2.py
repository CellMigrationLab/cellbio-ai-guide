"""ROI contours for the bf2 runs: export2.py name=path ..."""
import sys, json, tifffile
sys.path.insert(0, 'roi')
import importlib.util
spec = importlib.util.spec_from_file_location('ex', 'roi/export.py')
src = open('roi/export.py').read().split("if 'png' in sys.argv")[0]
ns = {}; exec(src, ns)
for a in sys.argv[1:]:
    name, path = a.split('=')
    json.dump(ns['contours'](tifffile.imread(path)), open(f'roi/{name}.json', 'w')); print(name, 'ok')
