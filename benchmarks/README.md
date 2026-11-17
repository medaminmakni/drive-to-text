# OCR benchmark

Small, reproducible benchmark used to choose the OCR engine (see decisions 006 and 007 in [docs/DECISIONS.md](../docs/DECISIONS.md)).
Published benchmarks rarely cover Arabic mixed with French, which is common in Tunisian documents, so we measure it ourselves.

## What is measured

| Metric | Meaning |
|---|---|
| **CER** (character error rate) | Characters wrong compared with the ground truth. Lower is better. Also counts reading-order mistakes. |
| **WER** (word error rate) | Same, at word level. In `results.csv`. |
| **Word F1** | Share of the right words found, in any order. Higher is better. Separates "badly read" from "read in the wrong order". |
| **s / image** | Time per image on the machine that runs the benchmark. |

Before scoring, Arabic diacritics and tatweel are removed, alef forms (أ إ آ) are unified, Arabic-Indic digits become 0-9 and whitespace is collapsed. Engines and ground truths often disagree on these even when the text is read correctly.

## Data

| Set | Content | Licence |
|---|---|---|
| `samples/` (committed) | 8 generated documents with exact ground truth: Arabic notice (clean, scan, photo), Arabic + French certificate (clean, scan), French invoice (clean, scan), English delivery note (photo) | Generated for this project (MIT) |
| `data/misraj/` (downloaded, not committed) | Real Arabic document pages from [Misraj-DocOCR](https://huggingface.co/datasets/Misraj/Misraj-DocOCR) | Apache-2.0 |

`make_samples.py` rebuilds `samples/` (it renders the text with Chromium so Arabic letters are shaped correctly).

## Engines

| Name | Engine |
|---|---|
| `tesseract` | Tesseract with the models installed on the machine (usually `tessdata_fast`) |
| `tesseract-best` | Tesseract with `tessdata_best` models (run `fetch_tessdata_best.py` first) |
| `easyocr` | EasyOCR on CPU (`pip install easyocr`) |
| `ollama:<model>` | Any vision model served by a local [Ollama](https://ollama.com), for example `ollama:glm-ocr` |

A missing engine is skipped with a message, it does not stop the run.

## Run it

From the repository root:

```bash
pip install -r benchmarks/requirements.txt
python benchmarks/fetch_tessdata_best.py          # optional, for tesseract-best
python benchmarks/fetch_misraj.py --count 20      # optional, real Arabic pages
ollama pull glm-ocr                               # optional, for ollama:glm-ocr

python benchmarks/run.py \
  --samples benchmarks/samples benchmarks/data/misraj \
  --engines tesseract tesseract-best easyocr ollama:glm-ocr
```

Results are written to `benchmarks/results/` (git-ignored): `results.csv` (one row per image and engine), `summary.md` (the table below) and the raw text of every engine in `outputs/`.

## Results

First run, generated samples only, Tesseract 5.3 with the default (fast) models, Linux CPU:

| Engine | CER arabic | CER latin | CER mixed | CER all | word F1 all | s / image |
|---|---|---|---|---|---|---|
| tesseract | 0.063 | 0.001 | 0.576 | 0.168 | 0.950 | 0.23 |

What it already shows:

- French and English are read almost perfectly, even on the scanned and photo versions.
- Clean Arabic is near perfect. The scanned serif version loses about 19% of characters.
- On the Arabic + French certificate, the words are mostly right (word F1 0.83 to 0.94) but CER is high. Tesseract treats the right-aligned Arabic lines and the left-aligned French lines as two columns and returns them in a different order. This is a layout problem, not a recognition problem.

The full comparison (tessdata_best, EasyOCR, GLM-OCR, real Misraj pages) is added here once it has been run.
