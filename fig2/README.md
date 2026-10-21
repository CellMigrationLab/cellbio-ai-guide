# Figure 2: Is the deep-learning output good enough for the measurement?

Final version: `figure/fig2.svg` / `fig2.pdf`; legend `legend.md`. Builder `code/make_fig2.py` (working version v3 of
16 Oct 2026; panels a and e updated 17 Oct 2026; layout tightened 20 Oct 2026).

## Rebuild and re-score
```
make fig2                                                     # -> figure/fig2.svg, byte-identical
cd fig2/source_data && export PYTHONPATH=../..
python ../code/postfilter.py --threshold 50                  # panels/cp_postfilter.tif (--scan prints thresholds 30-70)
python ../code/errors.py && python ../code/score_perturb.py   # ORDER MATTERS: score_perturb adds to errors' summary
python ../code/annot_agree.py; python ../code/bio_result.py; python ../code/al_intensity.py; python ../code/tubule_width.py
python ../code/squirrel_run.py        # NanoPyx environment (environment/requirements-nanopyx.txt)
```
`tools/check_all.py` runs the scoring scripts (not the Cellpose runs, `norm_inputs.py` or `postfilter.py`, which
need the models) in a temporary copy and checks that every JSON output equals the committed one
(SQUIRREL with `--with-squirrel`; verified: RSE/RSP and error maps identical, NanoPyx 2.1.5).

## Panels, scripts and source data
| Panel | What | Script(s) in `code/` | Files in `source_data/` |
|---|---|---|---|
| a | Cellpose-SAM on brightfield, one setting changed at a time (normalisation, scale, thresholds, post-filter) | `norm_inputs.py` (normalised inputs), `cellpose_perturb.py` (Cellpose 4.2.1.1 runs, CPU), `postfilter.py`, `errors.py` → `score_perturb.py` (F1, field 104), `score_fields.py` (F1 on fields 104 and 209, mean), `export_window.py` + recovered `data_ts_cp_.sh` (tile outlines) | `panels/cp_*.tif` and `panels/field209/cp_*.tif` (labels per variant), `panels/perturb_scores.json`, `panels/perturb_scores_fields.json`, `panels/error_summary.json`, `panels/ts_cp_*.json`, `from_fig1_panel_c/B_rep_*` (window and reference, from Fig. 1) |
| a | error types (StarDist vs Cellpose) | `errors.py`, `export_errors_window.py`, recovered `data_err_ids_.sh` | `panels/err_*.json`, `panels/err_bf.png` |
| a | reference agreement between two annotators | `annot_agree.py` | `panels/annot_agree.json`, `panels/pecam_tile.png` |
| b | decision scheme | (drawn in the builder) | — |
| c | denoising (CARE): intensity ranking preserved, rescaled | `image_generation.py` | `panels/dn_*.png`, `panels/dn_intensity.json`, `panels/dn_mask.json` |
| d | artificial labelling (pix2pix): intermediate step and measurement | `al_roi.py`, `al_gray.py`, `al_intensity.py` | `panels/roi*.png/json`, `panels/al_*.png`, `panels/al_intensity.json` |
| e | super-resolution (RCAN, BioSR): SQUIRREL error map and RSP; line profile; tubule width | `squirrel_run.py`, `squirrel_tile.py` (NanoPyx 2.1.5), `image_generation.py`, `tubule_width.py` | `panels/squirrel*.{json,tif}`, `panels/sr_*.png/npy/json`, `panels/tubule_width.json`, `panels/inferno_bar.png` |
| all | biological read-out from each segmentation | `bio_result.py` | `panels/bio_result.json` |

`from_fig1_panel_a/dark_tile.png` comes from the recovered command `code/recovered_inline/data5_dark_tile.png.sh`.
Inputs that are regenerated rather than stored: `panels/in_{minmax,histeq,clahe}.tif` (normalised brightfield; `norm_inputs.py`).
Default Cellpose labels are shared with Fig. 1: `../fig1/source_data/full_field_labels/cellpose_sam_labels.tif`.

## Caveats and notes for auditors
- Panel a: two fields of one experiment (field 104, 124 cancer cells; field 209, 163), one annotator for the cancer
  cells; the endothelial reference (panel d) has two annotators. Panels b–e use one field or one image each.
- `panels/al_intensity.json` in this repository contains an extra field `r_pixel` (whole-field pixel correlation) that
  `al_intensity.py` does not write: it was added by a recovered inline command
  (`code/recovered_inline/add_r_pixel_to_al_intensity.sh`), shown briefly and then removed from the figure. It is not
  used by the final Figure 2.
- Panel e tubule width: sampling revised on 17 Oct 2026 (code audit). The former rule (both skeletons, every 12th image
  row) over-weighted horizontal tubules and dropped failed locations silently (2,450 locations, −12.6 nm). Now: reference
  skeleton, minimum spacing 12 px in all directions, exclusions counted (`summary.sampling` in `tubule_width.json`):
  1,301 locations, −9.4 nm, noise floor 11.7 vs 20.4 nm. Tested in `tests/test_tubule_sampling.py`.
- Panel a on two fields (17 Oct 2026): every variant was re-run on field 209 (`norm_inputs.py`, `cellpose_perturb.py`
  and `postfilter.py` with `--field 209`; outputs in `panels/field209/`) and scored by `score_fields.py`, which also
  checks that the field-104 values equal `perturb_scores.json`. The bars show the mean of the two fields, dots each
  field (`panels/perturb_scores_fields.json`). The post-filter threshold (50) was chosen on field 104 only.
- `panels/squirrel.json` contains the runtime of each SQUIRREL call (`"s"`), which `squirrel_run.py` now prints instead
  of storing (it is not a result and varies between runs); the checks ignore that key.
- `panels/pecam_annotator{1,2}.json` and some `ts_cp_*.json` variants are intermediate files not drawn
  in the final figure.
- Published model outputs (custom StarDist, pix2pix, CARE, RCAN) were not re-run; Cellpose and SQUIRREL were.

## Folder names
`source_data/` folders were renamed after porting (17 Oct 2026): `data` → `panels`, `data4` → `from_fig1_panel_c`,
`data5` → `from_fig1_panel_a`. Recovered commands in `code/recovered_inline/` keep the original names.
