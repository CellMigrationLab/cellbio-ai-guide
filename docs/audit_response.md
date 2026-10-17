# Response to the audit (`audit_findings.md`)

The audit itself is kept unchanged. This file records, per finding, what was done and where, in the order the
authors chose ("merge and fix in order", 17 Oct 2026). `python3 tools/check_all.py` is re-run after every item.

| Finding | Status | What changed |
|---|---|---|
| P0.1 stale Fig. 1 output paths | Fixed | `fig1/code/fig1_paths.py` holds the canonical label paths (`full_field_labels/cellpose_sam_labels.tif`, `threshold_labels.tif`); every producer and consumer imports them. Producers write zlib-compressed TIFFs as stored, and `classical_seg.py` re-run in a copy of `fig1/source_data` reproduces every file byte for byte. |
| P0.2 `make check` is not raw-to-figure | Open | A full check from raw data in an empty copy is planned; the current check is the fast one. |
| P0.3 Fig. 1c not a fresh image | Fixed (one item to confirm) | Step 4 is now a crop of field 209 (`fig1/code/export_fresh_field.py`; window chosen by a fixed rule; StarDist F1 0.89 whole field and crop); checked byte for byte by `check_all`. Fig. 1 SVG and PDF rebuilt (PDF by `tools/svg_to_pdf.py`). Whether field 209 was in the custom StarDist training set is still to be confirmed by the authors. |
| P0.4 / P0.5 Fig. 3 split | Fixed | No split inside a field: field 104 is development, field 209 is the test field (`fig3/STRATEGY.md` §2). |
| P0.6 BioSR pixel size | Fixed | Input 62.6 nm/px, prediction and reference on the 2× grid at 31.3 nm/px (BioSR values; the TIFFs carry none). The figure already used 31.3 nm. `fig2/code/image_generation.py` and `panels/sr_profile.json` now store `px_nm` 31.3 and `lowres_px_nm` 62.6; the Fig. 1 README is corrected; `fig2/tests/test_biosr_pixel_size.py` checks the 2× shapes and every stored value. Figure SVGs unchanged (`px_nm` is not drawn). |
| P1.8 duplicate code | Partly fixed | Removed `fig1/code/compare_cancer_gt_lib.py` and `fig2/code/matching.py` (all callers use `common/matching.py`); `lines_to_cells` is shared in `common/annotations.py`. Archived scripts under `fig3/harness/` and `superseded/` keep their original imports on purpose. |
| P1.9 greedy matching | Disputed, to document | With non-overlapping labels and IoU > 0.5, each object can match at most one partner, so greedy matching equals optimal matching. Tests for ties, IoU exactly 0.5 and empty images to be added. |
| Other P1 / P2 items | Open | Scope labels in the legends only (authors' decision); the rest follows in order. |
