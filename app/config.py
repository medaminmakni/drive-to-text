"""Settings, read from environment variables. A local .env file is loaded if present."""

import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    google_api_key: str | None = None
    max_file_size_mb: int = 25
    max_workers: int = 3
    request_timeout: float = 30
    ocr_default_lang: str = "eng"
    pdf_min_chars_per_page: int = 20
    ocr_dpi: int = 300
    ocr_min_side_px: int = 1200  # small images are upscaled to this before OCR (measured: decision 016)
    ocr_review_threshold: float = 70
    # Limits: files come from a folder we do not control, so one file must never block a worker.
    ocr_timeout_s: float = 60  # per image or scanned page; 0 = no limit
    max_pdf_pages: int = 100  # pages read per PDF; the rest are skipped with a warning
    max_image_megapixels: int = 50  # larger images (or decompression bombs) are refused
    tessdata_dir: str | None = None  # optional folder with other Tesseract models (e.g. tessdata_best)
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "glm-ocr"

    @property
    def max_file_size_bytes(self) -> int:
        return self.max_file_size_mb * 1024 * 1024


def load_settings() -> Settings:
    load_dotenv()

    def text(name: str) -> str | None:
        value = os.getenv(name, "").strip()
        return value or None

    def number(name: str, default: float, cast=int):
        value = text(name)
        return cast(value) if value is not None else default

    defaults = Settings()
    return Settings(
        google_api_key=text("GOOGLE_API_KEY"),
        max_file_size_mb=number("MAX_FILE_SIZE_MB", defaults.max_file_size_mb),
        max_workers=number("MAX_WORKERS", defaults.max_workers),
        request_timeout=number("REQUEST_TIMEOUT", defaults.request_timeout, float),
        ocr_default_lang=text("OCR_DEFAULT_LANG") or defaults.ocr_default_lang,
        pdf_min_chars_per_page=number("PDF_MIN_CHARS_PER_PAGE", defaults.pdf_min_chars_per_page),
        ocr_dpi=number("OCR_DPI", defaults.ocr_dpi),
        ocr_min_side_px=number("OCR_MIN_SIDE_PX", defaults.ocr_min_side_px),
        ocr_review_threshold=number("OCR_REVIEW_THRESHOLD", defaults.ocr_review_threshold, float),
        ocr_timeout_s=number("OCR_TIMEOUT_S", defaults.ocr_timeout_s, float),
        max_pdf_pages=number("MAX_PDF_PAGES", defaults.max_pdf_pages),
        max_image_megapixels=number("MAX_IMAGE_MEGAPIXELS", defaults.max_image_megapixels),
        tessdata_dir=text("TESSDATA_DIR"),
        ollama_url=text("OLLAMA_URL") or defaults.ollama_url,
        ollama_model=text("OLLAMA_MODEL") or defaults.ollama_model,
    )
