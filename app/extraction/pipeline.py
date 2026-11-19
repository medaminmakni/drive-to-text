"""Orchestrates extraction: the only place that knows the full routing.

    PDF   -> pypdf text layer, page by page
             page with < min_chars characters -> render (pypdfium2) -> OCR
    image -> OCR
Each OCR page gets a confidence and, when needed, a "needs review" flag.
"""

from io import BytesIO

from PIL import Image, UnidentifiedImageError

from app.extraction.models import (
    ExtractionError,
    ExtractionResult,
    ExtractOptions,
    Method,
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
    ):
        if not engines:
            raise ValueError("At least one OCR engine is required.")
        self.engines = engines
        self.min_chars_per_page = min_chars_per_page
        self.ocr_dpi = ocr_dpi
        self.review_threshold = review_threshold

    def extract(self, data: bytes, mime_type: str = "", options: ExtractOptions | None = None) -> ExtractionResult:
        options = options or ExtractOptions()
        lang = parse_languages(options.lang)  # raises ValueError on unknown codes
        engine = self.engines.get(options.engine)
        if engine is None:
            raise ExtractionError(f"Unknown OCR engine '{options.engine}'.")

        if choose_pipeline(data, mime_type) is Pipeline.PDF:
            pages = self._pdf_pages(data, engine, lang, options)
        else:
            pages = [self._ocr_page(1, _open_image(data), engine, lang, options)]

        used_ocr = any(page.method is Method.OCR for page in pages)
        warnings = [ARABIC_AI_WARNING] if used_ocr and "ara" in lang and not engine.reliable_for_arabic else []
        return ExtractionResult(pages=pages, ocr_engine=engine.name if used_ocr else None, warnings=warnings)

    def _pdf_pages(self, data: bytes, engine: OcrEngine, lang: str, options: ExtractOptions) -> list[PageResult]:
        texts = read_text_layer(data)
        if not texts:
            raise ExtractionError("This PDF has no pages.")

        scanned = [index for index, text in enumerate(texts) if is_scanned(text, self.min_chars_per_page)]
        pages: dict[int, PageResult] = {
            index: PageResult(number=index + 1, text=text.strip(), method=Method.PDF_PARSER)
            for index, text in enumerate(texts)
            if index not in scanned
        }
        for index, image in render_pages(data, scanned, self.ocr_dpi):
            pages[index] = self._ocr_page(index + 1, image, engine, lang, options)
        return [pages[index] for index in sorted(pages)]

    def _ocr_page(
        self,
        number: int,
        image: Image.Image,
        engine: OcrEngine,
        lang: str,
        options: ExtractOptions,
    ) -> PageResult:
        result = engine.read(image, lang, options.page_mode)
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


def _open_image(data: bytes) -> Image.Image:
    try:
        image = Image.open(BytesIO(data))
        image.load()
        return image
    except (UnidentifiedImageError, OSError) as exc:
        raise ExtractionError("This image is damaged or in an unsupported format.") from exc
