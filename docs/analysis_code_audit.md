# Adversarial audit of the analysis and scoring code

**Date:** 17 October 2026  
**Repository revision reviewed:** `main` at `1464a4823a31c327c3ffdc54224ce8f508370fb9`  
**Scope:** active code that produces, transforms or scores data used by Figures 1–3, the Figure 3 round-2 protocol/scorer/operator, shared scientific helpers, and non-archived exploratory scripts that can overwrite active outputs. SVG layout-only builders, verbatim recovered shell commands, superseded builders and LLM-returned scripts were not reinterpreted as maintained analysis code.

## Executive verdict

The repository has improved substantially: canonical Figure 1 output paths are now shared, object matching is mostly centralized, pix2pix alignment has a checked reader, endothelial junction conversion has a shared implementation, and a raw-to-derived Figure 1–2 check exists.

It is **not yet correct or consistent enough to claim that all analysis code is fail-fast and uses one scientific implementation everywhere**. The main blockers are:

1. invalid label images are repeatedly converted with `astype(int)`, so probabilities, NaNs, negative values or non-integer outputs can be silently reinterpreted as instance labels;
2. the Figure 3 execution harness can score an output written by a script that exited non-zero or timed out;
3. the Figure 3 scorer does not yet verify the requested count/area table or physical units;
4. `cellpose_perturb.py` has an actual stale-value fallback for an unknown run name;
5. the super-resolution tubule-width sampling is orientation-biased and silently excludes failed measurements;
6. active exploratory Figure 1 scripts still duplicate scientific logic and can overwrite canonical source data;
7. several required inputs/keys are converted into blank/`None` results rather than explicit failures;
8. statistical and display helpers do not consistently reject empty, constant or non-finite inputs.

The current Figure 3 collection should remain paused. Fix the P0 items, run a dedicated preflight, freeze the complete execution/scoring code, and restart the final round from zero.

---

## Code inventory reviewed

### Shared scientific code

- `common/matching.py`
- `common/annotations.py`
- `common/pix2pix.py`
- `common/paths.py`

### Figure 1 active analysis path

- `fig1/code/segment_bf_cellpose.py`
- `fig1/code/classical_seg.py`
- `fig1/code/f1_scores.py`
- `fig1/code/export_rep_window.py`
- `fig1/code/export_fresh_field.py`
- `fig1/code/segment_panelA.py`
- `fig1/code/export_splits.py`
- `fig1/code/find_rep_window.py`

The following non-archived exploratory files were also checked because they duplicate scientific logic or write into active `source_data`: `compare_models_A.py`, `compare_cancer_gt.py`, `compare_nuclei_gt.py`, `compare_annotations.py` and `agent_run.py`.

### Figure 2 active analysis path

- `norm_inputs.py`
- `cellpose_perturb.py`
- `postfilter.py`
- `errors.py`
- `score_perturb.py`
- `export_window.py`
- `export_errors_window.py`
- `annot_agree.py`
- `bio_result.py`
- `al_roi.py`
- `al_gray.py`
- `al_intensity.py`
- `image_generation.py`
- `tubule_width.py`
- `squirrel_run.py`
- `squirrel_tile.py`
- exploratory `fig2/analysis/care_linearity.py`

### Figure 3 active scoring/execution path

- `fig3/scoring/tasks.py`
- `fig3/scoring/build_scores.py`
- `fig3/scoring/rescore_dev.py`
- `fig3/scoring/all_runs_table.py`
- `fig3/round2/make_assets.py`
- `fig3/round2/make_scenarios.py`
- `fig3/round2/run_operator.py`
- `fig3/round2/score_round2.py`
- `fig3/direct_answers/code/rasterise_poly.py` because its rasterized labels feed the current round-1 figure

---

# P0 — must fix before continuing Figure 3 or finalizing the figures

## P0.1 Strict label validation is missing throughout the scoring path

### Evidence

- `common/matching.match()` accepts any NumPy array. `NaN > 0` and negative values become background; floating labels are treated as object identifiers.
- `fig3/scoring/tasks.score()` uses `np.squeeze(pred).astype(int)`.
- `fig3/scoring/rescore_dev.py`, `fig1/code/f1_scores.py`, `fig2/code/errors.py`, `score_perturb.py`, `bio_result.py` and several exporters also cast labels with `astype(int)`.

This can silently turn a probability map into labels 0/1, truncate non-integer values, hide NaNs as background, or accept disconnected regions carrying one label as one object.

### Required fix

Add one shared strict implementation, for example `common/labels.py`:

- `validate_label_image(array, *, expected_shape=None, name="...")`
- require exactly two dimensions after an explicitly controlled squeeze;
- require numeric, finite, non-negative, integer-valued data;
- reject values outside the target output dtype rather than wrapping on cast;
- optionally require each positive label to be one connected component for instance-segmentation scores;
- return a validated integer array without changing the scientific meaning.

Use it at every scoring boundary and when reading manual/model label images. Do not put a silent cast inside `common.matching` and assume that makes the input valid.

### Regression tests

Float probability map; fractional labels; NaN/Inf; negative labels; 3D stack; wrong shape; disconnected duplicate label; `uint32` label beyond `uint16`; a normal sparse label image.

## P0.2 A failed or timed-out workflow can still be scored as successful

### Evidence

`fig3/round2/run_operator.py::run()` records the subprocess exit code or timeout in `run.log`, but then copies `labels.tif` whenever that path exists. `score_round2.py` only checks whether `labels.tif` exists and has the expected shape. A script that writes a partial output and then exits non-zero, or writes an output before timing out, can therefore receive `status: ok` and an F1 score.

### Required fix

Write a machine-readable `execution.json` containing command, exit code, timeout, runtime and output path. The primary run status must be non-success when the process exits non-zero or times out. A score of a produced partial output may be retained as a clearly secondary diagnostic (`f1_of_partial_output`), never as the primary successful result.

Kill the complete process group on timeout so child processes cannot continue writing after the operator returns.

### Regression tests

- script writes valid labels then exits 1;
- script writes labels then sleeps beyond timeout;
- script exits 0 without labels;
- script exits 0 with valid labels;
- script writes malformed TIFF.

## P0.3 Figure 3 does not score the biological measurement requested in its own prompts

The code/agent prompts request a label image, a count and a table of areas in µm². `score_round2.py` currently scores only `labels.tif` with object F1 and related counts.

Add co-primary measurement checks:

- reported count equals the number of positive labels;
- requested area table exists;
- one row corresponds to each object identifier;
- reported area agrees with pixel count × pixel area within a frozen tolerance;
- unit is µm²;
- count error and area-distribution error against the manual reference are reported.

Do not allow good segmentation F1 to stand in for a correct biological measurement.

## P0.4 `cellpose_perturb.py` silently reuses stale output for an unknown run identifier

The script assigns `m` only inside its `if/elif` branches. For an unrecognized run name:

- on the first iteration, `m` is unbound and the script crashes;
- after any valid iteration, the previous iteration's `m` is written as `cp_<unknown>.tif`.

This is a genuine silent fallback.

Replace the branch chain with an explicit dispatch table/parser. Reject no arguments, unknown names, invalid factors and unsupported thresholds with informative errors. Verify the native output shape and label dtype before writing.

## P0.5 The tubule-width analysis is not sampling structures neutrally

### Orientation bias

`tubule_width.py` retains points with `ys % 12 == 0` but imposes no spacing in x. A horizontal skeleton on a retained row contributes nearly every pixel, whereas a vertical skeleton contributes roughly one point every 12 pixels. The claimed "regular grid" sampling is therefore strongly orientation-dependent.

### Unmatched structures

Locations are the union of reference and prediction skeletons, but orientation is taken from the reference. At prediction-only structures the reference profile and reference orientation may not describe a tubule; at reference-only structures the predicted profile may not describe one. A finite FWHM can still be extracted from noise.

### Silent selection

A location is retained only if all four FWHMs are finite. The code does not report candidate count, exclusion count or reason. Because failure in the predicted image removes the corresponding reference/low-resolution values, the retained paired sample can be selected by prediction measurability.

### Required fix

For width fidelity, define locations from the higher-resolution reference using an orientation-neutral deterministic spacing rule (for example, geodesic spacing along skeleton components or deterministic minimum-distance sampling). Measure prediction and low-resolution profiles at those fixed reference locations. Treat missed and prediction-only structures as separate detection/consistency outcomes rather than forcing a width measurement.

Record:

- candidate locations;
- retained locations;
- rejection reason per image;
- component identity;
- spacing rule;
- whether a prediction structure is present within a frozen tolerance.

Recompute panel e and its legend after this change. Do not preserve the current 2,450-location number by weakening the revised method.

## P0.6 The recorded protocol freeze no longer represents the execution protocol

The frozen manifest includes prompts, assets, the scorer and operator instructions, but the actual execution helper and conventions changed afterwards. `run_operator.py`, the runnable environment, rerun rules and figure-selection plan are not all part of the original freeze. Accepted runs already use post-freeze shell/scratchpad conventions.

Create protocol v2 and include hashes for the full executable protocol: operator, scorer, task definitions, environment files, rerun policy, rating rubric and blank final-figure layout. Treat existing accepted/rejected runs as pilots.

## P0.7 Active exploratory scripts can overwrite canonical Figure 1 outputs and use different science

`fig1/code/compare_models_A.py` writes `panel_c_step3/A_scores.json`, although `f1_scores.py` claims to be its only writer. Other active-directory scripts locally redefine `match()` or `lines_to_cells()`, manually slice pix2pix rows and use a different cancer-overlap rule.

Examples:

- `compare_cancer_gt.py`: local matcher;
- `compare_annotations.py`: local matcher and local junction conversion;
- `compare_nuclei_gt.py`: manual `[1:1023]` pix2pix alignment and a 0.5 cancer-overlap exclusion;
- `compare_models_A.py`: overwrites the canonical score file;
- `agent_run.py`: old within-field development/test design.

Move these files to an explicitly non-production `analysis/legacy/` or `superseded/` location, make outputs write only there, and update any retained logic to import the shared helpers. Production `code/` should contain only the dependency graph used by `make full` and the figure builders.

---

# P1 — important correctness and consistency fixes

## P1.1 Required values are sometimes replaced by `None`, blank fields or omissions

- `fig3/scoring/build_scores.py::agent_condition()` uses `reported.get("f1") if reported.is_file() else None`.
- `rescore_dev.py` uses `reported.get("f1")`.
- `all_runs_table.py` silently leaves scores blank when a label image has the wrong shape and infers task from substrings in `run_id`.
- `export_window.centroids()` silently skips requested label IDs that are absent; `contours(..., keep=...)` silently ignores missing requested IDs.

Required analysis artefacts and keys should fail with a precise error or receive an explicit non-success status and reason. Do not use `.get()` for schema-required fields.

## P1.2 `run_operator.py` does not generate trustworthy metadata automatically

`write_meta()` currently sets `app_executed_code` to `False` and `packages_installed` to `[]` unconditionally. At least one committed accepted run says `app_executed_code: true`, implying manual correction outside the helper. The allowed-tool audit is also not derived from `scenarios.csv`; for example, direct rows permit web tools in the hard-coded allowlist even when web is not offered in the scenario.

Derive execution metadata from recorded tool calls where possible and require an explicit, schema-validated operator record for facts that cannot be inferred. One file should define offered tools; the framing, audit and metadata code must all consume it.

Path isolation checks must use resolved paths and `Path.is_relative_to()`, not string-prefix tests. Relative `../` shell access and sibling paths must be detected.

## P1.3 Agent pipelines are tested with development artefacts still present

The test runner copies the complete agent folder, potentially including the development image, annotation, cached labels and intermediates. A pipeline can therefore consult development artefacts during field-209 inference.

Run the frozen pipeline in a clean directory containing only the test image, `pipeline.py`, and explicitly declared runtime weights/configuration. Require a runtime manifest. Development annotations must not be mounted.

## P1.4 Direct-answer polygon scoring needs a frozen malformed-output policy

`score_round2.rasterise()` reports overlap but allows later polygons to overwrite earlier ones. Partly out-of-bounds polygons are clipped and accepted; `n_valid` counts input polygons rather than final surviving labels; self-intersection is not checked.

Predefine whether overlapping/out-of-bounds polygons invalidate the output, are clipped, or receive a secondary diagnostic score. Record final surviving objects separately from syntactically valid polygons. For the final experiment, centres on a preselected crop are likely more auditable than hundreds of full-field polygons.

## P1.5 Statistical functions do not consistently reject empty, constant or non-finite inputs

Examples:

- `errors.py`: mean IoU of an empty match list becomes NaN; empty reference/prediction can divide by zero;
- `annot_agree.py` and `bio_result.py`: mean area of no objects becomes NaN;
- `al_intensity.py`, `image_generation.py`, `care_linearity.py`: Pearson/Spearman/regression can be undefined for fewer than two values or constant arrays;
- denoising intensity ratios can divide by zero or near-zero background-subtracted input;
- `squirrel_tile.py`, display `lin()` helpers and `norm_inputs.py` divide by a zero intensity range on constant input;
- `tubule_width.py` takes percentiles/medians of potentially empty retained sets.

Add small shared helpers that either return a structured explicit undefined status or raise with a precise message. Do not emit JSON NaN/Infinity; use strict `json.dump(..., allow_nan=False)` for scientific outputs.

## P1.6 `al_intensity.py` duplicates junction-to-cell conversion

The script manually repeats the same `label` → `expand_labels` → `clear_border` → sliver filtering implemented by `common.annotations.lines_to_cells`. Replace it with the shared function and test that the derived cell labels and intensity results remain unchanged.

## P1.7 Pixel sizes and other analysis metadata are still hard-coded in multiple scripts

`0.649614`, `0.6337`, `31.3` and `62.6` appear in analysis scripts and prose. Centralize field/image metadata in one checked machine-readable source and import it everywhere measurements are converted to physical units. Keep rounded display values separate from exact analysis values.

## P1.8 `bio_result.py` computes percentage differences from rounded means

The script rounds mean area to one decimal and then uses that rounded value for `area_vs_ref_pct`. Compute all comparisons from unrounded values and round only serialized display fields.

## P1.9 Window-selection code duplicates approximate scoring rules and hard-coded targets

`find_rep_window.py` hard-codes whole-field F1 targets (0.86 and 0.78). `export_fresh_field.py` implements a similar but separate centroid-based local score. A matched reference object can be counted as a local TP even when its matched prediction centroid lies outside the window, while displayed contours may include truncated objects crossing the crop.

Create one documented window-scoring/selection helper, read target whole-field scores from the scorer, define inclusion for boundary-crossing objects, and store the selection result. Keep window selection explicitly illustrative and separate from quantitative evaluation.

## P1.10 `postfilter.py` has ambiguous CLI behaviour

With no threshold argument it prints a threshold scan and exits successfully without writing the canonical output. Use an explicit CLI: required `--threshold` for production, optional `--scan` for exploration, mutually exclusive. A production invocation that omits the threshold should fail.

## P1.11 SQUIRREL execution suppresses all warnings and stores unstable runtime in a reproducibility JSON

`squirrel_run.py` calls `warnings.filterwarnings("ignore")` globally. This can hide numerical, shape, deprecation and library warnings. Filter only a documented known warning, or record warnings in the output/log.

The JSON also stores rounded wall-clock seconds. This is not scientifically part of the result and can make byte/content comparison nondeterministic. Put runtime in a log/metadata record excluded from scientific equality checks.

## P1.12 Figure 1/2 display helpers are duplicated and unsafe on constant data

Many local `lin()` implementations perform `(x - lo) / (hi - lo)` without verifying `hi > lo`; crop bounds and expected shapes are also largely unchecked. Introduce one display-only percentile stretch helper that validates finite input, non-empty crop and positive range. It must be clearly separated from quantitative normalization.

---

# Consistency matrix

| Scientific operation | Current state | Required state |
|---|---|---|
| Instance-label validation | repeated `astype(int)`; NaN/fraction/negative accepted | one strict shared validator at every score/input boundary |
| Object matching/F1 | active primary paths mostly use `common.matching`; exploratory duplicates remain | only `common.matching` for maintained code |
| Junction lines → cells | shared in most paths; duplicated in `al_intensity.py` and legacy scripts | only `common.annotations.lines_to_cells` |
| Pix2pix row alignment | shared reader in active Fig. 1–2 paths; legacy scripts slice manually | only `common.pix2pix.read_pix2pix` |
| Pixel size/units | repeated constants and rounded prompt values | one machine-readable metadata source; exact analysis values |
| Undefined statistics | NaN/Inf can be serialized | explicit undefined/error status; strict JSON |
| Required files/keys | mixture of raise, `None`, blank, skip | one policy: fail or explicit non-success status |
| Runtime success | output existence can override exit failure | execution status and scientific score kept distinct |
| Exploratory vs production | mixed in active `code/`; some overwrite canonical files | physically separate and unable to write production outputs |

---

# Minimal dependency-ordered remediation plan

## PR 1 — shared strict contracts

1. Add `common/labels.py` and tests.
2. Add strict statistical/display helpers or narrowly scoped equivalents.
3. Add one metadata file/API for pixel size and expected shapes.
4. Make `common.matching` document that callers must pass validated labels; optionally validate in debug/tests.

Acceptance: all current manual and model labels validate; invalid synthetic cases fail; current scores remain byte/value-identical unless a documented bug is exposed.

## PR 2 — migrate Figure 1 and Figure 2

1. Replace every label cast at scoring boundaries.
2. Replace duplicate `lines_to_cells` and pix2pix slicing.
3. Fix `cellpose_perturb`, `postfilter`, `al_roi`, empty statistics and SQUIRREL warnings/runtime.
4. Quarantine exploratory Figure 1 scripts.
5. Correct `bio_result` rounding.

Acceptance: `make check` and `make full` pass; no maintained script outside `common/` defines `match` or `lines_to_cells`; no active script writes canonical outputs except its declared producer.

## PR 3 — review and replace the tubule-width sampling

This is a scientific-method change and should be isolated. Implement the frozen revised sampling rule, exclusion accounting and synthetic orientation tests, then regenerate Figure 2e and review the biological interpretation.

Acceptance: horizontal/vertical synthetic tubules have comparable sampling density; exclusion counts are explicit; width recovery is validated on synthetic profiles with known FWHM.

## PR 4 — harden Figure 3 execution and scoring

1. execution status file and process-group timeout handling;
2. clean inference runtime for agents;
3. strict label validation and malformed polygon policy;
4. count/area/unit validation;
5. truthful metadata generation and one tool-permission source;
6. explicit statuses in round-1 table/build scripts;
7. new protocol freeze covering all executable components.

Acceptance: a failing/timed-out script can never receive primary `ok`; development annotations are unavailable at test inference; area-table and unit tests pass; every rerun decision is protocol-driven.

---

## What appears sound

- The core IoU computation and one-to-one matching are appropriate for the stated convention, and the repository now documents/test its edge cases.
- `common.pix2pix.read_pix2pix()` rejects unexpected source shape before applying the registered row offset.
- `common.annotations.lines_to_cells()` captures the currently documented conversion, although it should additionally reject non-2D input.
- Figure 1 canonical Cellpose/threshold output paths are now shared by producers and consumers.
- The second field removes the former within-field split boundary from round 2.

These strengths do not remove the P0 issues above.

## Verification limitation

This is a source-level adversarial audit. GitHub Actions did not provide a runnable environment in the earlier independent attempt, and no new Figure 3 scenarios were run for this review. The proposed fixes therefore require local execution of the full test/rebuild matrix and targeted scientific regression tests before merge. Green existing checks alone are insufficient because several defects concern behaviours the current tests do not exercise.
