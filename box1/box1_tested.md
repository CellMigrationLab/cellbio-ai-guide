# Box 1 as tested in Figure 3 (the "detailed" prompts)

This is the Box 1 template that the "detailed" prompts of Figure 3 were built from (protocol v2): the Box 1 of the article
plus four additions from the pilots, written out in full here without the editing marks of `box1_final.md`. The slots in
square brackets were filled in per task and row; the filled-in prompts are in `fig3/v2/prompts/` (`advice_box1_*`,
`code_box1_*`, `optimise_*`). The additions and where they appear:

| Addition | Advice | Code | Agent, by eye | Agent, scored |
|---|---|---|---|---|
| "I use [software and version] on [hardware]" | yes | yes | yes | yes |
| "Include a test I can run on my annotated example and tell me what result would mean that the analysis failed" | yes | yes | no (no annotation is given) | yes |
| "If I ask for counts or measurements, return the masks or outlines they come from" | yes | yes | yes | yes |
| "read and write only inside [working folder]" (optimisation paragraph) | no | no | yes | yes |

```text
I want to [biological question or measurement] from [type of microscopy images]. Help me [choose an analysis approach / write the analysis / run or optimise the workflow].
My images are [2D/3D/time series], with axes [e.g. T, Z, C, Y, X], channels [channels], data type [dtype], pixel/voxel size [X µm], and objects of interest approximately [X–Y µm] in size. I use [software and version] on [hardware]. The output I need is [measurement/output]. I can provide [representative images/annotations/reference measurements / expected outputs].
Please:

* Clarify the task. Ask for missing information only when it could materially affect the analysis. If useful, ask me for representative images or examples of the expected result.
* Use appropriate methods. Prefer established, maintained software and documented APIs. Check current documentation rather than relying only on memory. If consequential behaviour remains unclear, inspect the source code when available rather than guessing.
* Check deep learning model suitability. If using a pre-trained model, consider whether my images match its training data, including image type, channels, dimensionality, object scale, preprocessing and post-processing.
* Write code according to best practices. Keep functions small and focused, use clear names and annotations, and separate consequential processing steps. Validate inputs, provide informative errors and do not use silent fallbacks.
* Make processing explicit. State important parameters, defaults and transformations, including resizing, resampling, normalisation, channel selection and post-processing. Preserve the original coordinate system and physical units unless a transformation is explicitly required and documented.
* Make the analysis testable. Test it on representative reference data where possible, save useful intermediate outputs and overlays, and use validation measures appropriate to the intended biological measurement rather than relying on a single generic score. Include a test I can run on my annotated example and tell me what result would mean that the analysis failed. If I ask for counts or measurements, return the masks or outlines they come from.
* Audit and challenge the result. Before finishing, assume that the analysis could be scientifically wrong even if the code runs and the output looks plausible. Identify the failure modes most likely to change the biological conclusion and suggest concrete tests or reference data that would expose them.

If you are allowed to optimise the workflow: optimise only on [development data], do not access [held-out data] until the workflow is fixed, keep raw images read-only, read and write only inside [working folder], and record consequential changes to the analysis. When optimising a deep learning model, choose suitable pre-processing, image scale and post-processing steps.
```
