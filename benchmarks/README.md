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
| `data/kitab_hindawi/` (downloaded, not committed) | Printed Arabic book passages, Hindawi subset of [KITAB-Bench](https://github.com/mbzuai-oryx/KITAB-Bench) (ACL 2025) | Not stated on the dataset card (KITAB-Bench repository: MIT). Evaluation only |
| `data/xfund_fr/` (downloaded, not committed) | Scanned French forms from [XFUND](https://github.com/doc-analysis/XFUND) | CC BY-NC-SA 4.0. Evaluation only, not redistributed |
| `data/funsd/` (downloaded, not committed) | Noisy scanned English forms from [FUNSD](https://guillaumejaume.github.io/FUNSD/) | Non-commercial research. Evaluation only, not redistributed |

All downloaded sets have a **human-made ground truth** ("gold"). For forms, the reference text is built from the labelled boxes ordered top to bottom and left to right. Forms have no single correct reading order, so **word F1 is the main score for them**, not CER.

`make_samples.py` rebuilds `samples/` (it renders the text with Chromium so Arabic letters are shaped correctly).

## Engines

| Name | Engine |
|---|---|
| `tesseract` | Tesseract with the models installed on the machine (`tessdata_fast` in the Docker image and most Linux packages) |
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
python benchmarks/fetch_kitab.py --count 20       # optional, Arabic book passages (KITAB-Bench)
python benchmarks/fetch_xfund.py --count 20       # optional, French forms
python benchmarks/fetch_funsd.py --count 20       # optional, English forms
ollama pull glm-ocr                               # optional, for ollama:glm-ocr

python benchmarks/run.py \
  --samples benchmarks/samples benchmarks/data/misraj \
  --engines tesseract tesseract-best easyocr ollama:glm-ocr
```

Results are written to `benchmarks/results/` (git-ignored): `results.csv` (one row per image and engine), `summary.md` (the table below) and the raw text of every engine in `outputs/`.

## Results

Run on 17 Nov 2026. 8 generated samples + 11 real text pages from Misraj-DocOCR (pages that are mostly photos are skipped by `fetch_misraj.py`).
Tesseract 4.1.1 ran on CPU (2-core Linux sandbox; Docker images ship Tesseract 5, same LSTM models). GLM-OCR ran through Ollama on a laptop GPU (model fully in GPU memory).

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

### Round 2: Arabic book pages and French forms (19 Nov 2026)

40 more pages: 20 printed Arabic book passages from KITAB-Bench (Hindawi, 612 x 792 px images) and 20 scanned French forms from XFUND. Tesseract 5 with the default models, on CPU in the cloud sandbox; GLM-OCR through Ollama on the laptop GPU. Same pages for every engine.

| Engine | CER arabic_books | word F1 arabic_books | CER forms_fr | word F1 forms_fr | s / image |
|---|---|---|---|---|---|
| tesseract (psm 3) | 0.320 | 0.595 | 0.294 | **0.774** | 1.3 |
| tesseract (psm 3) + upscaling to 1200 px | 0.081 | 0.760 | 0.294 | **0.774** | 1.4 |
| tesseract (psm 6) | 0.078 | 0.753 | **0.243** | 0.747 | 1.3 |
| tesseract (psm 6) + upscaling to 1200 px | **0.076** | **0.763** | **0.243** | 0.747 | 1.4 |
| ollama:glm-ocr | 5.207 | 0.032 | 0.896 | 0.178 | 88.7 |

6. **Small images were most of Tesseract's Arabic problem.** The book pages are 72 DPI: letters are only a few pixels high. Upscaling them to 1200 px before OCR (now done by the app, decision 017) brings the CER from 0.32 to 0.08. This also explains part of the 0.30 on the Misraj pages in round 1, which are around 1,100 px wide.
7. **GLM-OCR confirms round 1 on harder pages.** On Arabic books it writes about five times more text than the page holds (CER 5.2); on French forms it finds under a fifth of the words, and it takes 89 s per page on a GPU. It stays an optional engine for clean French and English documents, flagged for review on Arabic.
8. **On forms, word F1 (the main score) is best with psm 3**, while psm 6 has a lower CER because it keeps the left-to-right order of side-by-side fields. The app keeps psm 3 as the default and offers psm 6 as "Simple layout".

Limits of this benchmark: 59 documents in total, generated samples use only two fonts, timings depend on the machine (round 1 on a 2-core sandbox, round 2 on a faster one). It is meant to support the engine choice for this proof of concept, not to rank OCR engines in general.
