import shutil
from io import BytesIO

import pytesseract
import pytest
from PIL import Image

from app.extraction.models import ExtractionError, ExtractOptions, Method, OcrTimeoutError, PageMode, ReviewReason
from app.extraction.ocr import OcrResult, TesseractOcr, parse_languages
from app.extraction.pdf import is_scanned, read_text_layer
from app.extraction.pipeline import Extractor
from app.extraction.render import render_pages
from tests.factories import image_bytes, native_pdf, scanned_pdf

needs_tesseract = pytest.mark.skipif(shutil.which("tesseract") is None, reason="Tesseract is not installed")


class FakeOcr:
    """Stands in for an OCR engine, so the routing is tested without Tesseract."""

    def __init__(self, name="tesseract", confidence=95.0, text="ocr text", reliable_for_arabic=True):
        self.name, self.label = name, name
        self.confidence, self.text = confidence, text
        self.reliable_for_arabic = reliable_for_arabic
        self.calls = []

    def is_available(self):
        return True

    def read(self, image, lang, page_mode):
        self.calls.append((lang, page_mode))
        return OcrResult(self.text, self.confidence)


def extractor(*engines, **settings):
    engines = engines or (FakeOcr(),)
    return Extractor({engine.name: engine for engine in engines}, ocr_dpi=72, **settings)


# ---- routing through the pipeline ---------------------------------------------------

def test_native_pdf_uses_the_parser_only():
    ocr = FakeOcr()
    result = extractor(ocr).extract(native_pdf("Invoice 2026-001 total 450 TND"), "application/pdf")

    assert result.method is Method.PDF_PARSER
    assert "Invoice 2026-001" in result.text
    assert result.ocr_engine is None and result.confidence is None and not result.needs_review
    assert ocr.calls == []


def test_scanned_pdf_goes_to_ocr():
    ocr = FakeOcr()
    result = extractor(ocr).extract(scanned_pdf("Scanned page"), "application/pdf")

    assert result.method is Method.OCR
    assert result.ocr_engine == "tesseract"
    assert len(ocr.calls) == 1


def test_mixed_pdf_only_sends_pages_without_text_to_ocr():
    ocr = FakeOcr()
    result = extractor(ocr).extract(native_pdf("This page has a real text layer", ""), "application/pdf")

    assert result.method is Method.PDF_PARSER_AND_OCR
    assert [page.method for page in result.pages] == [Method.PDF_PARSER, Method.OCR]
    assert [page.number for page in result.pages] == [1, 2]
    assert len(ocr.calls) == 1


def test_image_uses_the_selected_language_and_page_mode():
    ocr = FakeOcr()
    options = ExtractOptions(lang="ara+fra", page_mode=PageMode.SINGLE_BLOCK)
    result = extractor(ocr).extract(image_bytes("x"), "image/png", options)

    assert result.method is Method.OCR
    assert ocr.calls == [("ara+fra", PageMode.SINGLE_BLOCK)]


def test_the_chosen_engine_is_used():
    tesseract, glm = FakeOcr("tesseract"), FakeOcr("glm-ocr", confidence=None, reliable_for_arabic=False)
    result = extractor(tesseract, glm).extract(image_bytes("x"), "image/png", ExtractOptions(engine="glm-ocr"))

    assert result.ocr_engine == "glm-ocr"
    assert glm.calls and not tesseract.calls


def test_unknown_engine_or_language_is_refused():
    with pytest.raises(ExtractionError, match="Unknown OCR engine"):
        extractor().extract(image_bytes("x"), "image/png", ExtractOptions(engine="nope"))
    with pytest.raises(ValueError, match="Unsupported OCR language"):
        extractor().extract(image_bytes("x"), "image/png", ExtractOptions(lang="deu"))


# ---- review flags --------------------------------------------------------------------

def test_low_confidence_page_needs_review():
    result = extractor(FakeOcr(confidence=40.0), review_threshold=70).extract(image_bytes("x"), "image/png")
    assert result.needs_review
    assert result.pages[0].review_reason is ReviewReason.LOW_CONFIDENCE
    assert result.confidence == 40.0


def test_confident_page_does_not_need_review():
    result = extractor(FakeOcr(confidence=92.0), review_threshold=70).extract(image_bytes("x"), "image/png")
    assert not result.needs_review


def test_page_without_text_needs_review():
    result = extractor(FakeOcr(text="  ")).extract(image_bytes("x"), "image/png")
    assert result.pages[0].review_reason is ReviewReason.NO_TEXT


def test_ai_engine_on_arabic_is_always_flagged_with_a_warning():
    glm = FakeOcr("glm-ocr", confidence=None, reliable_for_arabic=False)
    result = extractor(glm).extract(image_bytes("x"), "image/png", ExtractOptions(lang="ara", engine="glm-ocr"))

    assert result.pages[0].review_reason is ReviewReason.AI_OCR_ARABIC
    assert result.warnings and "invent Arabic text" in result.warnings[0]


def test_ai_engine_on_french_is_not_flagged():
    glm = FakeOcr("glm-ocr", confidence=None, reliable_for_arabic=False)
    result = extractor(glm).extract(image_bytes("x"), "image/png", ExtractOptions(lang="fra", engine="glm-ocr"))
    assert not result.needs_review and result.warnings == []


def test_result_serialises_to_json_friendly_dict():
    data = extractor(FakeOcr(confidence=81.234)).extract(image_bytes("x"), "image/png").to_dict()
    assert data["method"] == "ocr" and data["confidence"] == 81.2 and data["pages_count"] == 1
    assert data["pages"][0] == {"number": 1, "method": "ocr", "confidence": 81.2,
                                "needs_review": False, "review_reason": None, "text": "ocr text"}


# ---- errors and helpers -------------------------------------------------------------

def test_damaged_pdf_fails_cleanly():
    with pytest.raises(ExtractionError, match="damaged"):
        read_text_layer(b"%PDF-1.4 this is not really a pdf")


def test_damaged_image_fails_cleanly():
    with pytest.raises(ExtractionError, match="damaged"):
        extractor().extract(b"\x89PNG\r\n\x1a\nbroken", "image/png")


def test_scanned_page_detection_ignores_whitespace():
    assert is_scanned("  \n \t ", min_chars=20)
    assert not is_scanned("This line has more than twenty characters", min_chars=20)


@pytest.mark.parametrize("value, expected", [("eng", "eng"), ("fra+ara", "fra+ara"), ("eng+eng", "eng"), (None, "eng")])
def test_parse_languages(value, expected):
    assert parse_languages(value) == expected


# ---- limits: one hostile or huge file must never block a worker ---------------------

class SlowOcr(FakeOcr):
    def read(self, image, lang, page_mode):
        raise OcrTimeoutError("OCR stopped after 60 s.")


def test_pdf_over_the_page_limit_keeps_the_first_pages_with_a_warning():
    pages = [f"Page {n}: a native page with enough characters to be parsed." for n in (1, 2, 3)]
    result = extractor(max_pages=2).extract(native_pdf(*pages), "application/pdf")
    assert [page.number for page in result.pages] == [1, 2]
    assert any("first 2 of 3 pages" in warning for warning in result.warnings)


def test_page_that_times_out_is_left_empty_and_flagged_without_failing_the_file():
    result = extractor(SlowOcr()).extract(scanned_pdf("SLOW PAGE"), "application/pdf")
    page = result.pages[0]
    assert page.text == "" and page.review_reason is ReviewReason.NO_TEXT
    assert any("Page 1" in warning and "60 s" in warning for warning in result.warnings)


def test_image_over_the_pixel_limit_is_refused_before_decoding():
    with pytest.raises(ExtractionError, match="pixels"):
        extractor(max_pixels=10_000).extract(image_bytes("too big"), "image/png")


def test_rendered_scanned_page_never_exceeds_the_pixel_limit():
    [(index, image)] = list(render_pages(scanned_pdf("BIG PAGE"), [0], dpi=600, max_pixels=200_000))
    assert index == 0 and image.width * image.height <= 200_000 * 1.02


def test_tesseract_timeout_becomes_an_ocr_timeout(monkeypatch):
    def timeout(*args, **kwargs):
        raise RuntimeError("Tesseract process timeout")

    monkeypatch.setattr(pytesseract, "image_to_data", timeout)
    with pytest.raises(OcrTimeoutError):
        TesseractOcr(timeout=5).read(Image.new("L", (50, 50), "white"), "eng")


def test_tesseract_failure_is_still_a_clean_extraction_error(monkeypatch):
    # TesseractError is a RuntimeError too: it must not be mistaken for a timeout.
    def failure(*args, **kwargs):
        raise pytesseract.TesseractError(1, "bad image")

    monkeypatch.setattr(pytesseract, "image_to_data", failure)
    with pytest.raises(ExtractionError, match="OCR failed"):
        TesseractOcr(timeout=5).read(Image.new("L", (50, 50), "white"), "eng")


# ---- the real Tesseract (skipped when it is not installed) -------------------------------

@needs_tesseract
def test_tesseract_reads_text_and_gives_a_confidence():
    image = Image.open(BytesIO(image_bytes("HELLO DIXPERTIA 2026")))
    result = TesseractOcr().read(image, "eng")
    assert "DIXPERTIA" in result.text.upper()
    assert 50 < result.confidence <= 100


@needs_tesseract
def test_full_pipeline_on_a_scanned_pdf_with_tesseract():
    extractor_ = Extractor({"tesseract": TesseractOcr()}, ocr_dpi=200)
    result = extractor_.extract(scanned_pdf("SCANNED INVOICE 42"), "application/pdf")
    assert result.method is Method.OCR
    assert "INVOICE" in result.text.upper()
    assert result.confidence is not None
