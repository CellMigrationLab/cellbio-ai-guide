# Figure 3 pilot runs with Box 1 draft v3

These runs, made on 17 October 2026, were exploratory and are **not included in the figure**. They tested Box 1 draft v3 (the exact text is in each run's prompt; the draft file was removed), with task-specific prompts assembled by [make_prompts.py](make_prompts.py).

- `runs/advice_{generic,box1}v3_*`: advice requests; the generic condition used only the first sentence.
- `runs/code_box1v3_*`: code-generation requests. Initial scripts are stored in `artifacts/`; revised scripts, after the model asked follow-up questions, are recorded in `conversation.md`.

Answers to follow-up questions came only from [answer_sheet_pilot.md](answer_sheet_pilot.md). The full exchanges are retained in each `conversation.md`. Scores had not been added when this README was written.

An earlier plan to run these prompts in chat apps was dropped. The current design is [protocol v2](../PROTOCOL_V2.md).
