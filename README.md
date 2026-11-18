# Drive-to-Text

Small web app that takes a public Google Drive folder link, lists the PDFs and images inside it, and extracts their text: a PDF parser for native PDFs, OCR for images and scanned pages.

Work in progress. Technical choices and their reasons are recorded in [docs/DECISIONS.md](docs/DECISIONS.md).

## OCR languages

Tesseract needs one model file per language. The app lists English, French and Arabic, and greys out
any language whose model is missing on the server (a batch that asks for it is refused with a clear message).

- **Docker:** the image installs all three, nothing to do.
- **Linux:** `sudo apt install tesseract-ocr-eng tesseract-ocr-fra tesseract-ocr-ara`
- **Windows (UB Mannheim installer):** run the installer again and tick Arabic and French under
  "Additional language data", or download `ara.traineddata` and `fra.traineddata` from
  [tesseract-ocr/tessdata](https://github.com/tesseract-ocr/tessdata) into `C:\Program Files\Tesseract-OCR\tessdata`.

Check with `tesseract --list-langs`, then restart the backend.
