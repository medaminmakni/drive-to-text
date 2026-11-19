# Third-party licences

The project is under the **MIT licence** ([LICENSE](LICENSE)).

**Summary.** Everything shipped with the app is under a permissive licence (MIT, BSD, Apache-2.0, ISC, PSF), so it can be used in a closed-source commercial product. No GPL or AGPL component is used. Two components have light conditions, explained below (`certifi`, `caniuse-lite`). The one LGPL component Next.js would install (`sharp` / `libvips`) is left out.

Versions are the ones installed on 19 Nov 2026: read inside the Docker images (Python and system packages) and from `web/package-lock.json` (Node).

## 1. Backend (Python), shipped in the `api` image

| Dependency | Version | Licence | Commercial use | Note |
|---|---|---|---|---|
| fastapi | 0.165.0 | MIT | Yes | Web API framework |
| uvicorn | 0.54.0 | BSD-3-Clause | Yes | Server |
| pypdf | 7.1.1 | BSD-3-Clause | Yes | Reads the text layer of PDFs |
| pypdfium2 | 5.15.2 | Apache-2.0 or BSD-3-Clause | Yes | Renders scanned pages (bundles Google's PDFium, BSD-3-Clause) |
| pytesseract | 0.3.13 | Apache-2.0 | Yes | Calls Tesseract |
| pillow | 13.0.0 | MIT-CMU (HPND) | Yes | Opens and resizes images |
| requests | 2.34.2 | Apache-2.0 | Yes | Google Drive API calls |
| python-dotenv | 1.2.4 | BSD-3-Clause | Yes | Reads `.env` |
| certifi | 2026.10.23 | MPL-2.0 | Yes | Installed by requests. File-level copyleft: only modified MPL files must be shared. Used unmodified |

Other packages installed with them, all usable commercially:

| Licence | Packages |
|---|---|
| MIT | pydantic 2.14.4, pydantic_core 2.50.5, anyio 4.16.0, annotated-doc 0.0.7, annotated-types 0.8.0, typing-inspection 0.4.5, h11 0.16.0, urllib3 2.8.0, charset-normalizer 3.5.2 |
| BSD-3-Clause | starlette 1.10.0, click 8.5.1, idna 3.20 |
| Apache-2.0 | opentelemetry-api 1.45.2, packaging 26.3 (or BSD-2-Clause) |
| PSF-2.0 | typing_extensions 4.16.0 |

## 2. OCR engine and system, shipped in the `api` image

| Dependency | Version | Licence | Commercial use | Note |
|---|---|---|---|---|
| Tesseract OCR | 5.3.0 | Apache-2.0 | Yes | Runs as a separate program |
| Leptonica | 1.82.0 | BSD-2-Clause | Yes | Image library used by Tesseract |
| Language models `eng`, `fra`, `ara` | 4.1.0 (tessdata_fast) | Apache-2.0 | Yes | Debian packages |
| Python | 3.12.16 | PSF-2.0 | Yes | Base image `python:3.12-slim-bookworm` |
| Debian 12 | bookworm | Mixed (mostly GPL/LGPL tools) | Yes | Standard OS, used as-is, not linked into the app |

## 3. Web page (Node), shipped in the `web` image

| Dependency | Version | Licence | Commercial use | Note |
|---|---|---|---|---|
| next | 16.4.6 | MIT | Yes | Framework and server |
| react, react-dom | 19.3.0 | MIT | Yes | |
| caniuse-lite | 1.0.30001826 | CC-BY-4.0 | Yes | Browser data used by Next.js. Only asks for attribution: this line is it |
| Node.js | 22.23.5 | MIT | Yes | Base image `node:22-alpine` |

Other packages installed with them, all usable commercially:

| Licence | Packages |
|---|---|
| MIT | @next/env 16.4.6, styled-jsx 5.1.6, client-only 0.0.1, scheduler 0.28.0, postcss 8.5.23, nanoid 3.3.20 |
| Apache-2.0 | @swc/helpers 0.5.23, baseline-browser-mapping 2.11.38, detect-libc 2.1.2 |
| ISC | picocolors 1.1.1, semver 7.8.6 |
| BSD-3-Clause / 0BSD | source-map-js 1.2.2 / tslib 2.9.1 |

**Not shipped: `sharp` 0.35.5 and its `libvips` binary (LGPL-3.0).** Next.js installs them for image optimisation. The page has no photos to resize, so optimisation is off (`images.unoptimized`) and the Docker build removes them. The page uses system fonts and its own SVG icons: no font, icon or CSS library.

## 4. Development tools (not shipped)

| Dependency | Version | Licence | Commercial use |
|---|---|---|---|
| pytest | 9.0.3 | MIT | Yes |
| httpx | 0.28.1 | BSD-3-Clause | Yes |
| ruff | 0.17.5 | MIT | Yes |
| typescript | 5.9.3 | Apache-2.0 | Yes |
| eslint, eslint-config-next | 9.39.5, 16.4.6 | MIT | Yes |
| @types/node, @types/react, @types/react-dom | 20.19.43, 19.3.0, 19.3.0 | MIT | Yes |

## 5. Optional AI OCR engine (off by default, not installed)

| Dependency | Version | Licence | Commercial use | Note |
|---|---|---|---|---|
| Ollama | any recent | MIT | Yes | Installed by the user |
| GLM-OCR model | 0.9B | MIT | Yes | Not recommended for Arabic (see benchmarks) |

## 6. Benchmark only (`benchmarks/`, not shipped)

| Dependency / dataset | Licence | Commercial use | Note |
|---|---|---|---|
| Generated samples | MIT (this project) | Yes | |
| EasyOCR 1.7+, Playwright 1.40+ | Apache-2.0 | Yes | Optional |
| Misraj-DocOCR pages | Apache-2.0 | Yes | Downloaded on demand |
| KITAB-Bench (Hindawi subset) | Repository MIT, data not stated | Evaluation only | Downloaded on demand |
| XFUND (French) | CC BY-NC-SA 4.0 | **No** | Evaluation only, never committed or shipped |
| FUNSD | Non-commercial research | **No** | Evaluation only, never committed or shipped |

## 7. Rejected because of their licence

| Alternative | Licence | Problem | Used instead |
|---|---|---|---|
| PyMuPDF | AGPL-3.0 or paid | A closed-source service would have to publish its code or buy a licence | pypdf + pypdfium2 |
| pdf2image + Poppler | GPL-2.0 | Rendering would depend on GPL binaries | pypdfium2 |
| MinerU, DocLayout-YOLO | AGPL-3.0 | Same AGPL problem | Own pipeline; PP-DocLayoutV3 (Apache-2.0) planned |
| sharp / libvips | LGPL-3.0 | Not needed | Turned off and removed |
| Google Vision, AWS Textract, Azure AI | Proprietary, paid | Not self-hosted; documents leave the machine | Tesseract, locally |
