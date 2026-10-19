# Rebuild and check everything. Run from the repository root.
PY ?= python3
export PYTHONPATH := $(CURDIR)

.PHONY: check full test data fig1 fig2 fig3 fig3v2 pdf scores

check:            ## tests + checksums + rebuild all figures and scores in a temporary copy (no files changed)
	$(PY) tools/check_all.py

full:             ## regenerate Fig 1-2 source data from data/raw, then rebuild the figures (no files changed)
	$(PY) tools/check_full.py

test:             ## all unit tests
	$(PY) -m unittest discover -s . -p 'test_*.py' -t .

data:
	$(PY) data/make_manifest.py --verify

fig1:             ## writes fig1/figure/fig1.svg (step 4 crop: cd fig1/source_data && python ../code/export_fresh_field.py)
	cd fig1/source_data && $(PY) ../code/make_fig1.py

fig2:             ## writes fig2/figure/fig2.svg
	cd fig2/source_data && $(PY) ../code/make_fig2.py

fig3:             ## writes fig3/figure/output/fig3.svg
	cd fig3/figure/source_data && $(PY) ../code/make_fig3.py

fig3v2:           ## draft Figure 3 (protocol v2) from the stored main runs
	cd fig3/figure_v2/source_data && PYTHONPATH=../../.. $(PY) ../code/make_fig3_v2.py

pdf:              ## SVG -> PDF for Figs 1 and 2 with headless Chromium
	$(PY) tools/svg_to_pdf.py fig1/figure/fig1.svg
	$(PY) tools/svg_to_pdf.py fig2/figure/fig2.svg

scores:           ## recompute Fig 3 scores and compare with the figure
	$(PY) fig3/scoring/build_scores.py --check
