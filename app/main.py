"""FastAPI backend. Implements the contract in docs/API.md.

Run locally:  uvicorn app.main:app --reload
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.batches import BatchManager
from app.config import Settings, load_settings
from app.drive.client import DriveApiClient, MissingApiKeyClient
from app.drive.errors import DriveError, DriveServiceError, FolderNotAccessibleError, InvalidDriveLinkError
from app.drive.links import extract_folder_id
from app.extraction.models import ExtractOptions, PageMode
from app.extraction.ocr import SUPPORTED_LANGUAGES, OcrEngine, TesseractOcr, parse_languages
from app.extraction.pipeline import Extractor
from app.extraction.vlm import OllamaVisionOcr

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

# Drive errors carry a user-facing message; this maps each kind to an HTTP status.
ERROR_STATUS = {InvalidDriveLinkError: 400, FolderNotAccessibleError: 404, DriveServiceError: 502}
PAGE_MODE_LABELS = {
    PageMode.AUTO: "Automatic layout",
    PageMode.SINGLE_BLOCK: "Simple layout (one column): forms, letters, certificates",
}


class FolderRequest(BaseModel):
    url: str = Field(description="Public Google Drive folder link")


class BatchRequest(BaseModel):
    url: str = Field(description="Public Google Drive folder link")
    file_ids: list[str] = Field(min_length=1, description="Ids of the files to process")
    lang: str | None = Field(default=None, description='OCR languages, e.g. "eng" or "ara+fra"')
    page_mode: PageMode = PageMode.AUTO
    engine: str | None = None


def default_engines(settings: Settings) -> dict[str, OcrEngine]:
    tesseract = TesseractOcr(settings.tessdata_dir)
    vision = OllamaVisionOcr(settings.ollama_model, settings.ollama_url)
    return {tesseract.name: tesseract, vision.name: vision}


def create_app(settings: Settings | None = None, drive=None, engines: dict[str, OcrEngine] | None = None) -> FastAPI:
    """Build the app. Tests pass fake Drive clients and OCR engines (dependency injection)."""
    settings = settings or load_settings()
    if drive is None:
        drive = (
            DriveApiClient(settings.google_api_key, settings.request_timeout)
            if settings.google_api_key
            else MissingApiKeyClient()
        )
    engines = engines or default_engines(settings)
    default_engine = next(iter(engines))
    extractor = Extractor(engines, settings.pdf_min_chars_per_page, settings.ocr_dpi, settings.ocr_review_threshold)
    batches = BatchManager(drive, extractor, settings.max_file_size_bytes, settings.max_workers)

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        yield
        batches.shutdown()

    app = FastAPI(title="Drive-to-Text API", version="0.1.0", lifespan=lifespan)

    @app.exception_handler(DriveError)
    async def drive_error(_: Request, exc: DriveError) -> JSONResponse:
        status = next((code for kind, code in ERROR_STATUS.items() if isinstance(exc, kind)), 502)
        return JSONResponse(status_code=status, content={"detail": str(exc)})

    def list_folder(url: str):
        return drive.list_folder(extract_folder_id(url))

    @app.get("/api/health")
    def health() -> dict:
        return {"status": "ok"}

    @app.get("/api/config")
    def config() -> dict:
        tesseract = engines.get("tesseract")
        installed = tesseract.installed_languages() if isinstance(tesseract, TesseractOcr) else list(SUPPORTED_LANGUAGES)
        return {
            "engines": [
                {
                    "name": engine.name,
                    "label": engine.label,
                    "available": engine.is_available(),
                    "reliable_for_arabic": engine.reliable_for_arabic,
                }
                for engine in engines.values()
            ],
            "default_engine": default_engine,
            "languages": [{"code": code, "label": SUPPORTED_LANGUAGES[code]} for code in installed],
            "default_language": settings.ocr_default_lang,
            "page_modes": [{"value": mode.value, "label": label} for mode, label in PAGE_MODE_LABELS.items()],
            "max_file_size_mb": settings.max_file_size_mb,
        }

    @app.post("/api/folders")
    def folder(request: FolderRequest) -> dict:
        listing = list_folder(request.url)
        return {
            "folder_id": listing.folder_id,
            "folder_name": listing.folder_name,
            "skipped": listing.skipped,
            "files": [file.to_dict() for file in listing.files],
        }

    @app.post("/api/batches", status_code=202)
    def start_batch(request: BatchRequest) -> dict:
        try:
            lang = parse_languages(request.lang, settings.ocr_default_lang)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        engine_name = request.engine or default_engine
        engine = engines.get(engine_name)
        if engine is None or not engine.is_available():
            raise HTTPException(status_code=400, detail=f"OCR engine '{engine_name}' is not available.")

        # List the folder again: only files that really belong to it are processed.
        listing = list_folder(request.url)
        by_id = {file.id: file for file in listing.files}
        if any(file_id not in by_id for file_id in request.file_ids):
            raise HTTPException(status_code=400, detail="Some selected files are no longer in this folder.")

        selected = [by_id[file_id] for file_id in dict.fromkeys(request.file_ids)]
        options = ExtractOptions(lang=lang, page_mode=request.page_mode, engine=engine_name)
        batch = batches.start(listing.folder_id, listing.folder_name, selected, options)
        return batches.snapshot(batch.id)

    @app.get("/api/batches/{batch_id}")
    def batch_status(batch_id: str) -> dict:
        state = batches.snapshot(batch_id)
        if state is None:
            raise HTTPException(status_code=404, detail="Batch not found.")
        return state

    @app.get("/api/batches/{batch_id}/export")
    def export_batch(batch_id: str) -> JSONResponse:
        return JSONResponse(
            content=batch_status(batch_id),
            headers={"Content-Disposition": f'attachment; filename="drive-to-text-{batch_id}.json"'},
        )

    return app


app = create_app()
