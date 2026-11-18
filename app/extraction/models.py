"""Shape of an extraction result, shared by the pipeline, the API, the web page and the JSON export."""

from dataclasses import dataclass, field
from enum import Enum


class Method(str, Enum):
    PDF_PARSER = "pdf_parser"
    OCR = "ocr"
    PDF_PARSER_AND_OCR = "pdf_parser+ocr"  # native PDF with some scanned pages


class PageMode(str, Enum):
    """How the OCR splits a page into blocks before reading (Tesseract's psm)."""

    AUTO = "auto"  # psm 3: finds columns and blocks itself, safe for any layout
    SINGLE_BLOCK = "single_block"  # psm 6: one column, line by line (forms, letters, certificates)


class ReviewReason(str, Enum):
    LOW_CONFIDENCE = "low_confidence"
    NO_TEXT = "no_text"
    AI_OCR_ARABIC = "ai_ocr_arabic"  # vision models invent Arabic text (measured in benchmarks/)


class ExtractionError(Exception):
    """The file cannot be read. The message can be shown to the user."""


@dataclass(frozen=True)
class ExtractOptions:
    lang: str = "eng"  # Tesseract codes: "eng", "fra", "ara", or a combination like "ara+fra"
    page_mode: PageMode = PageMode.AUTO
    engine: str = "tesseract"


@dataclass(frozen=True)
class PageResult:
    number: int  # 1-based
    text: str
    method: Method  # PDF_PARSER or OCR for a single page
    confidence: float | None = None  # 0-100 from the OCR engine; None for parser pages or engines without scores
    review_reason: ReviewReason | None = None

    @property
    def needs_review(self) -> bool:
        return self.review_reason is not None

    def to_dict(self) -> dict:
        return {
            "number": self.number,
            "method": self.method.value,
            "confidence": None if self.confidence is None else round(self.confidence, 1),
            "needs_review": self.needs_review,
            "review_reason": self.review_reason.value if self.review_reason else None,
            "text": self.text,
        }


@dataclass(frozen=True)
class ExtractionResult:
    pages: list[PageResult]
    ocr_engine: str | None = None  # set when at least one page went through OCR
    warnings: list[str] = field(default_factory=list)

    @property
    def text(self) -> str:
        return "\n\n".join(page.text.strip() for page in self.pages if page.text.strip())

    @property
    def method(self) -> Method:
        methods = {page.method for page in self.pages}
        if methods == {Method.PDF_PARSER}:
            return Method.PDF_PARSER
        if methods == {Method.OCR}:
            return Method.OCR
        return Method.PDF_PARSER_AND_OCR

    @property
    def needs_review(self) -> bool:
        return any(page.needs_review for page in self.pages)

    @property
    def confidence(self) -> float | None:
        """Lowest page confidence: a document is only as reliable as its worst page."""
        scores = [page.confidence for page in self.pages if page.confidence is not None]
        return min(scores) if scores else None

    def to_dict(self) -> dict:
        return {
            "method": self.method.value,
            "ocr_engine": self.ocr_engine,
            "confidence": None if self.confidence is None else round(self.confidence, 1),
            "needs_review": self.needs_review,
            "pages_count": len(self.pages),
            "warnings": self.warnings,
            "text": self.text,
            "pages": [page.to_dict() for page in self.pages],
        }
