# Recovered verbatim from the session transcript (2026-10-16T12:32:48.739Z).
# Last shell command that wrote data/ts_cp_. Paths are those of the original working folder.
cd <work2>/fig2; sed -i 's/^xe, we = xb, wb$/xe = 28 + 740 + 6\nwe = 1812 - xe/' fig2_body.py; ls data/ts_cp_*; cat fig2_head.py fig2_body.py > make_fig2.py; python3 make_fig2.py && H=$(grep -o 'height="[0-9.]*"' fig2.svg | head -1 | grep -o '[0-9.]*' | head -1); echo $H; sh render.sh fig2.svg preview_fig2.png ${H%.*}
