import sys, json, tifffile
sys.path.insert(0, '../bf')
from score_cancer import score as sc
from score_endo import score as se
L = tifffile.imread(sys.argv[2])
print(json.dumps(sc(L) if sys.argv[1] == 'cancer' else se(L)))
