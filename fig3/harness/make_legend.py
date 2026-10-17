"""Write the Figure 3 legend with every number taken from fig_scores.json (missing runs shown as '…')."""
import json, statistics
S = json.load(open('fig_scores.json')); T = S['tasks']
NAME = {'nuclei': 'nuclei', 'cancer': 'cancer cells', 'endo': 'endothelial cells'}


def f(v):
    vals = [0 if x == -1 else x for x in v if x is not None]
    if not vals: return '…'
    s = f'{statistics.median(vals):.2f}'
    if len(vals) > 1: s += f' ({min(vals):.2f}–{max(vals):.2f})'
    if len(vals) < len(v): s += f' [{len(vals)}/{len(v)} runs]'
    if -1 in v: s += f', {v.count(-1)} macro crashed'
    return s


def pair(cond):
    return '; '.join(f'{NAME[t]} {f(T[t][cond]["before"])} → {f(T[t][cond]["after"])}' for t in T)


def ag(t):
    a = T[t]['agent']; rep = a['dev_reported']
    one = lambda v: '…' if v[0] is None else f'{v[0]:.2f}'
    s = f'{NAME[t]} {one(a["before"])} → {one(a["after"])}'
    if rep is not None: s += f' (reported on the development half: {rep + 1e-9:.2f})'
    return s


def dr(t):
    d = T[t]['draw']
    return (f'{NAME[t]}: stated counts {", ".join(map(str, d["asked"]))} vs manual {d["manual"][0]}'
            f'{"–" + str(d["manual"][1]) if d["manual"][1] != d["manual"][0] else ""}; '
            f'outlines drawn {", ".join(str(x) for x in d["drawn"])}, F1 {f(d["f1"])}')


L = f"""**Figure 3 | Using a large language model (LLM) for image analysis: what changes when the request changes.**
Top, the three tasks, from easy to hard, all on one field of view (1024 × 1022 px, 0.65 µm per pixel) of an endothelial monolayer with cancer cells on top: segment the endothelial nuclei in the DAPI image (manual annotation, n = {S['manual']['nuclei']}), the cancer cells in the brightfield image (n = {S['manual']['cancer']}) and the endothelial cells in the same brightfield image (n = {S['manual']['endo']} complete cells, drawn from the PECAM-1 image; a second annotator agreed with F1 0.90). Right of each image, the manual annotation (desired result).
Rows a–d are ordered from the least to the most analysis delegated to the LLM (left arrow); each row compares a common request (before) with the request recommended in the text and Box 1 (after). Prompts are shortened; full prompts, verbatim replies, code and outputs are in the source data. All replies are from Claude Sonnet (the model available on the free tier), run as Claude Code sub-agents with the tool access stated per row, 16–17 October 2026, three independent conversations per condition unless stated. Scores are object-level F1 against the manual annotation (IoU ≥ 0.5, one-to-one matching; as in Figs. 1 and 2): bar, median; circles, individual runs; ×, code that crashed or wrote no output (scored 0); n, number of objects returned (median); dashed grey line, Cellpose-SAM with default settings. For nuclei, predicted objects lying mostly on cancer cells are ignored (cancer-cell nuclei are not annotated); for endothelial cells, objects touching the image border are removed from both annotation and prediction.
**a**, Advice without code. Asked which tool, model and settings to use, the LLM answering from memory recommended models (`cyto3`, the denoising models) that are no longer part of Cellpose 4; asked to check the current documentation first, it named the current model (`cpsam`). Caveat: the outdated advice still runs: `CellposeModel(pretrained_model='cyto3')` in Cellpose 4.2.1.1 loads the default model without any warning, so the user cannot tell that the advice was wrong.
**b**, Code. The LLM could view a preview of the image but could not run code; we ran every script or macro unchanged except for input and output paths. Generic request ("Please write a Fiji macro / Python script to segment the … in my image") versus the Box 1 code-generation prompt (with the LLM allowed to search the web for documentation; pixel size and object size filled in; we added one line giving the software available). Fiji (b1): {pair('fj')}. Python (b2): {pair('py')}. Caveat: whether the code runs says nothing about whether it is correct; the Box 1 prompt makes the settings explicit and asks for a test against annotation, and only that test shows whether they work.
**c**, Agent. An agent able to run code in a sandboxed folder was asked to run, assess and improve the analysis (before), or to build and optimise a pipeline scored against the user's annotation of the left half of the image, with the right half held out (after). Its final pipeline was then run unchanged on the held-out half. Both conditions are scored on the held-out half (n = {S['manual_half'].get('nuclei', '…')} nuclei, {S['manual_half'].get('cancer', '…')} cancer cells, {S['manual_half'].get('endo', '…')} endothelial cells): {'; '.join(ag(t) for t in T)}. Caveat: without an objective, the agent judged its own result by eye and had no score that could be checked (it called the nuclei result 'good, not perfect', with errors of 'a few percent'; for the cancer cells it estimated about 5 false positives and 4 missed cells, measured 17 and 8); with the annotation as objective, the score it reported on the development half held on the held-out half (reported → held-out, grey text). Two of the six agent runs wrote files outside the folder they were told to use, and a third copied files outside it and deleted the copies.
**d**, Direct answer. In new conversations, the LLM was shown the image and asked for the number of objects (orange) or to draw around every object and count them (purple squares, number of outlines it drew). {'. '.join(dr(t) for t in T)}. For endothelial cells, the drawn 'outlines' were a placeholder grid, as one reply stated. Caveat: the numbers were estimated, not counted, and did not match the outlines the same model drew.
Bottom, what to keep, at any level of delegation: test on representative images with reference outputs. One field of view and three runs per condition: the scores illustrate the differences between uses and are not a benchmark of LLMs.
"""
open('../../figure3/figure3_legend.md', 'w').write(L)
print(L)
