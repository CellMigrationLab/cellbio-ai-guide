#!/bin/sh
# Rescore all Cellpose runs, recompute annotator agreement, assemble and render Figure 2 v3.
cd "$(dirname "$0")"
python3 score_perturb.py > /dev/null 2>&1

python3 - <<'PY'
s=open('fig2_body.py').read(); tail=s[s.index('svg = (f\'<?xml'):]
open('fig2_body_v3.py','w').write(''.join(open(f).read() for f in ['blk_helpers.py','blk_a.py','blk_c.py','blk_d.py','blk_e.py','blk_f.py'])+tail)
PY
cat fig2_head.py fig2_body_v3.py > make_fig2_v3.py
sed -i 's/open("fig2.svg"/open("fig2_v3.svg"/' make_fig2_v3.py
python3 make_fig2_v3.py
H=$(grep -o 'height="[0-9]*"' fig2_v3.svg | head -1 | grep -o '[0-9]*')
sh render.sh fig2_v3.svg preview_fig2_v3.png $H
