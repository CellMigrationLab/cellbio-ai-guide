# Rebuild and check everything. Run from the repository root.
PY ?= python3
export PYTHONPATH := $(CURDIR)

.PHONY: check full test data fig1 fig2 fig3 pdf

check:            ## tests + checksums + rebuild all figure SVGs and recompute all scores in a temporary copy (no files changed)
	$(PY) tools/check_all.py

full:             ## regenerate Fig 1-2 source data from data/raw, then rebuild the figures (no files changed)
	$(PY) tools/check_full.py

test:             ## all unit tests in the repository's own test folders (never the recorded test files under fig3/v2/runs/)
	$(PY) -m unittest discover -s common/tests -p 'test_*.py' -t .
	$(PY) -m unittest discover -s fig2/tests -p 'test_*.py' -t .
	$(PY) -m unittest discover -s fig3/tests -p 'test_*.py' -t .

data:
	$(PY) data/make_manifest.py --verify

fig1:             ## writes fig1/figure/fig1.svg (step 4 crop: cd fig1/source_data && python ../code/export_fresh_field.py)
	cd fig1/source_data && $(PY) ../code/make_fig1.py

fig2:             ## writes fig2/figure/fig2.svg
	cd fig2/source_data && $(PY) ../code/make_fig2.py

fig3:             ## Figure 3 (protocol v2): SVG, PNG and PDF in fig3/figure_v2/output/ (needs headless Chromium for the PDF)
	cd fig3/figure_v2/source_data && PYTHONPATH=../../.. $(PY) ../code/make_fig3_v2.py && $(PY) ../code/export_png.py && cd ../../.. && $(PY) tools/svg_to_pdf.py fig3/figure_v2/output/fig3_v2.svg

pdf:              ## SVG -> PDF for Figs 1 and 2 with headless Chromium
	$(PY) tools/svg_to_pdf.py fig1/figure/fig1.svg
	$(PY) tools/svg_to_pdf.py fig2/figure/fig2.svg
