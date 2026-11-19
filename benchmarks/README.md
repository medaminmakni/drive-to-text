# OCR benchmark

Small, reproducible benchmark used to choose the OCR engine (decisions 006 and 007 in [docs/DECISIONS.md](../docs/DECISIONS.md)).
Published benchmarks rarely cover Arabic mixed with French, which is common in Tunisian documents, so we measured it ourselves on 59 documents.

**Results in short**

- **Tesseract is the right default.** With small images upscaled first, it reaches CER 0.08 on Arabic book pages and word F1 0.77 on scanned French forms, at about 1.4 s per page on a CPU.
- **The AI model GLM-OCR invents Arabic text** (CER 5.2 on Arabic books) and takes about 89 s per page on a GPU. It stays optional, for clean French and English documents.
- **Layout matters as much as the model.** Mixed Arabic + French forms read best in "one block" mode (psm 6), book pages and forms in automatic mode (psm 3). The app offers both.

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

1. **GLM-OCR is perfect on French and English but unusable on Arabic.** It writes fluent Arabic that is not on the page (for example "شركة أقامة" for "شهادة إقامة"), and is 7 to 10 times slower, even on a GPU.
2. **On mixed Arabic + French, the layout mode matters more than the model.** In automatic mode (psm 3) Tesseract finds the right words but reads the Arabic and French lines as two columns. One-block mode (psm 6) brings the CER from 0.58 to 0.03.
3. **psm 6 is worse on book pages** (0.34 to 0.37 vs 0.30), which have headers and footnotes to keep apart. A layout model (PP-DocLayoutV3) is the proper fix and is a next step.
4. **`tessdata_best` models are only slightly more accurate**, and 35 to 50% slower.

### Round 2: Arabic book pages and French forms (19 Nov 2026)

40 more pages: 20 printed Arabic book passages from KITAB-Bench (Hindawi, 612 x 792 px images) and 20 scanned French forms from XFUND. Tesseract 5 with the default models, on CPU in the cloud sandbox; GLM-OCR through Ollama on the laptop GPU. Same pages for every engine.

| Engine | CER arabic_books | word F1 arabic_books | CER forms_fr | word F1 forms_fr | s / image |
|---|---|---|---|---|---|
| tesseract (psm 3) | 0.320 | 0.595 | 0.294 | **0.774** | 1.3 |
| tesseract (psm 3) + upscaling to 1200 px | 0.081 | 0.760 | 0.294 | **0.774** | 1.4 |
| tesseract (psm 6) | 0.078 | 0.753 | **0.243** | 0.747 | 1.3 |
| tesseract (psm 6) + upscaling to 1200 px | **0.076** | **0.763** | **0.243** | 0.747 | 1.4 |
| ollama:glm-ocr | 5.207 | 0.032 | 0.896 | 0.178 | 88.7 |

5. **Small images were most of Tesseract's Arabic problem.** The book pages are 72 DPI, so letters are a few pixels high. Upscaling to 1200 px before OCR (now done by the app, decision 017) brings the CER from 0.32 to 0.08.
6. **GLM-OCR confirms round 1:** about five times more text than the page holds on Arabic books, under a fifth of the words on French forms.
7. **On forms, word F1 (the main score) is best with psm 3.** The app keeps psm 3 as the default and offers psm 6 as "Simple layout".

Limits: 59 documents, generated samples use two fonts, and timings depend on the machine. The benchmark supports the engine choice for this proof of concept; it does not rank OCR engines in general.
