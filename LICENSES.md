# Third-party licences

The project itself is released under the **MIT licence** (see [LICENSE](LICENSE)).

This file lists every library, tool, model and dataset the project uses, its licence, and whether it can be used in a **closed-source commercial product**. Versions are the ones actually installed on 19 Nov 2026: Python packages and system packages read inside the Docker images, Node packages from `web/package-lock.json`.

**Summary.** Everything that ships with the app is under a permissive licence (MIT, BSD, Apache-2.0, ISC, PSF). Two components have weak, file-level conditions and are explained below (`certifi`, `caniuse-lite`). No GPL or AGPL component is used. The one LGPL component that Next.js would install (`libvips`, through `sharp`) is not needed and is left out of the Docker image.

## 1. Backend (Python), shipped in the `api` image

Direct dependencies (`requirements.txt`):

| Dependency | Version | Licence | Commercial use | Note |
|---|---|---|---|---|
| fastapi | 0.165.0 | MIT | Yes | Web API framework |
| uvicorn | 0.54.0 | BSD-3-Clause | Yes | ASGI server |
| pypdf | 7.1.1 | BSD-3-Clause | Yes | Reads the text layer of PDFs (decision 004) |
| pypdfium2 | 5.15.2 | Apache-2.0 or BSD-3-Clause | Yes | Renders scanned pages. Bundles Google's PDFium (BSD-3-Clause) and its permissive libraries: keep the notices in the wheel's `BUILD_LICENSES/` if the app is redistributed as a binary |
| pytesseract | 0.3.13 | Apache-2.0 | Yes | Calls the Tesseract program. Keep its NOTICE if redistributed |
| pillow | 13.0.0 | MIT-CMU (HPND) | Yes | Opens and resizes images |
| requests | 2.34.2 | Apache-2.0 | Yes | Google Drive API calls (decision 014) |
| python-dotenv | 1.2.4 | BSD-3-Clause | Yes | Reads `.env` |

Installed with them (transitive):

| Dependency | Version | Licence | Commercial use | Note |
|---|---|---|---|---|
| starlette | 1.10.0 | BSD-3-Clause | Yes | Through FastAPI |
| pydantic | 2.14.4 | MIT | Yes | Through FastAPI |
| pydantic_core | 2.50.5 | MIT | Yes | |
| anyio | 4.16.0 | MIT | Yes | |
| annotated-doc | 0.0.7 | MIT | Yes | |
| annotated-types | 0.8.0 | MIT | Yes | |
| typing-inspection | 0.4.5 | MIT | Yes | |
| typing_extensions | 4.16.0 | PSF-2.0 | Yes | Permissive |
| opentelemetry-api | 1.45.2 | Apache-2.0 | Yes | |
| click | 8.5.1 | BSD-3-Clause | Yes | Through uvicorn |
| h11 | 0.16.0 | MIT | Yes | Through uvicorn |
| urllib3 | 2.8.0 | MIT | Yes | Through requests |
| idna | 3.20 | BSD-3-Clause | Yes | Through requests |
| charset-normalizer | 3.5.2 | MIT | Yes | Through requests |
| certifi | 2026.10.23 | MPL-2.0 | Yes | Weak, **file-level** copyleft: only modified MPL files must be shared. Used unmodified (it is the list of trusted certificates), so nothing else is affected |
| packaging | 26.3 | Apache-2.0 or BSD-2-Clause | Yes | Through pytesseract |

## 2. OCR engine and language models, shipped in the `api` image

| Dependency | Version | Licence | Commercial use | Note |
|---|---|---|---|---|
| Tesseract OCR (`tesseract-ocr`, `libtesseract5`) | 5.3.0 | Apache-2.0 | Yes | Called as a separate program. Keep the NOTICE file when redistributing |
| Leptonica (`liblept5`) | 1.82.0 | BSD-2-Clause (Leptonica licence) | Yes | Image library used by Tesseract |
| Language models `eng`, `fra`, `ara` (`tesseract-ocr-*`) | 4.1.0 (tessdata_fast) | Apache-2.0 | Yes | Debian packages. `tessdata`, `tessdata_fast` and `tessdata_best` are all Apache-2.0 |
| Python | 3.12.16 | PSF-2.0 | Yes | Base image `python:3.12-slim-bookworm` |
| Debian 12 base system | bookworm | Mixed (mostly GPL and LGPL system tools) | Yes | Standard OS packages, used as-is, not linked into or modified by the app. Usual situation for any Debian-based image |

## 3. Web page (Node), shipped in the `web` image

| Dependency | Version | Licence | Commercial use | Note |
|---|---|---|---|---|
| next | 16.4.6 | MIT | Yes | Framework and server (decision 002) |
| react | 19.3.0 | MIT | Yes | |
| react-dom | 19.3.0 | MIT | Yes | |
| @next/env | 16.4.6 | MIT | Yes | Through Next.js |
| styled-jsx | 5.1.6 | MIT | Yes | Through Next.js |
| client-only | 0.0.1 | MIT | Yes | Through Next.js |
| scheduler | 0.28.0 | MIT | Yes | Through React |
| @swc/helpers | 0.5.23 | Apache-2.0 | Yes | Through Next.js |
| baseline-browser-mapping | 2.11.38 | Apache-2.0 | Yes | Through Next.js |
| caniuse-lite | 1.0.30001826 | CC-BY-4.0 | Yes | Browser-support data used by Next.js. CC-BY only asks for attribution: this line is the attribution |
| postcss | 8.5.23 | MIT | Yes | Through Next.js |
| nanoid | 3.3.20 | MIT | Yes | |
| picocolors | 1.1.1 | ISC | Yes | |
| source-map-js | 1.2.2 | BSD-3-Clause | Yes | |
| tslib | 2.9.1 | 0BSD | Yes | |
| detect-libc, semver | 2.1.2, 7.8.6 | Apache-2.0, ISC | Yes | Through `sharp` (see below) |
| Node.js | 22.23.5 | MIT | Yes | Base image `node:22-alpine` |

**`sharp` 0.35.5 (Apache-2.0) and its `libvips` 1.3.4 binary (LGPL-3.0-or-later): not shipped.** Next.js installs them as an optional dependency for its image optimisation. This page has no photos to resize, so optimisation is turned off (`images.unoptimized` in `web/next.config.ts`) and the Docker build removes `sharp`, `@img/*` and `@emnapi/*` before the final image (27 MB less). When running `npm install` locally they are still downloaded but never loaded. Even if they were used, LGPL allows commercial use of an unmodified library that is loaded dynamically and can be replaced, which is how `sharp` loads `libvips`.

The page uses system fonts and its own inline SVG icons: no font, icon or CSS library.

## 4. Development and test tools (not shipped)

| Dependency | Version | Licence | Commercial use | Note |
|---|---|---|---|---|
| pytest | 9.0.3 | MIT | Yes | Tests |
| httpx | 0.28.1 | BSD-3-Clause | Yes | FastAPI test client |
| ruff | 0.17.5 | MIT | Yes | Python linter |
| typescript | 5.9.3 | Apache-2.0 | Yes | |
| eslint | 9.39.5 | MIT | Yes | |
| eslint-config-next | 16.4.6 | MIT | Yes | |
| @types/node, @types/react, @types/react-dom | 20.19.43, 19.3.0, 19.3.0 | MIT | Yes | Type definitions |

## 5. Optional AI OCR engine (off by default, not installed by the project)

| Dependency | Version | Licence | Commercial use | Note |
|---|---|---|---|---|
| Ollama | any recent | MIT | Yes | Separate program, installed by the user |
| GLM-OCR model (`ollama pull glm-ocr`) | 0.9B | MIT | Yes | Not recommended for Arabic (it invents text, see `benchmarks/README.md`) |

## 6. Benchmark only (`benchmarks/`, not shipped)

| Dependency / dataset | Version | Licence | Commercial use | Note |
|---|---|---|---|---|
| Generated samples (`benchmarks/samples/`) | - | MIT (this project) | Yes | Made for this project |
| EasyOCR (optional engine) | 1.7+ | Apache-2.0 | Yes | Not installed by default (pulls PyTorch) |
| Playwright (optional, `make_samples.py`) | 1.40+ | Apache-2.0 | Yes | Renders Arabic text for the generated samples |
| Misraj-DocOCR pages | 2025 | Apache-2.0 | Yes | Downloaded on demand, not committed |
| KITAB-Bench (Hindawi subset) | 2025 | Repository MIT, data licence not stated | Evaluation only | Downloaded on demand, not committed |
| XFUND (French) | 1.0 | CC BY-NC-SA 4.0 | **No** | Evaluation only, never redistributed or shipped |
| FUNSD | 2019 | Non-commercial research | **No** | Evaluation only, never redistributed or shipped |

These datasets are only used to measure engines on a developer's machine. Nothing from them is part of the app, the images or the repository.

## 7. Alternatives rejected for licence reasons

| Alternative | Licence | Why it was not used | Used instead |
|---|---|---|---|
| PyMuPDF (fitz) | AGPL-3.0 or paid licence | AGPL would force a closed-source product to publish its source or buy a licence | pypdf + pypdfium2 |
| pdf2image + Poppler | MIT wrapper around GPL-2.0 Poppler | Rendering would depend on GPL binaries | pypdfium2 (BSD/Apache) |
| MinerU | AGPL-3.0 | Same AGPL problem; also heavy for a POC | Own small pipeline |
| DocLayout-YOLO (Ultralytics) | AGPL-3.0 | Same AGPL problem | PP-DocLayoutV3 (Apache-2.0) is the planned layout model (next steps) |
| sharp / libvips image optimisation | LGPL-3.0 | Not needed by the page | Turned off and left out of the image |
| Google Cloud Vision, AWS Textract, Azure AI | Proprietary, paid | The brief prefers self-hosted tools; documents would leave the machine | Tesseract, locally |
