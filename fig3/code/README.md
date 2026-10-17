# Figure 3 round 1: asking for code

These are the **round-1 draft** code-generation runs, not the planned replacement experiment ([protocol v2](../PROTOCOL_V2.md)).

The LLM wrote Fiji macros (row b1) or Python scripts (row b2) for nuclei, cancer cells and endothelial cells. Each task was tried with a short generic request and with the then-current [Box 1 v2 prompt](../../box1/box1_v2_used_in_figure3.md), three runs per condition.

The model could inspect an image preview but could not execute its code. We ran the returned scripts separately.

## Reading a run

Run folders follow `runs/{fiji,python}_{generic,box1}_{nuclei,cancer,endothelial}_r{1,2,3}`.

- `conversation.md` contains the returned code and the full exchange.
- `artifacts/script.py` or `artifacts/macro.ijm` is the version that was executed.
- `artifacts/labels.tif` is the resulting segmentation, if one was produced.
- The run log and metadata record execution details.

For Fiji, input and output paths were replaced by absolute paths before execution. The changes are described in [deviations.md](../deviations.md). A missing output was scored as zero in this historical round; it should not be confused with a valid empty segmentation.

The first generic Python runs for cancer and endothelial cells came from a two-target request rather than separate prompts. See the original conversations before comparing those runs.
