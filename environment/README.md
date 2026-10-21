# Software environments

Most figure checks need only the base Python packages. Re-running the deep-learning models or SQUIRREL needs the extra software below; nothing else is required.

## Start here

From the repository root:

```bash
python3 -m pip install -r environment/requirements.txt
make check
make full
```

The base environment uses Python 3.13. The SVG builders themselves use the Python standard library.

## Optional software

| Task | Setup | Notes |
|---|---|---|
| Re-run Cellpose segmentations | `python3 -m pip install -r environment/requirements-models.txt --extra-index-url https://download.pytorch.org/whl/cpu` | The CPU PyTorch build comes from the PyTorch index; use `python tools/check_full.py --with-models`. |
| Re-run SQUIRREL (Figure 2e) | Install [requirements-nanopyx.txt](requirements-nanopyx.txt) in a **separate virtual environment** | NanoPyx has different NumPy requirements; run the full check with `--with-squirrel`. |
| Review Figure 3 LLM experiments | [Figure 3 records](../fig3/README.md) and [protocol v2](../fig3/PROTOCOL_V2.md) | The LLM conversations cannot be reproduced byte-for-byte; their outputs and transcripts are retained. |

**Cellpose version caveat:** in Cellpose 4.2.1.1, `models.Cellpose` no longer exists and asking `CellposeModel` for the removed `cyto3` or `nuclei` weights silently loads `cpsam_v2`. This is why the row-a note of Figure 3 says that outdated advice can "silently run another model": a script that runs is not proof that the requested model was used.

## Export PDFs

The figure SVGs are converted using headless Chromium:

```bash
make pdf     # Figures 1 and 2
make fig3    # Figure 3: SVG, PNG and PDF (the PDF also needs headless Chromium)
```

See [tools/svg_to_pdf.py](../tools/svg_to_pdf.py) for the converter.
