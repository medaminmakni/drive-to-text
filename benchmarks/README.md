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

Run on 17 Nov 2026. 8 generated samples + 11 real text pages from Misraj-DocOCR (pages that are mostly photos are skipped by `fetch_misraj.py`).
Tesseract 4.1/5 models ran on CPU (2-core Linux sandbox). GLM-OCR ran through Ollama on a laptop GPU (model fully in GPU memory).

| Engine | CER arabic | CER arabic_real | CER latin | CER mixed | CER all | word F1 all | s / image |
|---|---|---|---|---|---|---|---|
| tesseract-fast (psm 3) | 0.061 | **0.303** | **0.000** | 0.576 | 0.246 | **0.737** | **5.4** |
| tesseract-fast@6 | 0.018 | 0.365 | 0.020 | 0.030 | 0.221 | 0.729 | 6.4 |
| tesseract-best (psm 3) | 0.061 | 0.307 | **0.000** | 0.592 | 0.250 | **0.741** | 7.3 |
| tesseract-best@6 | **0.016** | 0.343 | 0.020 | **0.006** | **0.205** | 0.723 | 9.5 |
| ollama:glm-ocr | 0.595 | 1.521 | **0.000** | 0.192 | 0.995 | 0.297 | 51.0 |

Groups: `arabic` = generated Arabic notice (clean, scan, photo), `arabic_real` = Misraj book pages, `latin` = French and English documents, `mixed` = Arabic + French certificate.

What the numbers say:

1. **GLM-OCR is perfect on French and English but unusable on Arabic.** It writes fluent Arabic that is not on the page (for example "شركة أقامة" for "شهادة إقامة"). A CER above 1.0 on real pages means it produced more invented text than the page contains. It is also about 7 to 10 times slower, even on a GPU.
2. **Page segmentation decides the mixed Arabic + French result, not the model.** With psm 3, Tesseract reads the right words (word F1 above 0.83) but treats the right-aligned Arabic lines and the left-aligned French lines as two columns. psm 6 (one block, line by line) brings the CER from 0.58 to 0.03 or less.
3. **psm 6 is worse on real book pages** (0.34 to 0.37 vs 0.30), which have footnotes, headers and page numbers that must stay separate. The right mode depends on the document type. A layout model that predicts reading order (PP-DocLayoutV3, Apache-2.0) is the proper fix and is listed as a next step.
4. **`tessdata_best` is only slightly more accurate than the default `tessdata_fast` models**, and 35 to 50% slower.
5. **Real Arabic pages are still hard for every engine tested here** (CER around 0.30). This matches KITAB-Bench, where the best open model that runs locally (AIN-7B, GPU) reaches 0.20 and Tesseract 0.54.

Limits of this benchmark: small sample (19 documents), generated samples use only two fonts, timings depend on the machine. It is meant to support the engine choice for this proof of concept, not to rank OCR engines in general.
