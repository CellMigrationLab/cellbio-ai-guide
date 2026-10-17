# Environments

| Purpose | Requirements | Notes |
|---|---|---|
| Rebuild figures, recompute scores, run tests (`make check`, `make full`) | `python3 -m pip install -r environment/requirements.txt` | Python 3.13; the figure builders need only the standard library |
| Re-run Cellpose segmentations (`python tools/check_full.py --with-models`) | `python3 -m pip install -r environment/requirements-models.txt --extra-index-url https://download.pytorch.org/whl/cpu` (the `+cpu` torch build is only on the PyTorch index) | `pretrained_model='cyto3'` silently loads `cpsam_v2` in this version (Fig 3a) |
| SQUIRREL (Fig 2e; `--with-squirrel`) | `requirements-nanopyx.txt`, in its own virtual environment | separate environment because of NumPy pins |
| Fiji macros (Fig 3b) | plain Fiji (Linux x64, downloaded 16 Oct 2026), no update sites added | run headless: `xvfb-run -a ImageJ-linux64 -batch macro.ijm` |
| LLM runs (Fig 3) | Claude Code sub-agents, model claude-sonnet-5-5 | not reproducible bit-for-bit; transcripts are stored in `fig3/*/runs/` |

PDFs are rendered from the SVGs with headless Chromium: `make pdf` (`tools/svg_to_pdf.py`).
