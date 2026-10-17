# Adversarial re-audit of Figure 3 round 2

**Date:** 17 October 2026  
**Repository revision reviewed:** `main` at `1464a4823a31c327c3ffdc54224ce8f508370fb9`  
**Status at review:** three accepted Claude-side scenarios are present, with rejected attempts retained separately.

## Executive verdict

The plan is substantially stronger than the first audited version. The most important earlier defects were addressed: field 104 is now development data and field 209 is a genuinely separate test field; both optimisation conditions receive the same development image; scoring is performed on the whole test field; malformed outputs are recorded rather than guessed; the Figure 1 producer paths and raw-to-figure checks were improved; and protocol inputs are hash-recorded.

However, I recommend **pausing the full round now**. The first three accepted scenarios should be treated as a pilot and rerun after one final protocol freeze. The present operator/harness behaviour changed after the recorded freeze, and several remaining issues could invalidate a long, expensive run or weaken the paper's central narrative.

The most important unresolved point is conceptual: the experiment asks whether an LLM-assisted workflow produces the requested biological measurement, but the current code/agent rows primarily score segmentation F1. They do not yet verify the requested area measurements, physical units, or consistency between the reported table and the label image. A workflow could therefore score well while answering the user's actual measurement request incorrectly.

---

## What is now solid

1. **Separate development and test fields.** Field 104 is used for development; field 209 is never annotated for the subject and is used for final evaluation. This is much stronger than the former within-field split.
2. **Whole-field scoring.** The split-boundary problem is removed.
3. **Manual counts are derived from annotations.** They are no longer hard-coded in the round-2 scorer.
4. **Malformed outputs are explicit.** Missing files, invalid JSON, invalid counts and wrong shapes are recorded as statuses.
5. **All runs and rejected attempts are retained.** This is essential for an auditable LLM study.
6. **Prompts, assets and scorers are hashed.** The freeze manifest and test are useful, even though their scope must be expanded.
7. **The strategy avoids inferential statistics with n = 3.** Showing every run is the correct choice.
8. **The plan states that generic versus Box 1 compares complete requests, not isolated prompt components.** This interpretation must remain prominent.

---

## P0: resolve before continuing the full round

### P0.1 Treat the current runs as a pilot and re-freeze before restarting

The protocol was recorded as frozen at commit `725e484…`, but material execution rules changed afterwards:

- `run_operator.py` was added after the freeze;
- code-row subjects were subsequently allowed to execute shell commands;
- scratchpad handling was changed;
- the model environment was repaired after a torchvision/torch mismatch;
- the current accepted runs were produced under these post-freeze conventions.

These are not cosmetic changes. They affect what the subject can do and whether conditions are comparable. The clean solution is to call the existing accepted and rejected scenarios a **pilot**, resolve the items below, create a new protocol hash manifest/tag, and restart run order from zero. With only three accepted scenarios, this is inexpensive relative to carrying a compromised design through 162 scenarios.

### P0.2 Freeze the actual execution protocol, not only prompts and scorers

`protocol_freeze.csv` does not include several files that materially define the experiment, especially:

- `fig3/round2/run_operator.py`;
- `fig3/STRATEGY.md`;
- the environment requirements and Fiji setup;
- the rerun/rejection policy;
- the advice-rating guide;
- the exact final-figure plan.

`run_operator.py` currently grants code rows shell access even though `scenarios.csv` still describes those rows as `web; view attachment`. Thus the frozen scenario table and the actual harness disagree.

Expand the freeze to include the full operator and environment. Add a test that the tools offered in `scenarios.csv`, the framing in `run_operator.py`, and the operator instructions agree exactly.

### P0.3 Decide whether the code row is code generation or agentic execution

The manuscript distinguishes:

1. asking for code that the researcher runs; and
2. allowing an agent to execute and optimise the workflow.

The current Claude code-row subjects are given shell access and can inspect the image, prototype algorithms and iterate. One accepted Fiji-code subject prototyped repeatedly in Python before returning a macro. This blurs rows b and c and differs from `scenarios.csv`.

**Preferred design:** code-row subjects may inspect the attached image and return code, but do not execute or optimise it. The operator runs the final code once. Row c remains the autonomous execution/optimisation condition.

If execution is retained for realism, rename row b to **LLM-assisted coding**, state that some interfaces executed code, and do not present it as pure code generation. Use the same execution entitlement for every assistant/interface in that row.

### P0.4 Enforce isolation rather than auditing it afterwards

The current Claude sub-agent isolation is checked after the run, not enforced. Subjects can in principle access the repository, test annotations or previous runs. Relative paths and shell commands can also evade simple string-based path checks. The shared harness scratchpad is outside the subject folder and has already required special handling.

For the final round, run subjects in a container or restricted filesystem containing only the scenario files. Use a unique temporary directory/scratch space inside that sandbox. The test-field annotations and repository must not be mounted. A post-hoc tool-call audit should remain, but it should not be the primary barrier against leakage.

### P0.5 Test frozen agent pipelines in a clean runtime package

For optimisation runs, `run_operator.py` copies the complete agent folder to the test execution directory. That folder may contain the development image, manual annotation, cached labels and other development artefacts. A pipeline could therefore consult development data at test time.

After optimisation, test the frozen pipeline from a clean directory containing only:

- the test image;
- `pipeline.py`;
- explicitly declared runtime dependencies such as trained weights/configuration.

Do not copy the development image or annotation. Require a `runtime_manifest.json` or construct an operator allowlist. Record every file read during the test run where feasible. A pipeline that requires the development annotation at inference should fail the deployability test.

### P0.6 Score the requested measurement, not only the segmentation

Every code/agent prompt asks for counts and areas in µm², but the primary automated score uses only `labels.tif`. Add measurement-level checks:

- label image exists, is 2D, finite, non-negative and integer-valued;
- reported object count agrees with the label image;
- `areas.csv` or equivalent exists when requested;
- one row is present per labelled object;
- areas agree with label-pixel areas multiplied by the stated pixel area, within a pre-specified tolerance;
- units are explicitly µm²;
- summary count and area statistics are compared with the manual reference.

Retain object F1, but make **measurement correctness** a co-primary or central secondary outcome. This directly tests the paper's argument that correct-looking code is not enough.

The scorer currently casts predictions to integers. Reject non-integer/probability images explicitly rather than silently truncating them.

### P0.7 Redesign the direct-answer row before running it at scale

The current inspectable-output prompt requests polygons for every object in a 1024 × 1022 field containing up to 473 nuclei. This can exceed response-token limits and tests JSON-output capacity as much as visual counting. Models also see a resized/rendered PNG but are asked for original-pixel polygons.

Use a pre-specified, representative crop with a manageable number of objects for both conditions, or request object centres rather than full polygons. For a counting claim, centres are sufficient and can be matched one-to-one to manual objects. If masks/outlines are essential, use a smaller crop and freeze its selection rule before collection.

Rename the internal/public condition from `box1` to **inspectable output** in this row. It is not the full Box 1 prompt; it tests `count only` versus `locations/outlines plus count`.

### P0.8 Ensure every target is observable from the supplied image

Two tasks risk testing missing information rather than LLM quality:

- endothelial nuclei are scored excluding cancer-cell nuclei, but the model receives DAPI alone and cannot necessarily know which nuclei belong to cancer cells;
- endothelial-cell boundaries are scored from PECAM-1 junction annotations while the model receives brightfield, including regions hidden by overlying cancer cells.

A target that is not visible in the input contradicts the paper's own advice to define a measurable quantity. Preferred fixes:

- provide the channels needed to define the target; or
- use all visible nuclei as the nuclei target; or
- use PECAM-1 for the endothelial-cell task; or
- remove the affected task from rows where the target cannot be inferred.

Do not rely on hidden scoring masks to make an intrinsically unobservable task appear valid.

### P0.9 Use an isolated software environment for every scenario

Package installations or Fiji update sites can persist and affect later runs. The recent torchvision mismatch shows that the environment was not fully preflighted.

Before restarting:

- run a fixed smoke test for Python, Cellpose, torchvision and Fiji;
- freeze the base environment;
- use a fresh virtual environment/container per scenario, or an immutable base plus a per-run overlay;
- use a pristine Fiji copy/profile per scenario when plugins or update sites are installed;
- record exact package/plugin versions and installation failures.

Pre-specify which failures are operator/environment faults eligible for rerun and which are model failures that remain F1 = 0.

### P0.10 Allow the advice model to receive the image/reference when it asks

The article and Box 1 recommend asking for representative images. In the first accepted advice run, the subject asked for the file but received `I don't know`; the answer also referred to a PNG preview despite no image being attached. This penalises the behaviour the paper recommends.

For advice rows, either:

- provide the development image and annotation when requested in both conditions; or
- explicitly define the task as metadata-only advice and remove image-request behaviour from the rubric.

The former is more faithful to the paper.

### P0.11 Freeze an objective rerun/rejection policy

Define before restarting:

- rerun: operator error, corrupted attachment, unavailable runner, verified shared-environment defect, or subject access to forbidden data;
- do not rerun: invalid code, nonexistent API/package suggested by the model, crash caused by returned code, malformed output, refusal or timeout;
- all attempts remain archived;
- the rerun decision is made without considering whether the outcome is favourable.

The distinction between a broken shared torchvision installation and a model requesting an invalid dependency must be explicit.

---

## P1: strengthen interpretation and reduce avoidable reviewer attacks

### P1.1 The advice rubric is partly tautological

Several rubric items restate instructions contained in Box 1, so a higher Box 1 score primarily demonstrates instruction following. Describe the outcome as **adherence to the paper's recommended safeguards**, not overall advice quality.

Before rating, freeze a task-specific scoring manual with examples. Also report factual-error rate, nonexistent/deprecated APIs, evidence of documentation use, and inter-rater agreement. Add physical units/output definition to the rubric if those are central to the manuscript.

### P1.2 Validate the field-209 references and report a human ceiling

Field 209 has one reference for cancer cells and nuclei, and two endothelial junction annotations with notably different object counts. Compute and report human-human agreement for field 209. Consider scoring endothelial outputs against both annotators or a consensus; at minimum show the human-human F1 as context.

Record annotator, tool, date and whether annotation was performed blind to the model outputs.

### P1.3 Freeze the exact Figure 3 display before seeing the results

The current plan specifies that every run is shown, but not the exact main-figure layout. With 162 scenarios, outcome-dependent panel selection would be easy and the final figure could become unreadable.

Before continuing, commit a schematic that specifies:

- which outcome appears in each row;
- which task/assistant/language groupings are shown in the main figure;
- how crashes, refusals and malformed outputs appear;
- what moves to the supplementary table;
- whether assistants/interfaces are separated rather than pooled.

Do not aggregate across assistants or interfaces unless the display is clearly descriptive.

### P1.4 Chat app, API and sub-agent runs are different experimental conditions

The current Claude runs use Claude Code sub-agents, not claude.ai. System prompts, tools and execution behaviour differ. Show interface/model explicitly and do not combine these runs as if they were interchangeable. If the paper claims to represent ordinary cell-biologist use, actual chat-app runs should be primary.

### P1.5 Clean up stale protocol documentation

Several files still describe the superseded design:

- `AGENTS.md` refers to optimisation tested on a held-out half;
- `fig3/round2/README.md` says runs have not started;
- `STRATEGY.md` still contains at least one reference to left-half assets;
- legacy held-out-half tests remain in `fig3/tests/test_round2.py`.

Update or clearly label legacy material before release. Stale text in an audit repository is itself a reproducibility risk.

### P1.6 Fix metadata generation

`run_operator.py` currently initializes some metadata fields rather than deriving them robustly. Ensure `app_executed_code`, packages installed, plugin installations, tool use and environment changes are generated from the transcript/run logs or explicitly entered and validated. Add a run-completeness validator that checks required files and metadata for every row.

### P1.7 Range answers should not be reduced only to a midpoint

For direct counts, preserve the original range, report whether the manual count falls within it, and use midpoint error only as a secondary summary. Do not discard uncertainty expressed by the model.

---

## Is 162 scenarios justified?

The full design is defensible only after the P0 items are fixed, but it is large for a short Comment and may look like a benchmark despite using two fields from one experiment. The main risk is not insufficient repetitions; it is spending substantial effort on a design that conflates interfaces, evaluates unobservable targets or fails to score the requested measurement.

Recommended sequence:

1. Treat the existing three accepted scenarios and rejected attempts as pilot data only.
2. Implement the P0 fixes.
3. Run a **preflight set** covering every row, condition, task type and execution environment (roughly 12–24 scenarios). Use it only to test the harness/output feasibility, not in the final results.
4. Freeze protocol v2, environment and figure layout.
5. Run the final round from zero.

If workload must be reduced, prioritise the rows that directly support the manuscript's novel guidance: code generation, autonomous optimisation and direct inspectable answers. The advice row provides the weakest causal evidence because its rubric largely tests whether the model repeats instructions in Box 1. Fiji is valuable for the audience, but it can be moved to the supplement or restricted to one representative task if necessary.

## Go/no-go recommendation

**No-go for continuing the 162-scenario collection under the current harness.** The development/test-field revision is excellent, but the operator freeze, row separation, runtime isolation, direct-answer format and measurement-level scoring should be corrected first. Because only three accepted scenarios have been collected, restarting now is the lowest-cost and most defensible choice.
