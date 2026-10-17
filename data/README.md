# Data

Everything the figures need is in `raw/`; nothing is downloaded at build time.

| File | What it is |
|---|---|
| `raw/` | Raw images and annotations, unchanged bytes (verify with `python data/make_manifest.py --verify`) |
| `raw/third_party/` | The DeepBacs files used in Fig. 1a (test images, published model predictions, QC tables, our parsing scripts) |
| `raw_name_map.csv` | Original upload name → repository name, source and content of every authors' file |
| `sources.csv` | Full citation, DOI and licence for every source key |
| `manifest.csv` | Path, size, SHA-256 and source key of every file in `raw/` |
| `make_manifest.py` | Writes or verifies `manifest.csv` |

## The main field of view (Figs 1–3)

One brightfield field of cancer cells on a confluent endothelial monolayer, with acquired DAPI and PECAM-1 of the same
field (Follain et al. 2026, EMBO J; 1022 × 1024 px, 0.649614 µm/px, written 0.65 µm in the figures):

| File | Content |
|---|---|
| `field104_brightfield.tif` | brightfield (uint16) |
| `field104_dapi.tif`, `field104_pecam1.tif` | acquired DAPI and PECAM-1 |
| `field104_cancer_cells_manual_labels.tif` | 124 manually annotated cancer cells |
| `field104_endothelial_nuclei_manual_labels.tif` | 441 manually annotated endothelial nuclei (drawn on DAPI) |
| `field104_endothelial_junctions_annotator1.tif` / `_annotator2.tif` | endothelial cell outlines drawn on PECAM-1 by two annotators (lines; converted to cells by `lines_to_cells`, 382 / 369 complete cells, agreement F1 0.90) |
| `field104_cancer_cells_stardist_custom_labels.tif` | custom StarDist model output (published predictions, not re-run) |
| `field104_pix2pix_predicted_{dapi,pecam1}.tif` | pix2pix predictions from brightfield (1024 × 1024; one-row offset to the brightfield, corrected in the scripts) |
| `field104_pix2pix_*_labels.tif`, `_outlines.tif` | segmentations of the predicted images provided by the authors |

To confirm before release: annotator names, annotation tool and dates (add to this table).

## Other images
`care_denoising_{acquired,restored}.tif` (Fig. 1a, 2c), `biosr_er_{lowres_input,rcan_prediction,highres_reference}.tif`
(Fig. 1a, 2e), `hpmec_nuclei_max_projection.tif` (Fig. 1b), `trackmate_capture_tracks.tif` (Fig. 1c). Two TrackMate PDF
reports were explored for Fig. 1 and are not shown.

## Licences and citation
Images and annotations produced by the authors: **CC BY 4.0** (see `LICENSE-content.md`). Third-party data keep their
own licence (DeepBacs: CC BY 4.0, Zenodo 10.5281/zenodo.5551016 and 10.5281/zenodo.5551057; BioSR: CC BY 4.0, to confirm).
If you use the data, cite the sources in `sources.csv`. To double-check before release: the BioSR licence, and the DOIs
listed for Cellpose-SAM and NanoPyx.

## Sanity check: every image with its annotation
`overview.png` (made by `PYTHONPATH=. python data/make_overview.py`) is organised by question (one row each): the
images (grey bar) and, separately, the annotations or references (green bar), with object counts read from the
annotation files. Manual annotations exist
for **one field** (field 104: 124 cancer cells, 382 / 369 endothelial cells by two annotators, 441 endothelial nuclei)
and for the DeepBacs examples (dataset ground truth). The CARE, BioSR, HPMEC and TrackMate images have no manual
annotation (BioSR is compared with its high-resolution acquisition).

## Adding data
Send files under any name; `python data/add_raw_files.py` copies them unchanged to `raw/` with standard names
(`field<N>_<role>.tif`, e.g. `field105_brightfield.tif`, `field105_cancer_cells_manual_labels.tif`; or
`<prefix>_<role>.tif`, e.g. `care_denoising_highsnr_reference.tif`), checks shapes and label types, and updates
`raw_name_map.csv` and `manifest.csv`. Pending (requested 17 Oct 2026): one more annotated field (Fig 3 test image) and
a ground truth for the CARE example.
