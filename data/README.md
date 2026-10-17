# Microscopy data and annotations

The images, annotations and model outputs used in Figures 1–3 are stored in [raw/](raw/). Nothing is downloaded when the figures are built.

[View the dataset overview](overview.png) to see the images alongside their annotations or reference images.

## Find the data

| Location | What you will find |
|---|---|
| [raw/](raw/) | Original image and annotation files, kept byte-for-byte |
| [raw/third_party/](raw/third_party/) | DeepBacs examples used in Figure 1a |
| [raw_name_map.csv](raw_name_map.csv) | Original upload names and their repository filenames |
| [sources.csv](sources.csv) | Source papers, DOIs, licences and permission notes |
| [manifest.csv](manifest.csv) | File sizes, source keys and SHA-256 checksums |

## Cancer cells on an endothelial monolayer

Fields **104** and **209** are from the same experiment (Follain et al., 2026). Both contain brightfield, acquired DAPI and PECAM-1 images, with manual annotations prepared by the Jacquemet lab using Fiji for the FlowVision paper. The pixel size is 0.649614 µm; figures use the rounded value 0.65 µm.

| Annotation | Field 104 | Field 209 |
|---|---:|---:|
| Cancer cells | 124 | 163 |
| Endothelial nuclei | 441 | 473 |
| Complete endothelial cells, annotator 1 | 382 | 388 |
| Complete endothelial cells, annotator 2 | 369 | 345 |

The endothelial cell annotations are junction lines drawn on PECAM-1 and converted into cell regions using [lines_to_cells](../common/annotations.py). The two annotators agree at object F1 = 0.90 on field 104. The annotator-2 file for field 209 contains two nonzero pixel values; both represent junction lines.

The main files follow the pattern `field104_<description>.tif` or `field209_<description>.tif`. For example:

- `field104_brightfield.tif`, `field104_dapi.tif`, `field104_pecam1.tif`: acquired images.
- `field104_cancer_cells_manual_labels.tif`: manually outlined cancer cells.
- `field104_endothelial_nuclei_manual_labels.tif`: endothelial nuclei annotated on DAPI.
- `field104_endothelial_junctions_annotator1.tif`: manually drawn junction lines.
- `field104_cancer_cells_stardist_custom_labels.tif`: published custom StarDist predictions.
- `field104_pix2pix_predicted_dapi.tif` and `field104_pix2pix_predicted_pecam1.tif`: predicted fluorescence channels from brightfield.

Equivalent field-209 files use the same naming scheme. The two fields were not used to train the custom StarDist model. Field 209 is used for a separate-field check in Figures 1 and 2 and is reserved as the test field in the Figure 3 protocol v2. It is **not** an independent biological repeat.

The pix2pix outputs are 1024 × 1024 pixels and have a one-row offset relative to the acquired images (1022 × 1024). The analysis applies the checked alignment in [common/pix2pix.py](../common/pix2pix.py). The alignment of field 209 was also inspected visually.

## Other images

| Files | What they show |
|---|---|
| `care_denoising_acquired.tif`, `care_denoising_restored.tif` | Low-SNR acquired image and CARE restoration (Figures 1a and 2c); pixel size 0.6337 µm |
| `care_denoising_highsnr_reference.tif` | Higher-SNR acquisition of the same field; used in [exploratory analysis](../fig2/analysis/README.md), not the final figure |
| `biosr_er_lowres_input.tif`, `biosr_er_rcan_prediction.tif`, `biosr_er_highres_reference.tif` | Endoplasmic reticulum, RCAN super-resolution and acquired higher-resolution reference (Figures 1a and 2e) |
| `hpmec_nuclei_max_projection.tif` | HPMEC nuclei in Figure 1b; pixel size 0.158436 µm |
| `trackmate_capture_tracks.tif` | Tracking example in Figure 1c; pixel size 1.31483 µm |
| `trackmate_tracks_*.pdf` | Reports explored during figure development but not shown |
| `raw/third_party/deepbacs_*` | Published bacterial detection and classification examples in Figure 1a |

CARE, BioSR, HPMEC and TrackMate images have no manual annotation in this repository; BioSR has an acquired higher-resolution reference. The [overview](overview.png) makes the distinction visible.

## Verify or add data

Check that the original files have not changed:

```bash
python data/make_manifest.py --verify
```

The script [add_raw_files.py](add_raw_files.py) copies new uploads without changing their bytes, checks image shapes and label types, and updates the name map and manifest. Standard filenames use `field<N>_<role>.tif` or `<prefix>_<role>.tif`.

## Sources and licences

See [sources.csv](sources.csv) for the original paper, DOI and licence for each dataset. Authors' images and annotations are covered by [CC BY 4.0](../LICENSE-content.md); third-party data retain their own licences. DeepBacs source data: 10.5281/zenodo.5551016 and 10.5281/zenodo.5551057. The Follain et al. paper lists a related deposit at 10.5281/zenodo.17232437. Check the source record before reusing any individual file.

## Information to confirm before release

The individual annotators' names and annotation dates remain unrecorded (the Jacquemet lab prepared the annotations using Fiji for the FlowVision paper); the CARE model version and training data; the TrackMate experiment and tracking settings; or the exact BioSR source file/cell and RCAN training provenance. These details should be confirmed by the authors rather than inferred. The [Figure 1 provenance notes](../fig1/README.md) list the remaining source-specific questions.
