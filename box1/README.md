# Box 1: the reusable prompt

Box 1 of the article is a prompt template for asking an LLM to produce an image-analysis workflow that can be inspected and
tested. This folder holds it in two forms.

| File | What it is |
|---|---|
| [box1_manuscript.md](box1_manuscript.md) | Box 1 exactly as printed in the article. Copy this one. |
| [box1_tested.md](box1_tested.md) | The version used for the "detailed" prompts of Figure 3: the printed Box 1 plus four lines added after the pilots, with a table of which rows received each line. |
| [box1_final.md](box1_final.md) | The working copy of that tested version, with the four additions marked ➕. It is one of the frozen protocol files (`fig3/v2/FREEZE.json`); `fig3/v2/make_protocol.py` fills it in per task to make the prompts in `fig3/v2/prompts/`. |

The four additions that the tested version has and the printed Box 1 does not:

1. a slot for the software, its version and the hardware ("I use [software and version] on [hardware]");
2. "Include a test I can run on my annotated example and tell me what result would mean that the analysis failed";
3. "If I ask for counts or measurements, return the masks or outlines they come from";
4. "read and write only inside [working folder]", in the paragraph for agents that optimise the workflow.

They came from the preflight of 17 Oct 2026 and were kept out of the printed Box 1 for brevity. Earlier drafts of the prompt
are in git history.
