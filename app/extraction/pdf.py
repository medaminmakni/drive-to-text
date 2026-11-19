"""Read the text layer of PDF pages with pypdf (BSD-3-Clause, decision 004)."""

import logging
from io import BytesIO

from pypdf import PdfReader
from pypdf.errors import PdfReadError

from app.extraction.models import ExtractionError

logger = logging.getLogger(__name__)


def read_text_layer(data: bytes, max_pages: int = 0) -> tuple[list[str], int]:
    """Text of each page, and the real number of pages in the document.

    A page without a text layer (a scan) gives an empty string. With ``max_pages``, only
    the first pages are read: a 2,000-page PDF must not block a worker.
    """
    try:
        reader = PdfReader(BytesIO(data))
        if reader.is_encrypted and not reader.decrypt(""):
            raise ExtractionError("This PDF is password-protected.")
        total = len(reader.pages)
        pages = []
        for number, page in enumerate(reader.pages, start=1):
            if max_pages and number > max_pages:
                break
            try:
                pages.append(page.extract_text() or "")
            except Exception:  # one broken page must not lose the whole document
                logger.exception("Could not read the text layer of page %s", number)
                pages.append("")
        return pages, total
    except ExtractionError:
        raise
    except (PdfReadError, ValueError, KeyError, TypeError) as exc:
        raise ExtractionError("This PDF is damaged or not a valid PDF.") from exc


def is_scanned(text: str, min_chars: int) -> bool:
    """A page with almost no characters in its text layer is a picture (decision 005)."""
    return len("".join(text.split())) < min_chars
