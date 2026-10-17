# Figure 2: Is the deep-learning output good enough for the measurement?

Final version: `figure/fig2.svg` / `fig2.pdf`; legend `legend.md`. Builder `code/make_fig2.py` (= working version v3,
16 Oct 2026), assembled from `code/build_parts/` (`fig2_head.py` + `blk_*.py` + the tail of `fig2_body.py`, see
`build_parts/rebuild.sh`).

## Rebuild and re-score
```
make fig2                                                     # -> figure/fig2.svg, byte-identical
cd fig2/source_data && export PYTHONPATH=../..
python ../code/errors.py && python ../code/score_perturb.py   # ORDER MATTERS: score_perturb adds to errors' summary
python ../code/annot_agree.py; python ../code/bio_result.py; python ../code/al_intensity.py; python ../code/tubule_width.py
python ../code/squirrel_run.py        # NanoPyx environment (environment/requirements-nanopyx.txt)
```
`tools/check_all.py` runs all of these in a temporary copy and checks that every JSON output equals the committed one
(SQUIRREL with `--with-squirrel`; verified: RSE/RSP and error maps identical, NanoPyx 2.1.5).

## Panels, scripts and source data
| Panel | What | Script(s) in `code/` | Files in `source_data/` |
|---|---|---|---|
| a | Cellpose-SAM on brightfield, one setting changed at a time (normalisation, scale, thresholds, post-filter) | `norm_inputs.py` (normalised inputs), `cellpose_perturb.py` (Cellpose 4.2.1.1 runs, CPU), `postfilter.py`, `errors.py` → `score_perturb.py` (F1), `export_window.py` + recovered `data_ts_cp_.sh` (tile outlines) | `data/cp_*.tif` (labels per variant), `data/perturb_scores.json`, `data/error_summary.json`, `data/ts_cp_*.json`, `data4/B_rep_*` (window and reference, from Fig. 1) |
| a | error types (StarDist vs Cellpose) | `errors.py`, `export_errors_window.py`, recovered `data_err_ids_.sh` | `data/err_*.json`, `data/err_bf.png` |
| a | reference agreement between two annotators | `annot_agree.py` | `data/annot_agree.json`, `data/pecam_tile.png` |
| b | decision scheme | (drawn in the builder) | — |
| c | denoising (CARE): intensity ranking preserved, rescaled | `image_generation.py` | `data/dn_*.png`, `data/dn_intensity.json`, `data/dn_mask.json` |
| d | artificial labelling (pix2pix): intermediate step and measurement | `al_roi.py`, `al_gray.py`, `al_intensity.py` | `data/roi*.png/json`, `data/al_*.png`, `data/al_intensity.json` |
| e | super-resolution (RCAN, BioSR): SQUIRREL error map and RSP; line profile; tubule width | `squirrel_run.py`, `squirrel_tile.py` (NanoPyx 2.1.5), `image_generation.py`, `tubule_width.py` | `data/squirrel*.{json,tif}`, `data/sr_*.png/npy/json`, `data/tubule_width.json`, `data/inferno_bar.png` |
| all | biological read-out from each segmentation | `bio_result.py` | `data/bio_result.json` |

`data5/dark_tile.png` comes from the recovered command `code/recovered_inline/data5_dark_tile.png.sh`.
Inputs that are regenerated rather than stored: `data/in_{minmax,histeq,clahe}.tif` (normalised brightfield; `norm_inputs.py`).
Default Cellpose labels are shared with Fig. 1: `../fig1/source_data/full_field/cellpose_sam_labels.tif`.

## Caveats and notes for auditors
- One field of view and one annotator for the cancer cells (124 cells); the endothelial reference has two annotators.
- `data/al_intensity.json` in this repository contains an extra field `r_pixel` (whole-field pixel correlation) that
  `al_intensity.py` does not write: it was added by a recovered inline command
  (`code/recovered_inline/add_r_pixel_to_al_intensity.sh`), shown briefly and then removed from the figure. It is not
  used by the final Figure 2.
- `data/pecam_annotator{1,2}.json`, `data/perturb*.log` and some `ts_cp_*.json` variants are intermediate files not drawn
  in the final figure.
- Published model outputs (custom StarDist, pix2pix, CARE, RCAN) were not re-run; Cellpose and SQUIRREL were.
- Earlier builders: `superseded/`.
