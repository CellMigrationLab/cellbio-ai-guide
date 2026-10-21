# Box 1: the reusable prompt

| File | What it is |
|---|---|
| [box1_manuscript.md](box1_manuscript.md) | Box 1 as printed in the article. |
| [box1_tested.md](box1_tested.md) | The Box 1 that was actually tested in Figure 3, written out clean (the article's Box 1 plus the four additions), with where each addition appears. |
| [box1_final.md](box1_final.md) | The same version the "detailed" prompts of Figure 3 were built from (protocol v2, [`fig3/PROTOCOL_V2.md`](../fig3/PROTOCOL_V2.md) section 4; the filled-in prompts are in `fig3/v2/prompts/`). |

**The two are not identical.** `box1_final.md` has four additions (marked ➕ in that file) that are not in the printed
Box 1:

1. a slot for the software and version and the hardware ("I use [software and version] on [hardware]");
2. "Include a test I can run on my annotated example and tell me what result would mean that the analysis failed";
3. "If I ask for counts or measurements, return the masks or outlines they come from";
4. "read and write only inside [working folder]" in the optimisation paragraph.

These came from the pilots (17 Oct 2026). Results of the "detailed" conditions in Figure 3 are therefore for the Box 1
with these four additions. The article's Figure 3 legend does not define the detailed prompt; the authors should either add
the four lines to Box 1 or say in the legend that the detailed prompt is Box 1 plus these additions (see `fig3/README.md`).
