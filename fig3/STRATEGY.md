# Figure 3, round 2: strategy (draft for approval, 17 Oct 2026)

Round 1 (Box 1 v2, Claude Code sub-agents) is complete and stored in this folder. Round 2 starts from zero with the
current Box 1, run in the chat apps a reader would use. Nothing is collected until this document, the final Box 1, the
prompts, `fig3/round2/scenarios.csv`, `fig3/round2/OPERATOR.md` and the answer sheet are committed and tagged
(`fig3-round2-protocol`); those files are written once the decisions in section 8 are made. Section 9 is the adversarial audit of
the first draft; its fixes are already applied above it.

## 1. What the figure must show (from the text)
| Row | Use | "Before" | "After" (what the text recommends) | Claim it illustrates |
|---|---|---|---|---|
| a | Advice | first sentence only | Box 1 | advice from memory can be outdated and still run; asking to check the docs, scale and suitability changes the advice |
| b | Code (Python, Fiji) | first sentence only | Box 1 | code that runs is not code that works; Box 1 makes settings explicit and asks for a test, only the test shows if it works |
| c | Optimise (agent) | "run, assess, improve" | Box 1 + optimisation paragraph (annotated development half, held-out half) | without an external objective the agent judges by eye; with one, its score can be checked on held-out data |
| d | Direct answer | "How many … ?" | "Draw around every … and count them" (Box 1: request masks, not only a number) | numbers are estimated, not counted |
| all | | | | test on representative images with reference outputs |

The figure illustrates differences; it is not a benchmark. We report every run, whatever the result (section 7).

## 2. Tasks, data and scoring (unchanged from round 1)
Three tasks on one field (0.65 µm/px): **nuclei** (DAPI), **cancer cells** (brightfield), **endothelial cells**
(brightfield). References and scorers: `fig3/scoring/tasks.py` (object F1 at IoU ≥ 0.5, one-to-one).

**Development / held-out split for every row (audit fix A1).** If a model is given an annotation, it only ever gets the
**left half** (x < 512). All segmentation scores are computed on the **right half** (233 nuclei, 51 cancer cells,
181 endothelial cells), for every row and condition, so a model that saw the annotation cannot be rewarded for fitting
it, and the rows stay comparable. Counts (row d) are compared with whole-field manual counts, because the model sees
the whole field.

## 3. Prompts
- **Box 1**: the final text is frozen in `box1/box1_final.md` before collection (now: `box1_draft_v3.md` plus the edits
  in section 8, item 1). Filled in per task by `fig3/prompt_pack/make_prompts.py`; the filled text is committed.
- **Generic**: the first sentence of Box 1 only, the same for both conditions:
  - advice: "I want to count the … and measure their area from … images. Help me choose an analysis approach."
  - code: "… Help me write the analysis as a Python script." / "… as a Fiji macro."
  - optimise: "… Please run the analysis on [image], assess the result, improve the analysis and give me the result."
  - direct answer: "How many … are in this image?" / "Please draw around every … in this image and count them."
- The Box 1 condition = the generic sentence + the rest of Box 1 (+ the optimisation paragraph in row c).
- **No wrapper text** in the chat apps (round 1's harness instructions are not used). The only fixed addition, for code,
  is the file name of the attached image and "save the label image as labels.tif", identical in both conditions (A2).

## 4. Assistants, sessions and replicates
| Row | Where | Replicates | Conversations |
|---|---|---|---|
| a advice | ChatGPT (free tier) and Claude.ai (free tier) | 3 per task × condition × assistant | 36 |
| b code | same | 3 per task × condition × language × assistant | 72 |
| c optimise | Claude Code agent, sandboxed folder (as round 1); ChatGPT agent optional | 3 per task × condition | 18 |
| d direct | ChatGPT and Claude.ai | 3 per task × condition × assistant | 36 |

Every conversation: new chat, logged in, memory and personalisation off (temporary chat where available), the default
model shown by the app (recorded), web search at the app default (recorded: on/off and used/not used). Order of
conversations randomised by `prompt_pack/schedule.csv` (generated with a fixed seed), all within 3 days; the date and the
model string are recorded for each (A6).

## 4b. Execution by AI operators (proposed: ChatGPT and a Claude agent each run every scenario)
Two roles are kept strictly apart (A13):
- **Operator**: an agent that reads this repository (Claude Code here; for OpenAI, Codex or ChatGPT agent mode). It reads
  `fig3/round2/scenarios.csv` and `fig3/round2/OPERATOR.md`, opens a **fresh subject session** for each scenario, sends
  only the prompt and attachments, answers questions only from `answer_sheet.md`, runs and scores the code, and writes
  `fig3/round2/runs/<assistant>/<scenario_id>/` in the round-1 layout.
- **Subject**: the model being tested. It never sees the repository, the condition labels, the answer sheet or earlier
  results; it receives exactly what a cell biologist would type and attach. Claude subjects: fresh sub-agents with only
  the tools stated per row (as round 1). OpenAI subjects: fresh chats or API calls opened by the operator, web search
  enabled where the app enables it (recorded).
Each operator also runs the scenarios with the *other* vendor's prompt files unchanged, so prompts are identical
across vendors. A person spot-checks a random 10 % of transcripts for steering (A14). Where the subject is an API call
rather than the chat app, this is recorded and stated in the legend (A15).

## 5. Running a conversation (operator or person at the keyboard)
1. Paste the prompt file unchanged. Attach: code and direct-answer rows, the image (TIFF; if refused, the PNG preview,
   recorded). Advice row: nothing.
2. Answer follow-up questions **only from `answer_sheet.md`**, only what is asked, at most 3 replies. If the model asks
   for the image or an annotation, upload the PNG preview / the **left-half** annotation. Never hint, steer or mention errors.
3. If the app runs code itself (e.g. ChatGPT's code tool) let it, and record it; for row b we still run the final script
   ourselves (A4).
4. Save: share link, exported text (`conversation.md`), the final code unedited (`code_as_returned.*`), `meta.json`
   (date, app, model, web state, uploads, number of follow-ups, whether the app executed code).

## 6. Running and measuring
| Row | Measured (primary in bold) |
|---|---|
| a | **rubric score** (section 6.1), models/tools named (current vs removed), docs checked (cited), questions asked, length |
| b | **held-out F1**; runs unchanged (yes/no/after installing what the reply says); number of objects; the reply's own test run on the left-half annotation: what it reports vs our held-out F1 (does the test warn the user?); complexity (`complexity.py`); runtime |
| c | **held-out F1** of the frozen output; F1 the agent reports on the development half, re-scored with our scorer; files touched outside its folder |
| d | **count error** vs manual; F1 of the drawn outlines (held-out half); stated count vs number of outlines drawn |

Code is run unchanged except for input/output paths (diff stored); packages the reply asks for are installed and
recorded. Python: CPU, 1 h limit. Fiji: plain Fiji; update sites or plugins only if the reply explicitly instructs it
(recorded as an extra step, A5). Crash or no output: F1 0, drawn as ×.

### 6.1 Advice rubric (A3)
Eight yes/no items, fixed before collection: (1) names tools that exist in their current versions; (2) names no removed
model or deprecated call; (3) states versions or says to check them; (4) addresses object scale / size parameters;
(5) addresses whether a pre-trained model suits these images; (6) proposes testing against the user's annotation;
(7) proposes held-out data or similar; (8) states failure modes specific to these images. Two authors score each reply
independently from text with the prompt removed and the condition hidden; disagreements are resolved and both scores kept.

## 7. Analysis and reporting
- Per task × condition × assistant: median and every run (dots), crashes as ×, n. No statistical tests (n = 3).
- Figure: both assistants shown, marked by symbol; nothing is dropped. Supplementary table: every run (`all_runs.csv`).
- Pre-stated expectations, reported whatever happens: Box 1 code ≥ generic for nuclei and cancer cells (round 1); Fiji
  generic fails on brightfield; advice rubric higher with Box 1; agents with annotation report scores that hold on the
  held-out half; direct counts are estimates. If round 2 contradicts the text, the text changes, not the figure.

## 8. Decisions needed before collection
1. **Box 1 final text.** Proposed edits to draft v3 from the pilots: add "I use [software, version]"; "include a test I
   can run on my annotated example and tell me what result would mean it failed"; "if you can run code, work only in
   [folder]"; "if I ask for counts or measurements, return the masks or outlines they come from".
2. **Workload.** 144 chat conversations (≈ 6–8 h of copy-paste). Options to reduce: Fiji in one assistant only (−36),
   advice with 1 replicate (−24).
3. **Fiji plugins**: allow installs that the reply instructs (proposed) or plain Fiji only (round 1).
4. Who runs the conversations: AI operators (section 4b), people, or both; which OpenAI interface (Codex, ChatGPT agent mode, API) and account.

## 9. Adversarial audit of the first draft (and what was changed)
| # | Attack | Fix |
|---|---|---|
| A1 | If a model receives the annotation (it often asks), it can fit it, and scoring on the same image rewards that. Round 1 scored code on the whole field. | Only the left half is ever shared; every segmentation score is on the right half. |
| A2 | Box 1 adds information (pixel size, object size, output), not only good practice, so "after" differs in content. | Intended: Box 1 asks the user to give that information. Stated in the legend. Same file-name/output line in both conditions. An extra arm (generic + facts) is not run. |
| A3 | Advice quality is judged subjectively and could be scored to fit the story. | Fixed 8-item rubric, two blinded raters, prompt removed, both scores kept. |
| A4 | ChatGPT may execute code itself, so row b mixes "code" with "agent". | Allowed (realistic) and recorded; we still score our run of the final script. |
| A5 | Plain Fiji makes plugin-based macros fail by design. | Install what the reply explicitly instructs, record it as an extra step; decision 3. |
| A6 | Model versions drift, account memory and the order of runs bias results. | Memory off / temporary chats, randomised order, 3-day window, model string recorded. |
| A7 | Our follow-up answers can steer (round-1 pilot answer was wrong). | Answer sheet verified against the data and frozen; only questions asked are answered; every exchange stored. |
| A8 | Uploading a 16-bit TIFF may fail or be converted by the app. | Try TIFF first, fall back to PNG preview, record which. |
| A9 | Three runs and one field cannot support general claims. | Descriptive only; every run shown; scope stated in the legend. |
| A10 | Selective reporting after seeing results. | Protocol, prompts and answer sheet tagged before collection; expectations listed in section 7; every run in `all_runs.csv`. |
| A11 | Row c conditions differ in two things (objective and annotation). | Intended: the external objective *is* the annotation; stated in the legend. |
| A12 | The person running the chats knows the hypothesis. | They follow a script with no free text; the transcripts are public, so any steering is visible. |
| A13 | An operator that reads the repo passes it to the model being tested, which then knows the hypothesis and what a "good" answer is. | Operator and subject are separate sessions; subjects receive only the scenario prompt and attachments; `meta.json` records every file and message sent to the subject; the audit checks that no repository text reached a subject. |
| A14 | An AI operator answers follow-ups more helpfully in the Box 1 condition. | Answers only from the frozen answer sheet, quoted verbatim; condition hidden from the answering step where possible; 10 % human spot-check. |
| A15 | API calls or sub-agents are not the chat apps readers use (tools, system prompt, web). | Record the interface per run; prefer the app when the operator can drive it; state the difference in the legend. |
