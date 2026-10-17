# cellbio-ai-guide

Data, code, prompts and LLM transcripts behind Figures 1–3 of
**"The cell biologist's guide to AI-assisted image analysis"** (Gómez-de-Mariscal, Henriques & Jacquemet).

Every pixel and every number in the three figures can be traced to a file here, and rebuilt:

```
python3 -m pip install -r environment/requirements.txt   # numpy, scipy, scikit-image, tifffile, pillow, pandas, matplotlib
make check                                                # fast check, ~1 min; changes no files
make full                                                 # full check from raw data, ~2 min; changes no files
```

Two checks, both run in a temporary copy:
- **`make check` (fast)** starts from the committed source data: unit tests, the SHA-256 of every raw file, the three
  figure SVGs rebuilt **byte-identical**, the Figure 1 and Figure 2 scoring re-run, and **every Figure 3 score**
  recomputed from the stored LLM outputs.
- **`make full`** starts from `data/raw`: it deletes the Figure 1 and Figure 2 source data, regenerates it script by
  script in dependency order (a missing input stops it), compares every regenerated file with the committed one, and
  rebuilds both figures byte-identical from the regenerated files. It also lists every file it did **not** regenerate
  and why: Cellpose-SAM outputs (re-run with `--with-models`, needs cellpose and torch), SQUIRREL (`--with-squirrel`,
  NanoPyx environment), and a few crops whose producer exists only as a recovered inline command or was not recovered.
  Figure 3 depends on LLM conversations, which cannot be regenerated; its scores are recomputed by the fast check.

## What is where

| Folder | Content |
|---|---|
| `data/` | raw images and annotations (unchanged bytes), sources and citations, checksums |
| `common/` | shared code: repository paths, object matching and F1 (with tests) |
| `fig1/` | Figure 1: builder, the exact source data it draws, processing and scoring scripts, legend |
| `fig2/` | Figure 2: as above, including SQUIRREL (NanoPyx) for panel e |
| `fig3/` | Figure 3, split by use: `advice/`, `code/`, `optimise/`, `direct_answers/`; plus `figure/`, `scoring/`, `harness/`, `prompt_pack/`, `pilots/`, `superseded/` |
| `box1/` | Box 1 versions (the one used in Fig. 3 and the current draft) |
| `tools/` | porting and checking tools (how this repository was assembled; `check_all.py` fast check, `check_full.py` full check, `svg_to_pdf.py`) |
| `docs/` | adversarial audit, our response (`audit_response.md`) and repository plan |
| `AGENTS.md` | purpose, status and working rules for anyone (human or AI) working in this repository |

Each figure folder follows the same layout: `code/` (builder and scripts), `source_data/` (the files the builder reads,
under the names it reads them), `figure/` (SVG, PDF), `legend.md`, `README.md` (provenance and caveats),
`superseded/` (earlier builders, kept for the record).

## Scope
The figures illustrate how to use AI tools; they are not benchmarks. Scores come from one field of view and, for LLMs,
a few runs per condition on one model (Claude Sonnet, October 2026). Caveats are listed at the top of each figure README.

## Licence
Code: MIT (`LICENSE`). Images, annotations, figures, prompts and text: CC BY 4.0 (`LICENSE-content.md`).
Third-party data keep their own licence. Cite the data sources in `data/sources.csv`.

## Path placeholders
Transcripts, logs and record-only scripts (`recovered_inline/`, `fig3/harness/`, superseded code) keep their original
commands; local folder prefixes were replaced by placeholders: `<work>` and `<work2>` (the two working folders;
`<fig3-work>` = `<work>/fig3`), `<uploads>` (the raw files, now `data/raw/` under the names in `data/raw_name_map.csv`),
`<tasks>`, `<transcript>`, `<transcript2>` (session records, not included).
