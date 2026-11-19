# Sample output

JSON exports produced by the app from real, public Google Drive folders (same format as the
"Export JSON" button, see [docs/API.md](../docs/API.md)).

| File | Drive folder | What it shows |
|---|---|---|
| `sample-output.json` | [documents](https://drive.google.com/drive/folders/1SEpqcVS9xtV5MZ41WxjKHzSu9SD54RuB) (11 files) | Native PDFs (parser), scanned PDFs, photos and images (OCR), English, French, Arabic, a rotated scan, a street photo flagged for review |
| `sample-edge-cases.json` | [edge-cases](https://drive.google.com/drive/folders/1iXL8lI6tsen8PjJOFEX8SpVygCrAeVXD) (2 files) | A blank scanned page (flagged: no text) and a damaged PDF (clean failure) |

Settings: Tesseract, languages `ara+eng+fra`, automatic layout. The documents are public forms
and test pages; the folder's `sources.json` lists where each one comes from.

## Results at a glance

| File | Method | Confidence | Note |
|---|---|---|---|
| 01-irs-w9-en.pdf | PDF parser | – | 6 pages, exact text |
| 02-cerfa-cession-fr.pdf | PDF parser | – | exact text |
| 03-mcdonalds-receipt.jpg | OCR | 78 | photo of a receipt |
| 04-multilingual-text.png | OCR | 92 | |
| 05-arabic-scan.jpg | OCR | 83 | 2 of 3 lines exact; the "Simple layout" option reads all 3 |
| 06-french-scan.pdf | OCR | 91 | |
| 07-linn-scan.pdf | OCR | 95 | |
| 08-typewritten-page.png | OCR | 89 | |
| 09-epson-scan.pdf | OCR | 93 | |
| 10-rotated-skew-scan.pdf | OCR | 95 | |
| 11-french-photo.jpg | OCR | – | street signs (scene text): no text found, flagged for review |

## Rebuild

With the backend running (`uvicorn app.main:app --port 8000`):

```
python samples/make_sample.py "https://drive.google.com/drive/folders/1SEpqcVS9xtV5MZ41WxjKHzSu9SD54RuB"
python samples/make_sample.py "https://drive.google.com/drive/folders/1iXL8lI6tsen8PjJOFEX8SpVygCrAeVXD" --out sample-edge-cases.json
```

Batch ids, dates and durations change from run to run.
