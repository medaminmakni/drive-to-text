"""Orchestrates extraction: the only place that knows the full routing.

    PDF   -> pypdf text layer, page by page
             page with < min_chars characters -> render (pypdfium2) -> OCR
    image -> OCR
Each OCR page gets a confidence and, when needed, a "needs review" flag.

Limits (files come from a folder we do not control): at most ``max_pages`` pages per PDF,
at most ``max_pixels`` per image or rendered page, and the OCR engine's own time limit per
page. A page that hits the time limit is left empty and flagged; the rest of the file is kept.
"""

from io import BytesIO

from PIL import Image, UnidentifiedImageError

from app.extraction.models import (
    ExtractionError,
    ExtractionResult,
    ExtractOptions,
    Method,
    OcrTimeoutError,
    PageResult,
    ReviewReason,
)
from app.extraction.ocr import OcrEngine, parse_languages
from app.extraction.pdf import is_scanned, read_text_layer
from app.extraction.render import render_pages
from app.extraction.routing import Pipeline, choose_pipeline

ARABIC_AI_WARNING = (
    "AI OCR engines can invent Arabic text that is not on the page. "
    "Pages in Arabic read by this engine are flagged for review."
)


class Extractor:
    def __init__(
        self,
        engines: dict[str, OcrEngine],
        min_chars_per_page: int = 20,
        ocr_dpi: int = 300,
        review_threshold: float = 70.0,
        max_pages: int = 100,
        max_pixels: int = 50_000_000,
    ):
        if not engines:
            raise ValueError("At least one OCR engine is required.")
        self.engines = engines
        self.min_chars_per_page = min_chars_per_page
        self.ocr_dpi = ocr_dpi
        self.review_threshold = review_threshold
        self.max_pages = max_pages
        self.max_pixels = max_pixels

    def extract(self, data: bytes, mime_type: str = "", options: ExtractOptions | None = None) -> ExtractionResult:
        options = options or ExtractOptions()
        lang = parse_languages(options.lang)  # raises ValueError on unknown codes
        engine = self.engines.get(options.engine)
        if engine is None:
            raise ExtractionError(f"Unknown OCR engine '{options.engine}'.")

        warnings: list[str] = []
        if choose_pipeline(data, mime_type) is Pipeline.PDF:
            pages = self._pdf_pages(data, engine, lang, options, warnings)
        else:
            image = _open_image(data, self.max_pixels)
            pages = [self._ocr_page(1, image, engine, lang, options, warnings)]

        used_ocr = any(page.method is Method.OCR for page in pages)
        if used_ocr and "ara" in lang and not engine.reliable_for_arabic:
            warnings.insert(0, ARABIC_AI_WARNING)
        return ExtractionResult(pages=pages, ocr_engine=engine.name if used_ocr else None, warnings=warnings)

    def _pdf_pages(
        self, data: bytes, engine: OcrEngine, lang: str, options: ExtractOptions, warnings: list[str]
    ) -> list[PageResult]:
        texts, total = read_text_layer(data, self.max_pages)
        if not texts:
            raise ExtractionError("This PDF has no pages.")
        if total > len(texts):
            warnings.append(f"Only the first {len(texts)} of {total} pages were processed (MAX_PDF_PAGES).")

        scanned = [index for index, text in enumerate(texts) if is_scanned(text, self.min_chars_per_page)]
        pages: dict[int, PageResult] = {
            index: PageResult(number=index + 1, text=text.strip(), method=Method.PDF_PARSER)
            for index, text in enumerate(texts)
            if index not in scanned
        }
        for index, image in render_pages(data, scanned, self.ocr_dpi, self.max_pixels):
            pages[index] = self._ocr_page(index + 1, image, engine, lang, options, warnings)
        return [pages[index] for index in sorted(pages)]

    def _ocr_page(
        self,
        number: int,
        image: Image.Image,
        engine: OcrEngine,
        lang: str,
        options: ExtractOptions,
        warnings: list[str],
    ) -> PageResult:
        try:
            result = engine.read(image, lang, options.page_mode)
        except OcrTimeoutError as exc:
            warnings.append(f"Page {number}: {exc} The page is left empty.")
            return PageResult(number=number, text="", method=Method.OCR, review_reason=ReviewReason.NO_TEXT)
        text = result.text.strip()
        return PageResult(
            number=number,
            text=text,
            method=Method.OCR,
            confidence=result.confidence,
            review_reason=self._review_reason(text, result.confidence, engine, lang),
        )

    def _review_reason(self, text: str, confidence: float | None, engine: OcrEngine, lang: str) -> ReviewReason | None:
        if not text:
            return ReviewReason.NO_TEXT
        if "ara" in lang and not engine.reliable_for_arabic:
            return ReviewReason.AI_OCR_ARABIC
        if confidence is not None and confidence < self.review_threshold:
            return ReviewReason.LOW_CONFIDENCE
        return None


def _open_image(data: bytes, max_pixels: int = 0) -> Image.Image:
    """Open an image, checking its size from the header before decoding the pixels."""
    try:
        image = Image.open(BytesIO(data))
        width, height = image.size
        if max_pixels and width * height > max_pixels:
            raise ExtractionError(
                f"This image is {width} x {height} pixels; the limit is {max_pixels // 1_000_000} megapixels."
            )
        image.load()
        return image
    except Image.DecompressionBombError as exc:
        raise ExtractionError("This image is too large to process safely.") from exc
    except (UnidentifiedImageError, OSError) as exc:
        raise ExtractionError("This image is damaged or in an unsupported format.") from exc
