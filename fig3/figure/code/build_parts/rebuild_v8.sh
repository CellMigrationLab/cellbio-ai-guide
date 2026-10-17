cd <fig3-work>/bf3 && python3 build_scores.py && python3 make_legend.py > /dev/null > /dev/null
cd .. && cat fig3_head.py fig3_helpers.py fig3_v9.py > make_fig3_v9.py && python3 make_fig3_v9.py && H=$(python3 -c "import re;print(re.search(r'height=\"(\d+)\"',open('fig3_v9.svg').read()).group(1))") && sh render.sh fig3_v9.svg prev_v9.png $H && cp prev_v9.png ../figure3/draft_v9.png
