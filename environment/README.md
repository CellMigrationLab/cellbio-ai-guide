# Environments

| Purpose | Requirements | Notes |
|---|---|---|
| Rebuild figures, recompute scores, run tests | `requirements.txt` (first block) | Python 3.13; the figure builders need only the standard library |
| Re-run Cellpose segmentations | `requirements.txt` (Cellpose 4.2.1.1, torch CPU) | `pretrained_model='cyto3'` silently loads `cpsam_v2` in this version (Fig 3a) |
| SQUIRREL (Fig 2e) | `requirements-nanopyx.txt` | separate environment because of NumPy pins |
| Fiji macros (Fig 3b) | plain Fiji (Linux x64, downloaded 16 Oct 2026), no update sites added | run headless: `xvfb-run -a ImageJ-linux64 -batch macro.ijm` |
| LLM runs (Fig 3) | Claude Code sub-agents, model claude-sonnet-5-5 | not reproducible bit-for-bit; transcripts are stored in `fig3/*/runs/` |

Rendering the SVG previews to PNG/PDF used headless Chromium (`fig*/code/build_parts/render.sh`).
