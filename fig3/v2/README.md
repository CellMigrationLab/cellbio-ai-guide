# Figure 3, protocol v2: harness

The protocol is `../PROTOCOL_V2.md`. This folder implements it.

| File | Role |
|---|---|
| `make_protocol.py` | writes `prompts/`, `rows.csv` and `scenarios.csv` from `box1/box1_final.md` (nothing is edited by hand) |
| `rows.csv` | per row: subject agent, tools offered, framing sentence (one table used by the framing, the audit and `meta.json`) |
| `scenarios.csv` | the 72 subject runs in their randomised order (seed in `make_protocol.py`) |
| `answer_sheet.md` | the only answers ever given to a subject's questions, including the hints |
| `assets/` | images given to subjects: field 104 image and annotation (development), field 209 image (test); `make_assets.py` |
| `run_operator.py` | prepare a scenario, add the field-104 files on request (row B before code), audit, write `meta.json`, reject |
| `runner.py` | the scripted runner (rows B and C): fields 104 and 209, clean folder, fresh venv, `execution_fF.json` |
| `score.py` | all scores (rows B, C, D) |
| `runs/`, `runs_rejected/` | one folder per scenario; rejected attempts with the reason |

## One scenario, step by step
1. `PYTHONPATH=. python fig3/v2/run_operator.py prepare <id>` (refuses if the harness scratchpad is not empty).
2. Start a **fresh** sub-agent of the type named in `rows.csv` (`subject-chat` = Read and web only, no shell;
   `general-purpose` for row C), from the subject folder, with exactly `subject_message.txt`.
3. Answer follow-up questions only from `answer_sheet.md` (at most 3 replies). Row B, image or annotation asked
   **before** any code: `run_operator.py give_dev_files <id>` and the answer-sheet sentence. Row D: send turns 2 and 3
   (`prompts/direct_turn2_*`, `direct_turn3_*`) after each reply.
4. `run_operator.py audit <id> <agent_id>` (all tool calls; flags = rerun under the rerun policy) and
   `run_operator.py meta <id> <agent_id> "<notes>"`.
5. Row B: save the final script as `code_as_returned.py` (paths edited only, if needed, in `code_run.py` + `EDITS.md`);
   packages the reply asks for in `packages.txt`. Row C: copy the agent's folder to `agent_folder/`.
   Row D: write `direct_answers.json` from the conversation.
6. Rows B, C: `PYTHONPATH=. python fig3/v2/runner.py fig3/v2/runs/<id>` (fields 104 and 209).
7. `PYTHONPATH=. python fig3/v2/score.py fig3/v2/runs/<id>`. Row A: the item check (protocol section 5).
8. Commit after every 10 scenarios.
