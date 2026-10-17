# Rebuild and check everything. Run from the repository root.
PY ?= python3
export PYTHONPATH := $(CURDIR)

.PHONY: check test data fig1 fig2 fig3 scores

check:            ## tests + checksums + rebuild all figures and scores in a temporary copy (no files changed)
	$(PY) tools/check_all.py

test:
	$(PY) -m unittest discover -s common -t .

data:
	$(PY) data/make_manifest.py --verify

fig1:             ## writes fig1/figure/fig1.svg
	cd fig1/source_data && $(PY) ../code/make_fig1.py

fig2:             ## writes fig2/figure/fig2.svg
	cd fig2/source_data && $(PY) ../code/make_fig2.py

fig3:             ## writes fig3/figure/output/fig3.svg
	cd fig3/figure/source_data && $(PY) ../code/make_fig3.py

scores:           ## recompute Fig 3 scores and compare with the figure
	$(PY) fig3/scoring/build_scores.py --check
