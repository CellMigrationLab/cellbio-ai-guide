# Figure 1: Using AI in microscopy image analysis

Final version: `figure/fig1.svg` / `fig1.pdf` (builder `code/make_fig1.py`, = working version v16, 16 Oct 2026).

## Rebuild
```
make fig1                 # cd fig1/source_data && python ../code/make_fig1.py  -> figure/fig1.svg (byte-identical)
cd fig1/source_data && PYTHONPATH=../.. python ../code/f1_scores.py   # panel c F1 scores from the label images
```
The builder uses the Python standard library only; it embeds the PNGs in `source_data/` and draws all outlines as vectors.

## Where every file in `source_data/` comes from
| File (as read by the builder) | Panel | Produced by |
|---|---|---|
| `panel_a/detect_input.png`, `panel_a/detect_boxes.json` | a, detection | `code/recovered_inline/data5_detect_*.sh` (DeepBacs growth-stage image and published YOLOv2 boxes, `data/raw/third_party/deepbacs_ecoli_growth_stage`) |
| `panel_a/split_cells.png` | a, segmentation | `code/export_splits.py` |
| `panel_a/split_classif.png` | a, classification | `code/recovered_inline/data5_split_classif.png.sh` (DeepBacs antibiotic phenotyping) |
| `panel_a/split_denoise.png`, `split_label.png`, `split_sr_zoom.png` | a, denoising / artificial labelling / super-resolution | `code/export_splits.py` |
| `panel_b/panelA_acquired_crop.png` | b, attached image | `code/segment_panelA.py` |
| `panel_c_steps2_4/rep0.png`, `rep1.png`, `rep2.png` | c, step 2 reference fields | **producer not recovered**: 260 × 260 px crops of `field104_brightfield.tif` at (y, x) = (40, 240), (600, 620), (700, 60), resized to 300 px |
| `panel_c_step3/B_rep_bf.png`, `panel_c_step3/B_rep_{ref,cellpose,stardist}.json` | c, step 3 window | `code/export_rep_window.py` (window chosen by `code/find_rep_window.py`) |
| `panel_c_steps2_4/rep_classical.json` | c, step 3 threshold | `code/classical_seg.py` |
| `panel_c_step3/A_scores.json` | c, step 3 F1 | `code/f1_scores.py` reproduces it from `full_field_labels/*.tif` and `data/raw` (original: `code/recovered_inline/data4_A_scores.json.sh`) |
| `panel_c_steps2_4/test_bf.png`, `test_ref.json`, `test_stardist.json` | c, step 4 | `code/recovered_inline/data8_test_bf.png.sh` |
| `panel_c_step5/trackmate_crop.png` | c, step 5 | `code/recovered_inline/data9_trackmate_crop.png.sh` |
| `full_field_labels/cellpose_sam_labels.tif` | c (scores), Figs 2–3 | `code/segment_bf_cellpose.py` (Cellpose 4.2.1.1, default `cpsam`, CPU) |
| `full_field_labels/threshold_labels.tif` | c (scores) | `code/classical_seg.py` |

Recovered commands (`code/recovered_inline/`) are copied verbatim from the session transcripts; their paths are those of
the original working folder (`U` = the upload folder, now `data/raw/` with the names in `data/raw_name_map.csv`;
`dl_deepbacs`, `dl_abx` = `data/raw/third_party/`). Other scripts in `code/` were explorations for earlier versions
(`compare_*.py`, `b12.py`, `b13.py`, `export_bf_example.py`, `agent_run.py`); earlier builders are in `superseded/`.

Changes in v16 relative to the provenance notes below (written for the data package of 16 Oct, 11:58): the step-3
candidates are labelled "Pre-trained generalist" and "Custom-trained"; the super-resolution tile is a 2× zoom
(`split_sr_zoom.png`, 31.3 nm pixels, 1 µm scale bar). Panel-c tile file names in the notes below refer to the package;
the table above gives the names used here.

## Provenance

Two caveats are listed first because they affect what the figure claims.

> **Caveat 1 — panel c steps 2–4 use one field of view.** The reference images (step 2), the comparison window (step 3) and the "unseen image" (step 4) are all crops of the same brightfield field (`data/raw/field104_brightfield.tif`). The step-4 crop overlaps the step-2 crop `step2_reference_image_1.png` almost completely, and the F1 scores are computed over this whole field. The figure illustrates the workflow; it does not show a genuinely independent final check.
>
> **Caveat 2 — the classification tile is not one field.** The right half of the classification tile is a gallery of cells from other test images in the same dataset (two per class), not the classification output for the cells in the left half.

### Panel a — deep-learning examples

| File | Source | Processing |
|---|---|---|
| `detection_input.png`, `detection_boxes.json` | DeepBacs *E. coli* growth-stage dataset and YOLOv2 model, Spahn et al. 2022 (*Commun. Biol.*, doi:10.1038/s42003-022-03634-z); Zenodo doi:10.5281/zenodo.5551016, CC BY 4.0. Image `image_patches/test_images/pos_8_frame_80_2.png`; boxes from the model archive's `Quality Control/predicted_bounding_boxes_for_custom_ROI_QC.csv` | Published predictions (model not re-run). 14 boxes: 8 rod, 3 dividing, 3 microcolony. 256 × 256 px, 0.5–99.5 percentile stretch. Pixel size for the scale bar: 160 nm (the paper quotes 158 nm — to confirm) |
| `segmentation_input_output.png` | Brightfield cancer cells and custom StarDist labels, Follain et al. 2026 (*EMBO J.*, doi:10.1038/s44318-025-00678-9); 0.649614 µm/px | Model not re-run. Crop y 60–270, x 200–410; 0.3–99.7 percentile stretch; nearest-neighbour resize. Left half input, right half label overlay. `code/export_splits.py` |
| `classification_input_output.png` | DeepBacs antibiotic phenotyping, Zenodo doi:10.5281/zenodo.5551057, CC BY 4.0; input `test/stitched_images/images/synthetic_image_23.png`, predictions from the model archive's QC CSV | Published predictions (model not re-run). Left: x 60–260 of the input. Right: two highest-confidence (> 0.6) cells per class (Control, Mecillinam, Nalidixate, Rifampicin) from other test images, box ± 6 px. **See caveat 2** |
| `denoising_input_output.png` | CARE denoising, provided by the authors (raw uint16 / restored float32), 0.6337 µm/px | Crop y 640–840, x 520–720; each half stretched to its own 0.3–99.7 percentiles. `code/export_splits.py` |
| `artificial_labelling_input_output.png` | Brightfield plus pix2pix-predicted DAPI and PECAM-1, Follain et al. 2026 | Predictions shifted by 1 row to register with the brightfield. Crop y 560–770, x 620–830; DAPI magenta, PECAM-1 green. `code/export_splits.py` |
| `super_resolution_input_output.png` | Endoplasmic reticulum, low-resolution input and RCAN prediction; data from Qiao et al. 2021 (*Nat. Methods*, doi:10.1038/s41592-020-01048-5); RCAN, Zhang et al. ECCV 2018; input 62.6 nm/px, prediction on the 2× grid 31.3 nm/px (BioSR values; not in the TIFF metadata) | Prediction crop y 160–300, x 600–740; matching 70 px input crop; separate stretches. `code/export_splits.py` |

### Panel b — LLM uses

| File | Source | Processing |
|---|---|---|
| `nuclei_image_card4.png` | Authors' image: HPMEC nuclei, max projection, 0.158436 µm/px (`MAX_2026.02.24_ECs_AsPC-1perfusion…Position 1-1.tif`) | Crop x 0–600, y 1248–2048; linear display 100–600. `code/segment_panelA.py` |

All prompts and replies in panel b are illustrative and were written for the figure; they are not recorded model outputs.

### Panel c — starting a project

| File | Source | Processing |
|---|---|---|
| `data/raw/field104_brightfield.tif` | Brightfield cancer cells, Follain et al. 2026, 1022 × 1024 px, 0.649614 µm/px | — |
| `data/raw/field104_cancer_cells_manual_labels.tif` | Manual cancer-cell annotation of the same field, 124 cells, provided by the authors | — |
| `data/raw/field104_cancer_cells_stardist_custom_labels.tif` | Custom StarDist model (ZeroCostDL4Mic), Follain et al. 2026 | Model not re-run |
| `full_field_labels/cellpose_sam_labels.tif` | Cellpose 4.2.1.1, default `cpsam` weights, default settings, CPU, whole field | `code/segment_bf_cellpose.py` |
| `full_field_labels/threshold_labels.tif` | Classical pipeline: Gaussian σ = 1 → local s.d. (7 px) → Otsu → closing (disk 3) → fill holes → remove < 250 px → opening (disk 4) → distance-transform watershed (min distance 12); parameters not tuned | `code/classical_seg.py` |
| `step2_reference_image_{0,1,2}.png` | Crops of `brightfield.tif`, 260 × 260 px at (y, x) = (40, 240), (600, 620), (700, 60), resized to 300 px | Image 0 carries the manual annotation outlines |
| `step3_*` | Window x 240–480, y 40–300, chosen by `code/find_rep_window.py` so that its local scores resemble the whole-field scores | Vector contours (`find_contours` + `approximate_polygon`, tolerance 0.6). `code/export_rep_window.py`, `code/classical_seg.py` |
| `step4_*` | Window x 600–840, y 620–880 of the **same** field. **See caveat 1** | As above |
| `step5_trackmate_tracks.png` | TrackMate capture provided by the authors, 1.31483 µm/px | Crop y 520–800, x 200–480; Lanczos resize to 472 px |

### F1 scores (panel c, step 3)

Object-level F1 over the whole field against `manual_annotation_labels.tif` (124 cells). Each pair of overlapping objects is scored by IoU; pairs are matched greedily from the highest IoU, one-to-one, keeping IoU ≥ 0.5. F1 = 2TP / (2TP + FP + FN). No edge exclusion; one image.

| Candidate | Objects | TP | FP | FN | F1 | Shown |
|---|---|---|---|---|---|---|
| Threshold | 187 | 59 | 128 | 65 | 0.379 | 0.38 |
| Cellpose-SAM | 191 | 122 | 69 | 2 | 0.775 | 0.78 |
| StarDist (custom) | 102 | 97 | 5 | 27 | 0.858 | 0.86 |

Reproduced by `code/f1_scores.py`. If this field was part of the StarDist training set, its score is optimistic.

## Still to confirm before deposit

- Licence and deposit for the authors' own data: the Follain et al. brightfield/StarDist/pix2pix files (the paper lists Zenodo doi:10.5281/zenodo.17232437 and the community `pdac_dl`), the denoising pair, the HPMEC nuclei image and the TrackMate capture.
- Super-resolution data: which Qiao et al. file and cell, who trained the RCAN model, and the licence.
- CARE denoising: training data and version; confirm which file is raw and which is restored.
- TrackMate capture: source experiment, detector and tracker.
- Manual annotation `manual_annotation_labels.tif`: who drew it, with which tool, and whether this field was used to train the StarDist model.
- DeepBacs detection pixel size (160 vs 158 nm).

## Folder names
`source_data/` folders were renamed after porting (17 Oct 2026) to the panel they feed: `data` → `panel_b`,
`data4` → `panel_c_step3`, `data5` → `panel_a`, `data8` → `panel_c_steps2_4`, `data9` → `panel_c_step5`,
`full_field` → `full_field_labels`. Recovered commands in `code/recovered_inline/` keep the original names.
