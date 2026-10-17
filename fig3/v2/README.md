# Figure 3 protocol v2: running and scoring the experiment

This folder contains the implementation of [Figure 3 protocol v2](../PROTOCOL_V2.md). **Read the protocol before running a scenario.** The round-1 draft is described in [../README.md](../README.md).

## Files to know

| File | Purpose |
|---|---|
| [make_protocol.py](make_protocol.py) | Generates the prompts and scenario tables from the [final Box 1 prompt](../../box1/box1_final.md). Do not edit generated prompts by hand. |
| [rows.csv](rows.csv) | Defines the model access and tools offered for each row; also used in audits and metadata. |
| [scenarios.csv](scenarios.csv) | Lists the 72 planned runs in seeded random order. |
| [answer_sheet.md](answer_sheet.md) | Approved replies to model follow-up questions. |
| [assets/](assets/) | Field-104 development images and annotations, plus the field-209 test image, prepared by `make_assets.py`. |
| [run_operator.py](run_operator.py) | Prepares, audits and records each model conversation. |
| [runner.py](runner.py) | Executes returned code on fields 104 and 209 in clean environments (rows B and C). |
| [score.py](score.py) | Scores outputs from rows B, C and D. |
| `runs/`, `runs_rejected/` | Accepted runs and rejected attempts, with reasons. |
| `runs_preflight/`, `runs_preflight_rejected/` | Preflight runs (section 11 of the protocol), not used in the figure. |
| [environment_freeze.txt](environment_freeze.txt) | `pip freeze` of the environment that runs the code. |

## Running one scenario

The commands below are for the **operator**, not the LLM being tested. Run them from the repository root. Replace `<id>` with the scenario ID.

All commands need `V2_STAGE=preflight` (runs in `runs_preflight/`, not used in the figure) or `V2_STAGE=main`, and
`SUBJECT_SCRATCHPAD` set to the operator session's scratchpad directory (it must stay empty).

1. Prepare the run: `PYTHONPATH=. python fig3/v2/run_operator.py prepare <id>`. Preparation refuses a non-empty
   operator scratchpad.
2. Start the subject: `run_operator.py start <id>`. This starts a fresh headless Claude Code session
   (`claude -p --restricted`, model `sonnet`, new session ID) in the subject folder, with only the tools in the
   `cli_tools` column of `rows.csv`, and sends `subject_message.txt`. Never use a sub-agent: it would inherit this
   repository's AGENTS.md and working directory.
3. Answer at most three follow-up questions, using only `answer_sheet.md`: `run_operator.py answer <id> "<text>"`.
   For row B, supply development files only when requested before code: `run_operator.py give_dev_files <id>` (it
   refuses once code has been given), then answer with the answer-sheet sentence. For row D, send the prescribed
   second and third turns: `run_operator.py turn <id> 2`, then `3`.
4. Audit the transcript: `run_operator.py audit <id>`. Record metadata with `run_operator.py meta <id> "<notes>"`.
   Follow the protocol's rerun rules if the audit finds a violation (`run_operator.py reject <id> "<reason>"`).
5. Save returned artefacts: `run_operator.py collect <id>`. Row B: `code_as_returned.py` (the last Python block of the
   last reply with code); any path-only edits go into `code_run.py` with `EDITS.md`, and requested packages into
   `packages.txt`. Row C: `agent_folder/`. Row D: `direct_answers.json` (fill in the turn-2 medians from the reply).
6. Execute code for rows B and C: `PYTHONPATH=. python fig3/v2/runner.py fig3/v2/<runs folder>/<id>`.
7. Score: `PYTHONPATH=. python fig3/v2/score.py fig3/v2/<runs folder>/<id>`. Row A uses the item check defined in
   protocol section 5.
8. Commit records after every ten scenarios.

Keep the field-209 annotations away from the subject model. Do not alter the generated prompts, answer sheet or scoring rules during the experiment; changes require a documented protocol revision.
