# Exploratory analyses (not in the final Figure 2)

## CARE intensity linearity against the high-SNR acquisition (`care_linearity.py`, 17 Oct 2026)
Per-nucleus background-subtracted mean intensity in the noisy input, the CARE output and the high-SNR acquisition of
the same field (`data/raw/care_denoising_*.tif`). Results: `care_linearity.json`, plot `care_linearity.png`.

- **Noisy vs restored** (the Fig 2c comparison): proportional (log-log slope 1.03, CI 0.98–1.09; gain 1.55, no trend
  with intensity), whichever image the nuclei are segmented on. CARE behaves as a near-linear rescaling of its input.
- **Against the high-SNR acquisition**, noisy and restored behave the same way (r 0.945 vs 0.942). Neither is
  proportional: dim nuclei keep a floor of ≈ 2,500–3,000 counts in the high-SNR image while they approach zero in the
  noisy and restored images (an offset, not a power law). So CARE does not add a new non-linearity here, but the
  comparison with acquired high-SNR data shows a mismatch that the input-vs-output comparison cannot reveal.
- **Not robust yet**: the log-log slopes against high-SNR change with the nuclear mask (0.90/0.74 with nuclei segmented
  on the high-SNR image, 1.32/1.31 with the Fig 2c mask from the restored image), because the offset dominates the dim
  nuclei. Before using this in a figure: a reviewed nuclear mask and a local (per-nucleus ring) background, and a check
  of acquisition settings (exposure, offset) between the low- and high-SNR images.
