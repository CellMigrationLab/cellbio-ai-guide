# Operator instructions for Figure 3, round 2

You are the **operator**: you run scenarios on a **subject** model and record what happens. Read `fig3/STRATEGY.md`
first. These rules exist so that the results can be audited; if you cannot follow one, stop and record why in
`deviations.md` rather than improvising.

## 1. Isolation (the most important rule)
- The subject must never see this repository, this file, the strategy, the answer sheet, the condition names
  ("generic", "box1"), other scenarios or any result. Send it **only** the prompt file text and the listed attachment.
- Open a **new** subject session for every scenario (new chat / new sub-agent / new API conversation). Memory,
  personalisation and custom instructions off; temporary chat where available.
- If the interface needs a fixed framing (sub-agents, API), use exactly the text in section 6, identical for every scenario.
- Record in `meta.json` every message and file you sent to the subject.

## 2. Order and identity
Run scenarios in `scenarios.csv` order (`run_order`), for your `assistant` only (`claude` or `openai`). One folder per
scenario: `fig3/round2/runs/<scenario_id>/`. Record the model string shown by the interface, the interface (app, agent
mode, API, sub-agent), the date and time, and whether web search was available and used.

## 3. Per row
**advice** — send the prompt; no attachment. Save the conversation. Nothing is run.

**code_python / code_fiji** — attach a copy of `assets/<task>_image.tif` named `image.tif` (the prompt refers to
this name; if refused, `<task>_image.png` named `image.png`, and record it). When the
conversation ends:
1. Save the final code exactly as returned (`code_as_returned.py` / `.ijm`).
2. Copy it to `code_run.*`, changing **only** input/output paths so it reads `image.tif` (a copy of
   `assets/<task>_image.tif`) and writes `labels.tif`; save the diff as `EDITS.md`. Install packages the reply asks
   for (record versions). Python: CPU, 1 h limit. Fiji: plain Fiji; install update sites/plugins only if the reply
   explicitly says so (record). Save stdout/stderr as `run.log`.
3. If the reply includes a test against an annotated example, run it as instructed with `assets/<task>_annotation_left.tif`
   (and the left half of the image if it needs a matching image); save its output as `test_output.txt`.
4. If the app executed code itself (e.g. ChatGPT's code tool), record it; still do steps 1–3.

**optimise** (Claude Code; ChatGPT agent optional) — create a fresh folder containing only the files in `agent_folder`
(generic: `image.tif`; box1: `image_left.tif`, `annotation_left.tif`). Give the subject shell access to that folder only.
When it finishes, save its whole folder (`agent_folder/`) and a list of any file it touched outside it. Then run its
`pipeline.py` unchanged on the whole field (`assets/<task>_image.tif`) → `labels.tif` (generic runs: use its own
`labels.tif` if `pipeline.py` fails, and record it). The right half is the held-out test.

**direct** — attach `assets/<task>_image.png`. Generic: write the number it gives in `stated_count.txt` (if it gives a
range, the midpoint; record the text). Box1: save its JSON as `reply.json` (if it does not give JSON, record that; no
outlines = F1 0).

## 4. Follow-up questions
Answer only what is asked, quoting `answer_sheet.md` verbatim. At most 3 replies; then say "Thanks, that is all I need."
If the model asks for the image or an annotation, upload the file named in the answer sheet (left half only).
Never steer, hint, praise, correct or report errors. Do not ask for revisions.

## 5. After each scenario
Write `meta.json`:
```json
{"scenario_id": "", "assistant": "", "row": "", "condition": "", "task": "", "replicate": 1,
 "interface": "", "model": "", "datetime_start": "", "datetime_end": "", "web_available": true, "web_used": [],
 "app_executed_code": false, "attachments_sent": [], "messages_sent": [], "follow_ups": 0,
 "packages_installed": [], "notes": ""}
```
Save `conversation.md` (every turn verbatim, with the share link if any). Then run
`PYTHONPATH=. python fig3/round2/score_round2.py fig3/round2/runs/<scenario_id>` (not for advice).
Commit after every 10 scenarios with the message `round2: <assistant> scenarios <from>-<to>`.

## 6. Fixed framing for sub-agent or API subjects
Use this text, and nothing else, before the prompt (fill the bracket from `subject_tools`):
```text
You are an AI assistant chatting with a user. [Tools: web search is available (WebSearch and WebFetch; load them with ToolSearch if they are not listed). | The user attached a file, which you can view: <path>. | You can run shell commands in the folder <path> only.] Reply to the user as you normally would.
```

## 7. Spot-check and audit
A person reads a random 10 % of transcripts (`python -c "import csv,random; r=[x['scenario_id'] for x in csv.DictReader(open('fig3/round2/scenarios.csv'))]; print(sorted(random.Random(20261017).sample(r, len(r)//10)))"`) and checks that only the prompt, answer-sheet
quotes and listed files reached the subject. Any problem goes in `deviations.md` and the scenario is rerun.
