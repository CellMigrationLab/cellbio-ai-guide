# Figure 3 round 1: asking for advice

This folder holds the **round-1 draft** results for the advice comparison. The replacement experiment is described in [protocol v2](../PROTOCOL_V2.md).

The model was asked how to analyse cancer or endothelial cells, either from memory (`runs/from_memory_*`) or after being asked to check current documentation (`runs/after_docs_*`). The draft figure quotes parts of these replies.

The `artifacts/labels.tif` files are **our implementation** of the advice, using [advise_impl.py](code/advise_impl.py). They are not the LLM's own analysis and are not shown in the draft figure.

## An instructive failure

The [cyto3 test](cyto3_silent_fallback/) shows that Cellpose 4.2.1.1 accepts `CellposeModel(pretrained_model='cyto3')` but loads `cpsam_v2` without warning. A recommendation can therefore be outdated even when the resulting code runs. See `output.txt` for the recorded result.
