"""OCR engines behind one small interface (decision 006 and 007).

The pipeline only knows "an engine that turns an image into text and a confidence".
Tesseract is the default. Other engines (see vlm.py) can be added without touching
the pipeline: this is the Strategy pattern.
"""

import logging
from collections import OrderedDict
from dataclasses import dataclass
from typing import Protocol

import pytesseract
from PIL import Image, ImageOps

from app.extraction.models import ExtractionError, PageMode

logger = logging.getLogger(__name__)

SUPPORTED_LANGUAGES = {"eng": "English", "fra": "French", "ara": "Arabic"}
TESSERACT_PSM = {PageMode.AUTO: 3, PageMode.SINGLE_BLOCK: 6}


@dataclass(frozen=True)
class OcrResult:
    text: str
    confidence: float | None  # 0-100, None when the engine gives no score


class OcrEngine(Protocol):
    name: str
    label: str
    reliable_for_arabic: bool

    def is_available(self) -> bool: ...

    def read(self, image: Image.Image, lang: str, page_mode: PageMode) -> OcrResult: ...


def parse_languages(value: str | None, default: str = "eng") -> str:
    """Validate a language string like "eng" or "ara+fra" and return it normalised."""
    codes = [code.strip() for code in (value or default).split("+") if code.strip()]
    unknown = [code for code in codes if code not in SUPPORTED_LANGUAGES]
    if not codes or unknown:
        raise ValueError(f"Unsupported OCR language: {', '.join(unknown) or value!r}.")
    return "+".join(dict.fromkeys(codes))  # keep the order, drop duplicates


def prepare(image: Image.Image) -> Image.Image:
    """Phone photos are often stored sideways with an EXIF rotation tag: apply it."""
    image = ImageOps.exif_transpose(image)
    return image if image.mode in ("RGB", "L") else image.convert("RGB")


class TesseractOcr:
    name = "tesseract"
    label = "Tesseract (default, fast, Arabic/French/English)"
    reliable_for_arabic = True

    def __init__(self, tessdata_dir: str | None = None):
        self._config = f'--tessdata-dir "{tessdata_dir}"' if tessdata_dir else ""

    def is_available(self) -> bool:
        return bool(self.installed_languages())

    def installed_languages(self) -> list[str]:
        """Supported languages whose model is installed on this machine."""
        try:
            installed = set(pytesseract.get_languages(config=self._config))
        except (pytesseract.TesseractNotFoundError, pytesseract.TesseractError, OSError):
            logger.warning("Tesseract is not installed or not on PATH")
            return []
        return [code for code in SUPPORTED_LANGUAGES if code in installed]

    def read(self, image: Image.Image, lang: str, page_mode: PageMode = PageMode.AUTO) -> OcrResult:
        """One OCR pass gives both the text and the confidence of every word."""
        config = f"{self._config} --psm {TESSERACT_PSM[page_mode]}".strip()
        try:
            data = pytesseract.image_to_data(
                prepare(image),
                lang=lang,
                config=config,
                output_type=pytesseract.Output.DICT,
            )
        except pytesseract.TesseractNotFoundError as exc:
            raise ExtractionError("The OCR engine (Tesseract) is not installed on the server.") from exc
        except pytesseract.TesseractError as exc:
            logger.warning("Tesseract failed: %s", exc)
            raise ExtractionError("OCR failed on this image.") from exc
        return OcrResult(text=_lines_from(data), confidence=_weighted_confidence(data))


def _lines_from(data: dict) -> str:
    """Rebuild the text line by line from Tesseract's word list (kept in reading order)."""
    lines: OrderedDict[tuple, list[str]] = OrderedDict()
    for index, word in enumerate(data["text"]):
        if word.strip():
            key = (data["block_num"][index], data["par_num"][index], data["line_num"][index])
            lines.setdefault(key, []).append(word)
    return "\n".join(" ".join(words) for words in lines.values())


def _weighted_confidence(data: dict) -> float | None:
    """Average word confidence, weighted by word length.

    Long words weigh more than one-character noise (dots, dashes) that Tesseract
    often scores badly. Tesseract gives -1 to non-word boxes: those are skipped.
    """
    total = weight = 0.0
    for word, confidence in zip(data["text"], data["conf"], strict=True):
        word, confidence = word.strip(), float(confidence)
        if word and confidence >= 0:
            total += confidence * len(word)
            weight += len(word)
    return total / weight if weight else None
