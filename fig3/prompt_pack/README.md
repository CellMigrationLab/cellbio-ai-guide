# Figure 3 prompt pack: generic request vs Box 1, across chat assistants

Purpose: show what changes when a cell biologist uses the Box 1 prompt instead of a one-line request,
for advice and for code, on three tasks of increasing difficulty (one field, manual annotation available).
Illustration, not a benchmark.

## Design
| Factor | Levels |
|---|---|
| Task | nuclei (DAPI), cancer cells (brightfield), endothelial cells (brightfield) |
| Use | advice ("Help me choose an analysis approach") · code ("Help me write the analysis") |
| Prompt | generic = the first sentence only · Box 1 = first sentence + full Box 1 (filled in) |
| Assistant | ChatGPT (free tier) · Claude (claude.ai, free tier) |
| Replicates | advice: 1 conversation per cell · code: 3 conversations per cell |

Total: 2 assistants × 3 tasks × 2 prompts × (1 advice + 3 code) = 48 conversations.
Row c (agent) is run in Claude Code as before (sandboxed folder, generic "run, assess, improve" vs
Box 1 + its optimisation paragraph, development half / held-out half).

## Protocol for each conversation
1. New conversation, logged in, memory/personalisation OFF, default model of the free tier (write the model name
   shown in the app), web search left at the app default (record whether it was on and whether it was used).
2. Paste the prompt file **unchanged**. Code prompts: attach the image (`data/raw/field104_dapi.tif` for nuclei, `data/raw/field104_brightfield.tif` for cancer and endothelial cells;
   if the app refuses TIFF, attach the PNG preview and say so in meta.json). Advice prompts: no attachment.
3. Follow-up questions: answer **only what is asked**, using `answer_sheet.md`, wording as close as possible.
   If it asks for the image or the annotation, upload the PNG from `assets/`. At most 3 user replies; then stop.
4. Do not ask for changes and do not mention errors. (Optional, separate column: if the code crashes, paste the
   traceback once and score the corrected code as "after one debug round".)
5. Save: the whole conversation (share link + exported text) as `runs/<assistant>_<use>_<prompt>_<task>_r<k>/conversation.md`,
   the final code (as given, unedited) as `code.py`, and `meta.json` (date, app, model, web on/used, attachments, n follow-ups).

## What we measure
- Advice: tools/models named (current vs removed/outdated), whether docs were checked, whether scale, model
  suitability, validation on the annotation and held-out data are raised, questions asked, length.
- Code: runs unchanged? (we only set input/output paths and install the packages it asks for, recorded);
  F1 vs manual annotation (IoU ≥ 0.5, same scorers as Figs 1–3); object count; complexity
  (`complexity.py`: lines, functions, branches, named parameters, dependencies, raise statements); runtime.

## Files
- `prompts/` 12 prompt files (exact text to paste).
- `assets/` PNG previews of the images and annotations (upload only if asked); raw TIFFs are in `data/raw/`.
- `answer_sheet.md` fixed answers for follow-up questions.
- `complexity.py` code metrics.  `runs/` one folder per conversation.
