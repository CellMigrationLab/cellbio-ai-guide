# Software environments

Most figure checks need only the base Python dependencies. Re-running the deep-learning models or SQUIRREL requires additional software.

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
| Re-run the historical Fiji macros (Figure 3 round 1) | Fiji for Linux x64, as used on 16 October 2026 | Headless invocation: `xvfb-run -a ImageJ-linux64 -batch macro.ijm`. Not part of protocol v2. |
| Review Figure 3 LLM experiments | [Figure 3 records](../fig3/README.md) and [protocol v2](../fig3/PROTOCOL_V2.md) | The LLM conversations cannot be reproduced byte-for-byte; their outputs and transcripts are retained. |

**Cellpose version caveat:** in Cellpose 4.2.1.1, asking for the removed `cyto3` model can silently load `cpsam_v2`. Figure 3a uses this as an example of why a script running successfully does not prove the requested model was used.

## Export PDFs

The SVGs are converted using headless Chromium:

```bash
make pdf
```

See [tools/svg_to_pdf.py](../tools/svg_to_pdf.py) for the converter.
