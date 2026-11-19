# API contract

The web page (`web/`, Next.js) and the backend (`app/`, FastAPI) agree on these calls and JSON shapes.
The page calls `/api/...` on its own address and Next.js forwards the request to FastAPI, so the browser sees a single origin (no CORS).

Errors always come back as `{"detail": "message to show the user"}` with an HTTP status:
400 bad request (invalid link, unknown or not installed language), 404 not found (private or missing folder, unknown batch), 502 Google Drive problem (API key, quota, network), 422 malformed request.

## GET /api/config

What the page can offer.

```json
{
  "engines": [
    {"name": "tesseract", "label": "Tesseract (default, fast, Arabic/French/English)", "available": true, "reliable_for_arabic": true},
    {"name": "glm-ocr", "label": "glm-ocr via Ollama (optional AI model, slower, best for French/English layouts)", "available": false, "reliable_for_arabic": false}
  ],
  "default_engine": "tesseract",
  "languages": [
    {"code": "eng", "label": "English", "installed": true},
    {"code": "fra", "label": "French", "installed": true},
    {"code": "ara", "label": "Arabic", "installed": false}
  ],
  "default_language": "eng",
  "page_modes": [
    {"value": "auto", "label": "Automatic layout"},
    {"value": "single_block", "label": "Simple layout (one column): forms, letters, certificates"}
  ],
  "max_file_size_mb": 25
}
```

`installed` is false when Tesseract on the server has no model for that language: the page shows it greyed out, and a batch that asks for it is refused with 400.

## POST /api/folders

Request: `{"url": "https://drive.google.com/drive/folders/<id>?usp=sharing"}`

Response 200:

```json
{
  "folder_id": "1AbC...",
  "folder_name": "Test documents",
  "skipped": 1,
  "files": [
    {"id": "1XyZ...", "name": "contrat.pdf", "mime_type": "application/pdf", "type": "pdf", "size": 27457}
  ]
}
```

`size` is in bytes and can be `null` when Drive does not report it. `skipped` counts items that are not PDFs or images (sub-folders included).

## POST /api/batches

Starts processing the selected files in the background.

Request:

```json
{"url": "https://drive.google.com/drive/folders/<id>", "file_ids": ["1XyZ..."], "lang": "ara+fra", "page_mode": "auto", "engine": "tesseract"}
```

`lang`, `page_mode` and `engine` are optional (defaults from `/api/config`). The folder is listed again on the server, so only files that really belong to it are processed.

Response 202: a batch object (see below), every file `pending`.

## GET /api/batches/{batch_id}

Current state of a batch. The page asks every second until `status` is `completed`.

```json
{
  "batch_id": "3f9c2a1b7d4e",
  "folder_id": "1AbC...",
  "folder_name": "Test documents",
  "created_at": "2026-11-18T10:42:03+00:00",
  "options": {"lang": "ara+fra", "page_mode": "auto", "engine": "tesseract"},
  "status": "running",
  "counts": {"pending": 1, "processing": 1, "done": 1, "failed": 1},
  "files": [
    {
      "id": "1XyZ...", "name": "contrat.pdf", "type": "pdf", "size": 27457,
      "status": "done", "error": null, "duration_ms": 412,
      "result": {
        "method": "pdf_parser", "ocr_engine": null, "confidence": null, "needs_review": false,
        "pages_count": 2, "warnings": [], "text": "...",
        "pages": [{"number": 1, "method": "pdf_parser", "confidence": null, "needs_review": false, "review_reason": null, "text": "..."}]
      }
    },
    {"id": "1Def...", "name": "corrompu.pdf", "type": "pdf", "size": 64, "status": "failed",
     "error": "This PDF is damaged or not a valid PDF.", "duration_ms": 35, "result": null}
  ]
}
```

File `status`: `pending` → `processing` → `done` or `failed`.
`method`: `pdf_parser`, `ocr`, or `pdf_parser+ocr` (PDF with some scanned pages).
`review_reason`: `low_confidence`, `no_text`, `ai_ocr_arabic`, or `null`.

## GET /api/batches/{batch_id}/export

The same JSON as above, sent as a downloadable file `drive-to-text-<batch_id>.json`.
