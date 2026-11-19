# Decision log

Each technical choice, why it was made, what was rejected and what it costs.
**Measured** means our own benchmark or test backs it ([benchmarks/README.md](../benchmarks/README.md)).

| # | Decision | |
|---|---|---|
| 001 | [Python and FastAPI for the backend](#001-python-and-fastapi-for-the-backend) | |
| 002 | [Next.js and TypeScript for the web page](#002-nextjs-and-typescript-for-the-web-page) | revised |
| 003 | [Google Drive API v3 with an API key](#003-google-drive-api-v3-with-an-api-key) | |
| 004 | [pypdf for native PDFs](#004-pypdf-for-native-pdfs) | |
| 005 | [Scanned pages detected per page, rendered with pypdfium2](#005-scanned-pages-detected-per-page-rendered-with-pypdfium2) | |
| 006 | [Tesseract as the OCR engine](#006-tesseract-as-the-ocr-engine) | measured |
| 007 | [Optional AI OCR engine through Ollama](#007-optional-ai-ocr-engine-through-ollama) | measured |
| 008 | [Route files by content, not by extension](#008-route-files-by-content-not-by-extension) | |
| 009 | [Thread pool and polling for progress](#009-thread-pool-and-polling-for-progress) | |
| 010 | [Batches kept in memory](#010-batches-kept-in-memory) | |
| 011 | [MIT licence](#011-mit-licence) | |
| 012 | [Docker Compose](#012-docker-compose) | measured |
| 013 | [Conventional Commits and feature branches](#013-conventional-commits-and-feature-branches) | |
| 014 | [requests as the HTTP client for Drive](#014-requests-as-the-http-client-for-drive) | |
| 015 | [Only the folder's direct content is listed](#015-only-the-folders-direct-content-is-listed) | |
| 016 | [Limits per file: pages, pixels, OCR time](#016-limits-per-file-pages-pixels-ocr-time) | |
| 017 | [Small images upscaled to 1200 px before OCR](#017-small-images-upscaled-to-1200-px-before-ocr) | measured |
| 018 | [Arabic always first in the language list](#018-arabic-always-first-in-the-language-list) | measured |

---

## 001. Python and FastAPI for the backend

- **Why:** the best open-source PDF and OCR tools are in Python. FastAPI validates requests (Pydantic) and generates API docs at `/docs` with very little code.
- **Rejected:** Node.js (weaker PDF/OCR libraries), Django (too much for a few endpoints), Flask (validation and docs by hand).
- **Trade-off:** Python is slower, but the time is spent in PDF parsing and OCR, not in the web layer.

## 002. Next.js and TypeScript for the web page

- **Decision:** a Next.js 16 page (React 19, TypeScript, CSS Modules) in `web/`. Next.js forwards `/api/...` to FastAPI, so the browser sees one address and no CORS setup is needed.
- **Why:** the page has real state (selection, options, a batch polled every second, results). Typed components keep each part small, and the API types follow `docs/API.md`.
- **Revised:** the first plan was one plain HTML/JS page. It was changed when the page state grew.
- **Rejected:** plain HTML/JS (no types, one large script), Vue or Svelte (fine, but React is what I know best).
- **Trade-off:** a Node build step. Docker hides it.

## 003. Google Drive API v3 with an API key

- **Why:** the official way to list a folder with names, types and sizes. An API key is enough for public files, which matches the brief (public links, no OAuth).
- **Rejected:** OAuth (the brief excludes login), a service account (the owner would have to share the folder with it), scraping Google's pages (no contract, no sizes), Apps Script (needs a Google account).
- **Trade-off:** the person running the app creates a free API key (steps in the README).

## 004. pypdf for native PDFs

- **Why:** BSD licence, pure Python, exact text from the PDF's text layer.
- **Rejected:** PyMuPDF (AGPL: a closed-source service would have to publish its code or buy a licence), pdfplumber (MIT, but slower and its table features are not needed).
- **Trade-off:** complex layouts (several columns) may come out in the wrong order.

## 005. Scanned pages detected per page, rendered with pypdfium2

- **Decision:** a PDF page with fewer than 20 non-space characters in its text layer is treated as scanned. Only those pages are rendered (300 DPI) and sent to OCR.
- **Why:** a PDF can mix typed and scanned pages. Typed pages keep their exact text. pypdfium2 is Apache/BSD and needs nothing else installed.
- **Rejected:** pdf2image (needs Poppler, GPL), OCR on every page (slower and less exact).
- **Trade-off:** a typed page with almost no text (a cover page) also goes through OCR. Harmless, only slower.

## 006. Tesseract as the OCR engine

- **Why:** Arabic, and Arabic mixed with French, is where engines differ. Public Arabic benchmarks rank Tesseract first among free CPU engines (KITAB-Bench character error rate: Tesseract 0.54, EasyOCR 0.58, PaddleOCR 0.79). It reads several languages in one call (`ara+fra`), is Apache-2.0 and runs on any CPU.
- **Measured:** CER 0.08 on Arabic book pages (with 017), word F1 0.77 on scanned French forms, about 1.4 s per page on a CPU. The more accurate `tessdata_best` models were only slightly better and 35 to 50% slower, so the standard models are kept.
- **Rejected:** EasyOCR (weaker on Arabic, pulls PyTorch), PaddleOCR (weaker on Arabic), paid cloud APIs (not self-hosted), Arabic AI models (need a GPU; listed as a next step).
- **Trade-off:** weak on handwriting, poor photos and complex tables.

## 007. Optional AI OCR engine through Ollama

- **Decision:** a second engine calls a local AI model (GLM-OCR, MIT) through Ollama. It appears only when Ollama is running. Its Arabic pages are always flagged for review.
- **Why:** AI models keep layout and tables and read clean French and English perfectly. The engine sits behind the same interface as Tesseract, so models can be swapped.
- **Measured:** it invents Arabic text that is not on the page (CER 5.2 on Arabic book pages), finds under a fifth of the words on scanned French forms, and takes about 89 s per page on a laptop GPU.
- **Rejected as default:** too slow without a GPU, unreliable on Arabic, and reviewers would have to install Ollama.

## 008. Route files by content, not by extension

- **Decision:** the first bytes decide (`%PDF-`, PNG and JPEG signatures), then the declared type.
- **Why:** names and types can be wrong: a PDF renamed `.png` still goes to the PDF parser.

## 009. Thread pool and polling for progress

- **Decision:** 3 worker threads process a batch; the page asks for its status every second.
- **Why:** downloads and OCR are blocking, and Tesseract runs as a separate process, so threads give real parallelism. Polling is simple, testable and works everywhere.
- **Rejected:** Celery + Redis (two more services), WebSockets or Server-Sent Events (better at scale; next step).

## 010. Batches kept in memory

- **Why:** enough for a proof of concept, no database to install.
- **Trade-off:** batches are lost when the server restarts. A database is a next step.

## 011. MIT licence

- **Why:** short and permissive, so the code can be reused in a commercial product. Compatible with every dependency (see [LICENSES.md](../LICENSES.md)).
- **Rejected:** Apache-2.0 (fine, longer), GPL/AGPL (would block closed-source reuse).

## 012. Docker Compose

- **Decision:** `docker compose up --build` starts two containers. `api` holds Python, FastAPI and Tesseract 5 with the English, French and Arabic models. `web` holds the Next.js server. The API key is read from `.env` at start, never copied into an image.
- **Why:** installing Tesseract and its language models by hand is the main setup risk (on Windows, only English was installed by default).
- **Measured:** the first Docker run was 10 times slower than on Windows. Each Tesseract process started one thread per CPU core while 3 files ran in parallel. With `OMP_THREAD_LIMIT=1` the same 11 files took 88 s instead of 247 s.
- **Trade-off:** first build takes a few minutes; images are 398 MB (api) and 264 MB (web).

## 013. Conventional Commits and feature branches

- **Why:** required by the brief, and the history reads as a list of small, explained steps. Each feature is built on its own branch and merged through a pull request.

## 014. requests as the HTTP client for Drive

- **Why:** only two Drive calls are needed. A small direct client is easy to read, and its HTTP session is a parameter, so tests replace Google with fake answers (no network, no key).
- **Rejected:** `google-api-python-client` (heavy for two calls), `httpx` (its async support is not needed).
- **Trade-off:** we map Drive's error answers ourselves. The mapping is tested.

## 015. Only the folder's direct content is listed

- **Why:** the brief asks for the folder's PDFs and images. Opening sub-folders adds paging per folder, loop protection and a tree in the UI.
- **Trade-off:** files in sub-folders are not shown (they are counted as skipped). Next step.

## 016. Limits per file: pages, pixels, OCR time

- **Decision:** at most 100 pages per PDF (with a warning giving the real count), images up to 50 megapixels (checked before decoding), 60 s of OCR per page (that page is left empty and flagged; the rest of the file is kept). All set in `.env`.
- **Why:** files come from a folder we do not control. One 2,000-page scan or one hostile image (a "decompression bomb") would block a worker or fill the memory.
- **Rejected:** failing the whole file when one page times out (a 40-page scan would lose 39 good pages).

## 017. Small images upscaled to 1200 px before OCR

- **Decision:** an image whose shorter side is under 1200 px is enlarged to 1200 px (at most 4x) before Tesseract. Scanned PDF pages are already larger.
- **Why:** Tesseract reads letters only a few pixels high badly. Measured (CER, lower is better):

  | Pages (median shorter side) | No upscaling | 1200 px | 1600 px | 2000 px |
  |---|---|---|---|---|
  | Arabic book pages (612 px) | 0.295 | **0.075** | 0.081 | 0.084 |
  | Arabic scans (1112 px) | 0.233 | **0.205** | 0.214 | 0.229 |
  | French forms (2480 px) | 0.363 | 0.363 | 0.363 | 0.363 |

  1200 px is best everywhere: Arabic book errors drop by 75% for about 0.3 s more per page. Large pages are unchanged.
- **Rejected:** a fixed 2x or 3x zoom (slower on large pages, and worse here).

## 018. Arabic always first in the language list

- **Decision:** when Arabic is chosen with other languages, it is sent to Tesseract first (`ara+eng+fra`).
- **Why:** Tesseract leans on the first language. On our real Arabic test page, English first turned the first Arabic word into Latin letters (CER 0.11). Arabic first gave a perfect result (CER 0.00) and changed nothing on English and French pages.
- **Rejected:** detecting the script automatically (Tesseract's detection failed on short Arabic text).

---

## Sources

- KITAB-Bench: https://github.com/mbzuai-oryx/KITAB-Bench, paper https://arxiv.org/abs/2502.14949
- SARD: https://arxiv.org/abs/2505.24600
- GLM-OCR: https://huggingface.co/zai-org/GLM-OCR
- OCR engines compared (2026): https://www.llamaindex.ai/agents/best-ocr-models-in-2026-accuracy-speed-and-cost-compared
- PaddleOCR comparison and licences: https://paddleocr.dev/compare
- Arabic OCR models (2026): https://misraj.ai/en/blogs/best-arabic-ocr-models-2026
- Qari-OCR: https://huggingface.co/NAMAA-Space/Qari-OCR-v0.3-VL-2B-Instruct
- Document parsers and licences: https://builderai.tools/blog/pdf-parsing-for-rag-mineru-docling-marker-compared
