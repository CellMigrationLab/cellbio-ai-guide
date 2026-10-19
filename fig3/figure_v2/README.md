# Figure 3 (protocol v2): figure builder

`make fig3v2` (or, from `source_data/`, `PYTHONPATH=../../.. python ../code/make_fig3_v2.py`, then `../code/export_png.py`) draws
the figure from the stored runs and writes `output/fig3_v2.svg` (editable; the same style as Figures 1 and 2) and a 2x PNG.

| Item | What it is |
|---|---|
| `code/make_fig3_v2.py` | Reads `fig3/v2/runs/*/score.json`, `fig3/v2/advice_outdated.csv` and `fig3/v2/scenarios.csv`; writes `source_data/fig_scores_v2.json` first (the numbers behind rows b to d), then the SVG. |
| `code/export_png.py` | SVG to PNG with headless Chromium (window taller than the figure, cropped to its size). |
| `source_data/assets/` | The header images: field 104 (DAPI or brightfield) and its manual labels, exported from `data/raw` for round 1. |
| `legend_short.md`, `legend.md` | Short and extended legend drafts; notes for the authors at the end of `legend.md`. |

What each row shows: **a** replies that suggested an outdated model or code (one dot per reply; classification and verbatim
evidence in `fig3/v2/advice_outdated.csv`); **b**, **c** median over three runs of the mean object F1 (IoU 0.5) on the held-out
right halves of fields 104 and 209 ("FOV 1", "FOV 2"), circles = runs, cross = a field failed (counts 0); **d** the count stated
in turn 1 against the manual count. Not shown, but in the repository: area and aspect-ratio results (`score.json`), the drawn
ellipses and the refusals to draw them (`fig3/v2/direct_summary.csv`), code metrics and ratings (`fig3/v2/code_metrics.csv`,
`fig3/v2/code_rating/`), the check of API calls in the advice code (`fig3/v2/advice_api_check.csv`).
