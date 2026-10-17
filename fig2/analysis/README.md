# Exploratory CARE intensity analysis

**Not included in the final Figure 2.** This analysis asks whether CARE restoration changes the relation between measured nuclear intensities and an acquired higher-SNR reference.

[care_linearity.py](care_linearity.py) measures background-subtracted mean intensity per nucleus in the low-SNR input, CARE output and higher-SNR acquisition of the same field. Results are saved in `care_linearity.json` and `care_linearity.png`.

## What the comparison found

The low-SNR and restored measurements were nearly proportional (log–log slope 1.03, confidence interval 0.98–1.09; gain 1.55), regardless of which of the tested images supplied the nuclear masks.

Against the higher-SNR acquisition, correlations were similar for low-SNR and restored images (r = 0.945 and 0.942). Both differed from the higher-SNR values for dim nuclei, where an offset of roughly 2,500–3,000 counts was apparent. Comparing only input with restoration would not reveal that discrepancy.

## Why this is still exploratory

The slope against the higher-SNR acquisition depends strongly on the nuclear masks: 0.90/0.74 with masks from the higher-SNR image versus 1.32/1.31 with the Figure 2c masks. Before using these results in a figure, review the masks, test local per-nucleus background estimates and verify acquisition exposure and offset settings.

This analysis does **not** establish that CARE intensities can be substituted for acquired intensities in quantitative measurements.
