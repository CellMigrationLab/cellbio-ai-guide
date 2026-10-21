# Figure 3 protocol v2: running and scoring the experiment

This folder contains everything that ran the Figure 3 experiment: the generated prompts, the operator tools that started and recorded each conversation, the runner that executed the returned code, the scorer, and the 72 run records. The plan it implements is [PROTOCOL_V2.md](../PROTOCOL_V2.md); read it before running a scenario.

## Files to know

| File | Purpose |
|---|---|
| [make_protocol.py](make_protocol.py) | Generates the prompts and scenario tables from the [final Box 1 prompt](../../box1/box1_final.md). Do not edit generated prompts by hand. |
| [rows.csv](rows.csv) | Defines the model access and tools offered for each row; also used in audits and metadata. |
| [scenarios.csv](scenarios.csv) | Lists the 72 planned runs in seeded random order. |
| [answer_sheet.md](answer_sheet.md) | Approved replies to model follow-up questions. |
| [assets/](assets/) | Whole-field images and annotations (rows D and scoring) and, from the revision of 19 Oct 2026, `halfdev_*` mosaics of the left halves of fields 104 and 209 for rows B and C; prepared by `make_assets.py`. |
| [run_operator.py](run_operator.py) | Prepares, runs (headless subject sessions), audits and records each model conversation. |
| [FREEZE.json](FREEZE.json) | SHA-256 of every file that defines the protocol, model ID and CLI version; `fig3/tests/test_v2_freeze.py` fails if any changes. |
| [runner.py](runner.py) | Executes returned code on fields 104 and 209 in clean environments (rows B and C). |
| [score.py](score.py) | Scores outputs from rows B, C and D. |
| `runs/` | The 72 accepted runs (prompts, replies, returned code or agent folder, execution records, scores). Rejected, superseded and preflight runs were removed on 21 Oct 2026 (git history; see `fig3/deviations.md`). |
| [check_scores.py](check_scores.py), [advice_outdated.py](advice_outdated.py) | Recompute every stored score from the run records (used by `make check`); classify the row-A replies (`advice_outdated.csv`, read by the figure). |
| [large_files.py](large_files.py) | Moves files over 50 MB out of the run records (listed in `LARGE_FILES.json`); run before committing. |
| [environment_freeze.txt](environment_freeze.txt) | `pip freeze` of the environment that runs the code. |

## Running one scenario

The commands below are for the **operator**, not the LLM being tested. Run them from the repository root. Replace `<id>` with the scenario ID.

All commands need `V2_STAGE=main` (`V2_STAGE=preflight` was used for the preflight, whose records are not kept), and
`SUBJECT_SCRATCHPAD` set to the operator session's scratchpad directory (it must stay empty).

1. Prepare the run: `PYTHONPATH=. python fig3/v2/run_operator.py prepare <id>`. Preparation refuses a non-empty
   operator scratchpad.
2. Start the subject: `run_operator.py start <id>`. This starts a fresh headless Claude Code session
   (`claude -p --restricted`, model `claude-sonnet-5-5`, new session ID; start each subject in its own process namespace, see `fig3/deviations.md`, and keep the operating session active while it runs: an idle session suspends the machine and kills the subject) in the subject folder, with only the tools in the
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
6. Execute code for rows B and C: `PYTHONPATH=. python fig3/v2/runner.py fig3/v2/runs/<id>`.
7. Score: `PYTHONPATH=. python fig3/v2/score.py fig3/v2/runs/<id>`. Row A uses the item check defined in
   protocol section 5.
8. Commit and push after every scenario, so that an interrupted session loses nothing; `run_operator.py status` lists
   complete, partial and next scenarios.

Keep every held-out annotation away from the subject model: the right halves of fields 104 and 209 given to rows B and C, and the whole field-209 annotation used for row D. Do not alter the generated prompts, answer sheet or scoring rules during the experiment; changes require a documented protocol revision.
