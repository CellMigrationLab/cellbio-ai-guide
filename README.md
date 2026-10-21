# The cell biologist's guide to AI-assisted image analysis

This repository accompanies the article **“The cell biologist's guide to AI-assisted image analysis”** by Estibaliz Gómez-de-Mariscal, Ricardo Henriques and Guillaume Jacquemet.

Everything behind the three figures is here: the microscopy images and manual annotations, the code that processed and scored them, the figure builders, the reusable prompt of Box 1, and a verbatim record of every LLM conversation in the Figure 3 experiment. The aim is that anyone can trace each number in the figures to its source and rebuild it. Model outputs and LLM replies that cannot be regenerated exactly are kept as records, and each figure's README says what is rerun and what is read from the records.

**Start here:** the table below links each figure to its files and its data-and-methods notes; `make check` (next section) rebuilds and verifies all of it.

## Figures and data

| Material | Open | What it contains |
|---|---|---|
| **Figure 1** | [SVG](fig1/figure/fig1.svg) · [PDF](fig1/figure/fig1.pdf) · [data and methods](fig1/README.md) | Where AI enters a microscopy workflow, and a practical route from a biological question to a checked analysis. |
| **Figure 2** | [SVG](fig2/figure/fig2.svg) · [PDF](fig2/figure/fig2.pdf) · [data and methods](fig2/README.md) | How to decide whether segmentation, denoising, artificial labelling or super-resolution is good enough for the intended measurement. |
| **Figure 3** | [PNG](fig3/figure_v2/output/fig3_v2.png) · [SVG](fig3/figure_v2/output/fig3_v2.svg) · [PDF](fig3/figure_v2/output/fig3_v2.pdf) · [study overview](fig3/README.md) · [protocol](fig3/PROTOCOL_V2.md) | Four ways to use an LLM for image analysis: 72 recorded runs of Claude Sonnet 5.5 on three segmentation and counting tasks, scored against manual annotation. |
| **Microscopy data** | [dataset guide](data/README.md) · [visual overview](data/overview.png) · [raw files](data/raw/) · [sources and licences](data/sources.csv) | Two annotated fields of cancer cells on an endothelial monolayer, plus the denoising, artificial-labelling and super-resolution examples used in the figures. |
| **Box 1** | [copy the prompt (as in the article)](box1/box1_manuscript.md) · [version tested in Figure 3](box1/box1_final.md) · [differences](box1/README.md) | A reusable prompt for asking an LLM to produce an image-analysis workflow that can be inspected and tested. |

## Rebuild and check the figures

Clone the repository, install the pinned packages (Python 3.13 was used), then run the fast or the full check:

```bash
git clone https://github.com/CellMigrationLab/cellbio-ai-guide.git
cd cellbio-ai-guide
python3 -m pip install -r environment/requirements.txt
make check     # a few minutes: tests, checksums, every figure and score rebuilt and compared
make full      # longer: regenerates the Figure 1 and 2 source data from the raw images first
```

`make check` runs the unit tests, verifies the checksums of the raw files, rebuilds the three figure SVGs from the committed source data (they must come out byte-identical) and recomputes every stored score. It changes no file. `make fig1`, `make fig2` and `make fig3` rebuild one figure in place (SVG and PDF; Figure 3 also PNG; the PDFs need headless Chromium).

`make full` starts from the raw data and regenerates the Figure 1 and Figure 2 source files for which a runnable producer is available. It reports any files that were kept rather than regenerated. Cellpose-SAM and SQUIRREL require the additional environments described in [`environment/README.md`](environment/README.md).

Figure 3 is built from recorded LLM conversations. The replies cannot be regenerated (a model answers differently each time), but everything downstream of them, the execution of the returned code, the scores and the figure, is recomputed from the records.

## Repository layout

| Path | Contents |
|---|---|
| [`data/`](data/) | Raw images, annotations, checksums, provenance and source licences. |
| [`common/`](common/) | Shared analysis code and tests, including label validation, object matching, annotation conversion and image metadata. |
| [`fig1/`](fig1/) | Figure 1 code, source data, figure files and provenance notes. |
| [`fig2/`](fig2/) | Figure 2 code, source data, figure files and provenance notes. |
| [`fig3/`](fig3/) | The LLM experiment: protocol, the harness that ran it and the 72 run records (`v2/`), the scoring code, the figure builder (`figure_v2/`) and tests. |
| [`box1/`](box1/) | Box 1 as printed in the article, and the slightly extended version tested in Figure 3 (differences in `box1/README.md`). Earlier versions survive in git history. |
| [`tools/`](tools/) | Repository checks (fast and full) and SVG-to-PDF conversion. |

## Scope

The figures are worked examples, not benchmarks. Most quantitative panels use one or two fields of view from one experiment. The Figure 3 experiment is one model, three tasks and three runs per condition, made on 17–19 October 2026 with the model and software versions recorded in each run; [`fig3/PROTOCOL_V2.md`](fig3/PROTOCOL_V2.md) is the plan that was followed and [`fig3/deviations.md`](fig3/deviations.md) lists everything that departed from it. The figure-specific READMEs give the caveats and scoring conventions. All three figures are the final versions of the article.

## Citation and licence

Use [`CITATION.cff`](CITATION.cff) to cite this repository. When reusing a source dataset, also cite the original source listed in [`data/sources.csv`](data/sources.csv).

Code is released under the [MIT licence](LICENSE). Images, annotations, figures, prompts and text are released under [CC BY 4.0](LICENSE-content.md), except where a third-party source retains its own licence.

## Use of AI in this repository

The AI coding assistant Claude Sonnet 5.5, accessed through Claude Code, helped develop, debug and revise the code for data
analysis and figure formatting in this repository (the commit history marks these commits). The authors reviewed the
AI-assisted code and analyses, verified the reported results and take full responsibility for them. Claude Sonnet 5.5 via
headless Claude Code was also the model evaluated in the experiments of Figure 3; its prompts, replies and outputs are
stored verbatim in `fig3/v2/runs/` and are research records, not authors' text. (Language editing of the manuscript used
GPT-6.1 and Grammarly; this does not concern the repository.)

## Acknowledgements

The RCAN super-resolution prediction in Figures 1 and 2e was provided by Iván Hidalgo-Cenalmor; the image it is applied to is
from the BioSR dataset (Qiao et al. 2021). Funding is listed in the article.

## Working on the repository

Read [`AGENTS.md`](AGENTS.md) before changing analysis code, generated files or LLM records, whether you are a person or an AI assistant. It explains the provenance rules (every file in `source_data/` is made by a script in `code/`, LLM records are never edited), which files may be regenerated, and the path placeholders (`<work>`, `<uploads>`, …) used in recorded commands. Questions and corrections are welcome as GitHub issues.
