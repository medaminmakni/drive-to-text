# Decision log

Every technical choice in this project is written down here with the reason, the alternatives we looked at and what we accept to lose. Status is **Accepted** (decided) or **Proposed** (waiting for our own measurement).

| # | Decision | Status |
|---|---|---|
| 001 | [Python and FastAPI for the backend](#001-python-and-fastapi-for-the-backend) | Accepted |
| 002 | [One plain HTML/JS page for the frontend](#002-one-plain-htmljs-page-for-the-frontend) | Accepted |
| 003 | [Google Drive API v3 with an API key](#003-google-drive-api-v3-with-an-api-key) | Accepted |
| 004 | [pypdf for native PDFs](#004-pypdf-for-native-pdfs) | Accepted |
| 005 | [Scanned page detection and rendering with pypdfium2](#005-scanned-page-detection-and-rendering-with-pypdfium2) | Accepted |
| 006 | [Tesseract as the default OCR engine](#006-tesseract-as-the-default-ocr-engine) | Proposed |
| 007 | [Optional vision-language OCR engine through Ollama](#007-optional-vision-language-ocr-engine-through-ollama) | Proposed |
| 008 | [Route files by content, not by extension](#008-route-files-by-content-not-by-extension) | Accepted |
| 009 | [Thread pool and polling for batch progress](#009-thread-pool-and-polling-for-batch-progress) | Accepted |
| 010 | [Batches kept in memory](#010-batches-kept-in-memory) | Accepted |
| 011 | [MIT licence for the project](#011-mit-licence-for-the-project) | Accepted |
| 012 | [Docker Compose to run everything](#012-docker-compose-to-run-everything) | Accepted |
| 013 | [Conventional Commits and feature branches](#013-conventional-commits-and-feature-branches) | Accepted |
| 014 | [requests as the HTTP client for Drive](#014-requests-as-the-http-client-for-drive) | Accepted |
| 015 | [Only the folder's direct content is listed](#015-only-the-folders-direct-content-is-listed) | Accepted |

---

## 001. Python and FastAPI for the backend

**Decision.** The backend is written in Python with FastAPI.

**Why.**
- The strongest open-source PDF and OCR tools (pypdf, pypdfium2, Tesseract bindings, most OCR models) are in Python.
- FastAPI validates every request with Pydantic and generates interactive API docs at `/docs`, with very little code.
- I already used FastAPI in a previous project (SmartWarehouse AI).

**Rejected.**
- Node.js: OCR and PDF libraries are weaker or wrap the same native tools.
- Django: too much framework for a few endpoints and one page.
- Flask: works, but request validation and API docs would have to be added by hand.

**Trade-off.** Python is slower than compiled languages, but the time is spent in PDF parsing and OCR, not in the web layer.

## 002. One plain HTML/JS page for the frontend

**Decision.** The UI is one HTML page with plain JavaScript and CSS, served by the backend.

**Why.**
- The brief asks for a single page covering the whole flow.
- No build step and no `node_modules`: the reviewer starts the project with one command.

**Rejected.** React or Vue: a second application to install and build for one screen.

**Trade-off.** No components or state library. Fine for one page, it would not scale to a large UI.

## 003. Google Drive API v3 with an API key

**Decision.** The folder is listed and files are downloaded through the official Drive API v3, authenticated with an API key only.

**Why.**
- It is the official and stable way to list a folder with name, type and size (`files.list` with `'<folderId>' in parents`).
- An API key is enough to read public files, which matches the brief: only public links, no OAuth login.

**Rejected.**
- OAuth login: the brief says no user login.
- Service account: the folder owner would have to share the folder with a robot email.
- Scraping Google's HTML pages (for example `embeddedfolderview`): no API contract, breaks when Google changes the page, and gives no file sizes.
- Google Apps Script: tied to a Google account and needs authorization.

**Trade-off.** The person running the app needs a free API key (2 minutes in Google Cloud Console). The setup steps are in the README.

## 004. pypdf for native PDFs

**Decision.** Text from PDFs that have a text layer is read with pypdf.

**Why.**
- BSD-3-Clause licence: free for closed-source commercial use.
- Pure Python, no system dependency.
- Reading the text layer is exact and fast, so OCR is not needed for these PDFs.

**Rejected.**
- PyMuPDF: AGPL-3.0 (or a paid licence). A closed-source service using it would have to publish its source code. This is the trap shown in the brief's licence table.
- pdfplumber / pdfminer.six (MIT): also allowed, but slower, and their strength (table geometry) is not needed here.

**Trade-off.** pypdf is not the fastest parser and can lose complex layouts (multi-column order). Acceptable for a proof of concept.

## 005. Scanned page detection and rendering with pypdfium2

**Decision.** A PDF page whose text layer has fewer than N non-space characters (20 by default, configurable) is treated as scanned. Only those pages are rendered to images with pypdfium2 and sent to OCR.

**Why.**
- Page by page detection handles mixed PDFs (some typed pages, some scans) and keeps the exact text of typed pages.
- pypdfium2 is Apache-2.0 / BSD-3-Clause and ships the PDFium binary, so there is nothing else to install.

**Rejected.**
- pdf2image: needs Poppler, which is GPL.
- PyMuPDF: AGPL (see 004).
- OCR on every page: slower, and less exact than the real text layer.

**Trade-off.** A typed page with almost no text (a cover page with one word) will also go through OCR. Harmless, just slower.

## 006. Tesseract as the default OCR engine

**Status.** Proposed. To be confirmed by our own measurement (see `benchmarks/`).

**Decision.** Images and scanned pages are read with Tesseract 5, using the `tessdata_best` language models for Arabic, French and English.

**Why.**
- **Arabic is the hard requirement.** French and English are read well by every engine. Arabic, and Arabic mixed with French in the same document (common in Tunisia), is where engines differ. Tesseract reads both in one call (`ara+fra`).
- **Independent Arabic benchmarks put Tesseract ahead of the other free CPU engines:**

  | Benchmark | Tesseract | EasyOCR | PaddleOCR |
  |---|---|---|---|
  | KITAB-Bench (ACL 2025, 8,809 samples, character error rate) | **0.54** | 0.58 | 0.79 |
  | SARD (2025, printed book pages, character error rate) | **0.16** | 0.60 | n/a |

  On KITAB-Bench it also does better than several large vision-language models (Qwen2.5-VL-7B 1.20, Surya 4.95).
- Apache-2.0 licence, self-hosted, runs on any CPU, one system package in Docker.
- `tessdata_best` models are more accurate than the default `tessdata_fast` models shipped by Linux packages, under the same licence.

**Rejected.**
- EasyOCR: lower Arabic accuracy, and it pulls PyTorch (large install).
- PaddleOCR / RapidOCR: better on Latin text, but weaker on Arabic in KITAB-Bench, the newest model generation dropped Arabic, and one model only handles one script family per call.
- Paid cloud APIs (Google Vision, Azure, Mistral OCR): accurate, but not open-source or self-hostable, which the brief prefers to avoid.
- Arabic-specialised vision models (Qari-OCR, Baseer, AIN): more accurate on hard documents, but they need a GPU. Listed as a next step.

**Trade-off.** Tesseract is weak on handwriting, very poor scans and complex tables. The optional engine in 007 covers part of that.

## 007. Optional vision-language OCR engine through Ollama

**Status.** Proposed. To be confirmed by our own measurement.

**Decision.** An optional second OCR engine calls a local vision-language model served by Ollama. Default model: GLM-OCR. It is off unless enabled in the configuration.

**Why.**
- Vision-language models are the main trend in document OCR in 2025-2026. They keep tables and layout.
- GLM-OCR: MIT licence, 0.9B parameters, ranked first on OmniDocBench v1.5 (94.62), available with `ollama pull glm-ocr`.
- I used GLM-OCR in production during my final-year internship (document pipeline at Essilor SIVO).
- Behind the same interface as Tesseract, so the model can be swapped (for example an Arabic model) without changing the pipeline.

**Rejected as the default.**
- Slow without a GPU (a few seconds per page on CPU).
- Its Arabic support is not published and it is absent from Arabic benchmarks.
- Can produce fluent but wrong text on blurry scans.
- Reviewers would need to run Ollama as well.

**Trade-off.** Two engines mean more code and configuration. Kept small by one shared interface.

## 008. Route files by content, not by extension

**Decision.** The pipeline is chosen from the first bytes of the file (`%PDF-`, PNG and JPEG signatures), then from the declared mime type.

**Why.** Extensions and mime types can be wrong. A PDF renamed `.png` still goes to the PDF parser.

**Rejected.** Trusting the extension only: one wrong name sends the file to the wrong pipeline.

**Trade-off.** None worth noting.

## 009. Thread pool and polling for batch progress

**Decision.** A batch is processed by a small thread pool. The page asks the server for the batch status every second.

**Why.**
- Downloading and OCR are blocking calls. Tesseract runs as a separate process, so threads give real parallelism here.
- Polling is simple, testable and works everywhere. It gives live per-file status (bonus item).

**Rejected.**
- Celery + Redis: two more services to run for a proof of concept.
- WebSockets / Server-Sent Events: better at scale, listed as a next step.

**Trade-off.** One request per second while a batch runs. Negligible locally.

## 010. Batches kept in memory

**Decision.** Batch state lives in the server's memory.

**Why.** Enough for a proof of concept, no database to install.

**Rejected.** SQLite or Postgres: needed for production, listed as a next step.

**Trade-off.** Batches are lost when the server restarts. Stated in the README limits.

## 011. MIT licence for the project

**Decision.** The project is released under the MIT licence.

**Why.**
- Short and permissive: anyone, including DI Xpertia, can reuse the code in a commercial product.
- Compatible with every dependency we chose (all permissive, see `LICENSES.md`).

**Rejected.**
- Apache-2.0: also fine, longer, adds patent terms we do not need.
- GPL / AGPL: would block closed-source reuse.

## 012. Docker Compose to run everything

**Decision.** `docker compose up --build` starts two containers:

- `api`: Python 3.12 slim + FastAPI + Tesseract 5 with the English, French and Arabic models (Debian packages).
- `web`: the Next.js "standalone" build, a small Node server. It forwards `/api/...` to the `api` container.

The API key is read from `.env` when the container starts, never copied into an image. The optional AI engine (007) uses an Ollama running on the host machine (`host.docker.internal:11434`), if there is one.

**Why.** Installing Tesseract and its language models by hand (especially on Windows) is the main setup risk for a reviewer: we hit it ourselves (only English was installed). With Docker the three languages are always there.

**Measured.** Inside Docker, the first run was about 10 times slower than on Windows and two pages hit the 60 s OCR limit. Cause: every Tesseract process starts one OpenMP thread per CPU core, and three files are processed in parallel. With `OMP_THREAD_LIMIT=1` (Tesseract's own advice for parallel runs) the same 11 files took 88 s instead of 247 s, with no timeout.

**Rejected.** Manual install only: kept as an alternative in the README, but not the main path. One single container for both: two images keep each one small and each runtime separate.

**Trade-off.** First build takes a few minutes and about 660 MB of images (398 MB api, 264 MB web). The web image leaves out `sharp` (image optimisation is off), see LICENSES.md.

## 013. Conventional Commits and feature branches

**Decision.** Commits follow Conventional Commits (`feat`, `fix`, `docs`, `refactor`, `test`, `chore`, with a scope). Each feature is built on its own branch and merged into `main`.

**Why.** Required by the brief, and it makes the history readable: each commit is one step of the story.

## 014. requests as the HTTP client for Drive

**Decision.** The Drive client calls the REST API directly with `requests`.

**Why.**
- Only two Drive calls are needed (read a folder or file, list children). A small direct client is easy to read and to test.
- `requests` is Apache-2.0, stable and known by everyone.
- The HTTP session is passed to the client as a parameter, so tests replace Google with fake responses: no network and no API key needed to run them.

**Rejected.**
- `google-api-python-client` (Google's official library): heavy for two calls, and it adds its own discovery layer.
- `httpx`: also fine, but its async support is not needed (downloads run in worker threads, see 009).

**Trade-off.** We map Drive's error responses ourselves. That mapping is covered by tests.

## 015. Only the folder's direct content is listed

**Decision.** Sub-folders are not opened. They are counted as ignored items.

**Why.** The brief asks for the folder's PDFs and images. Recursive listing adds paging per sub-folder, loops to protect against, and a tree in the UI. Not worth it for a proof of concept.

**Rejected.** Recursive listing: listed as a next step.

**Trade-off.** Files inside sub-folders are not shown. Stated in the README limits.

**Also out of scope.** Files shared before 2021 can require a "resource key" in addition to the link. Those are not supported.

---

## 016. Limits per file: pages, pixels and OCR time

**Decision.** Three limits, all set in `.env` (0 turns one off):

- `MAX_PDF_PAGES=100`: only the first 100 pages of a PDF are read, with a warning that gives the real page count.
- `MAX_IMAGE_MEGAPIXELS=50`: a larger image is refused from its header, before its pixels are decoded. A scanned page that would render larger is rendered at a lower resolution instead.
- `OCR_TIMEOUT_S=60`: Tesseract is stopped after 60 s on one image or page. That page is left empty and flagged for review, the rest of the file is kept.

**Why.** The files come from a folder we do not control. Without limits, one 2,000-page scan, one huge photo or one hostile file (a "decompression bomb": a small file that expands to billions of pixels) blocks a worker for minutes or exhausts memory, and the other files of the batch wait. 50 megapixels is far above an A4 page at 300 DPI (8.7 MP).

**Rejected.** Failing the whole file when one page times out: a 40-page scan would lose 39 good pages.

**Trade-off.** A very long PDF is only partly read. The warning says so, and the limit can be raised.

---

## 017. Small images are upscaled to 1200 px before OCR

**Decision.** Before Tesseract, an image whose shorter side is under 1200 pixels is enlarged (Lanczos, at most 4x) so that side reaches 1200 px (`OCR_MIN_SIDE_PX`). Scanned PDF pages, rendered at 300 DPI, are already larger and are not touched.

**Why.** Tesseract reads letters only a few pixels high badly. Our Arabic book pages are 612 x 792 px (72 DPI). Measured on 22 benchmark pages (Tesseract 5, psm 3) plus the French forms shrunk to 30 %, mean CER (lower is better) and word F1 (higher is better):

| Pages (median shorter side) | Off | 1200 px | 1600 px | 2000 px |
|---|---|---|---|---|
| KITAB Arabic books (612 px) | CER 0.295 | **0.075** | 0.081 | 0.084 |
| Misraj Arabic scans (1112 px) | CER 0.233 | **0.205** | 0.214 | 0.229 |
| XFUND French forms (2480 px) | CER 0.363 | 0.363 | 0.363 | 0.363 |
| XFUND forms at 30 % (744 px) | F1 0.656 | **0.797** | 0.793 | 0.788 |

1200 px is best on every set: Arabic book errors drop by 75 %, for about 0.3 s more per page. Larger targets are slower and slightly worse. Full-size pages are unchanged.

**Rejected.** A fixed 2x or 3x zoom: it would also enlarge pages that are already large, which costs time and here made results worse.

**Trade-off.** A small image takes a little more time and memory to read.

---

## 018. Arabic always first in the OCR language list

**Decision.** When Arabic is selected with other languages, the server sends it to Tesseract first (`ara+eng+fra`). The other languages keep their order.

**Why.** Tesseract leans on the first language. Found on the real test folder: the clean Arabic page "مرحبا بكم جميعا / اللغة العربية / لغة منتشرة في أنحاء العالم" came out with "Lin ja" instead of "مرحبا" when English was first. Measured on that page with the simple layout: CER 0.11 with `eng+fra+ara`, 0.00 with `ara+fra+eng`. On clean English, French and Dutch pages, Arabic first changed nothing. The web page sent languages in a fixed order (English first), so this was a real bug for Arabic documents.

**Also measured.** Adding Arabic at all slightly hurts a noisy Latin photo: on the receipt, "Singapore 319515" became "Singapore 5" with `ara` in the list. The page already says to pick only the languages present in the documents.

**Rejected.** Detecting the script automatically with Tesseract's OSD: it failed on the sparse Arabic page ("too few characters").

---

## Sources

- KITAB-Bench: https://github.com/mbzuai-oryx/KITAB-Bench and paper https://arxiv.org/abs/2502.14949
- SARD: https://arxiv.org/abs/2505.24600
- GLM-OCR: https://huggingface.co/zai-org/GLM-OCR
- OCR engines compared (2026): https://www.llamaindex.ai/agents/best-ocr-models-in-2026-accuracy-speed-and-cost-compared
- PaddleOCR comparison and licences: https://paddleocr.dev/compare
- Arabic OCR models (2026): https://misraj.ai/en/blogs/best-arabic-ocr-models-2026
- Qari-OCR: https://huggingface.co/NAMAA-Space/Qari-OCR-v0.3-VL-2B-Instruct
- Document parsers and licences: https://builderai.tools/blog/pdf-parsing-for-rag-mineru-docling-marker-compared
