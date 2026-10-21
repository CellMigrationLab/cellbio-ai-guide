# The cell biologist's guide to AI-assisted image analysis

This repository accompanies the manuscript **“The cell biologist's guide to AI-assisted image analysis”** by Estibaliz Gómez-de-Mariscal, Ricardo Henriques and Guillaume Jacquemet.

It contains the figures, microscopy images and annotations, analysis code, the reusable prompt from Box 1, and the records behind the LLM experiments. Scripts rebuild the figure files and recompute the reported scores. Published model outputs and LLM replies are stored as records when exact regeneration is not possible; each figure README states what was rerun and what was not.

## Figures and data

| Material | Open | What it contains |
|---|---|---|
| **Figure 1** | [SVG](fig1/figure/fig1.svg) · [PDF](fig1/figure/fig1.pdf) · [legend](fig1/legend.md) · [data and methods](fig1/README.md) | Where AI enters a microscopy workflow, and a practical route from a biological question to a checked analysis. |
| **Figure 2** | [SVG](fig2/figure/fig2.svg) · [PDF](fig2/figure/fig2.pdf) · [legend](fig2/legend.md) · [data and methods](fig2/README.md) | How to decide whether segmentation, denoising, artificial labelling or super-resolution is good enough for the intended measurement. |
| **Figure 3** | [PNG](fig3/figure_v2/output/fig3_v2.png) · [SVG](fig3/figure_v2/output/fig3_v2.svg) · [PDF](fig3/figure_v2/output/fig3_v2.pdf) · [study overview](fig3/README.md) · [protocol](fig3/PROTOCOL_V2.md) | Four ways to use an LLM for image analysis. Seventy-two runs of an LLM (Claude Sonnet 5.5) on three tasks, scored against manual annotation (draft, under review by the authors). |
| **Microscopy data** | [dataset guide](data/README.md) · [visual overview](data/overview.png) · [raw files](data/raw/) · [sources and licences](data/sources.csv) | Two annotated fields of cancer cells on an endothelial monolayer, plus the denoising, artificial-labelling and super-resolution examples used in the figures. |
| **Box 1** | [copy the prompt (as in the article)](box1/box1_manuscript.md) · [version tested in Figure 3](box1/box1_final.md) · [differences](box1/README.md) | A reusable prompt for asking an LLM to produce an image-analysis workflow that can be inspected and tested. |

## Rebuild and check the figures

Install the base dependencies, then run the fast or full check:

```bash
python3 -m pip install -r environment/requirements.txt
make check
make full
```

`make check` runs the tests, verifies the raw-file checksums, rebuilds the figure SVGs from the committed source data and recomputes the stored scores.

`make full` starts from the raw data and regenerates the Figure 1 and Figure 2 source files for which a runnable producer is available. It reports any files that were kept rather than regenerated. Cellpose-SAM and SQUIRREL require the additional environments described in [`environment/README.md`](environment/README.md).

Figure 3 depends on recorded LLM conversations. Those replies cannot be regenerated bit for bit, but the stored outputs can be rescored.

## Repository layout

| Path | Contents |
|---|---|
| [`data/`](data/) | Raw images, annotations, checksums, provenance and source licences. |
| [`common/`](common/) | Shared analysis code and tests, including label validation, object matching, annotation conversion and image metadata. |
| [`fig1/`](fig1/) | Figure 1 code, source data, figure files, legend and provenance notes. |
| [`fig2/`](fig2/) | Figure 2 code, source data, figure files, legend and provenance notes. |
| [`fig3/`](fig3/) | Protocol v2, its harness and run records (`v2/`), the figure (`figure_v2/`), scoring references and tests. |
| [`box1/`](box1/) | Box 1 as printed in the article, and the slightly extended version tested in Figure 3 (differences in `box1/README.md`). Earlier versions survive in git history. |
| [`tools/`](tools/) | Repository checks (fast and full) and SVG-to-PDF conversion. |

## Scope and current status

The figures are worked examples, not benchmarks. Most quantitative panels use one or two fields of view from one experiment. The LLM experiments use small, date-stamped samples, and the interface and model are recorded with each run. The figure-specific README files give the relevant caveats and scoring conventions.

Figures 1, 2 and 3 are the final manuscript versions. For Figure 3 the stored output is the protocol-v2 figure (`fig3/figure_v2/`), built from the study in [`fig3/PROTOCOL_V2.md`](fig3/PROTOCOL_V2.md). Of its 72 runs, 54 are scored and the 18 row-A runs are classified.

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

Read [`AGENTS.md`](AGENTS.md) before changing analysis code, generated files or LLM records. It explains the provenance rules, which files may be regenerated or edited, and the path placeholders (`<work>`, `<uploads>`, …) used in transcripts and recorded scripts.
