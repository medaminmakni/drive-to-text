"""Turn PDF pages into images for OCR, with pypdfium2 (Apache-2.0 / BSD-3-Clause, decision 005)."""

from collections.abc import Iterator

import pypdfium2 as pdfium
from PIL import Image

from app.extraction.models import ExtractionError


def render_pages(data: bytes, page_indexes: list[int], dpi: int = 300) -> Iterator[tuple[int, Image.Image]]:
    """Yield (index, image) for each requested page, one at a time to keep memory low.

    PDF sizes are in points (72 per inch), so scale = dpi / 72.
    """
    if not page_indexes:
        return
    try:
        document = pdfium.PdfDocument(data)
    except pdfium.PdfiumError as exc:
        raise ExtractionError("Could not open this PDF to render its scanned pages.") from exc
    try:
        for index in page_indexes:
            page = document[index]
            try:
                image = page.render(scale=dpi / 72).to_pil()
            finally:
                page.close()
            yield index, image
    finally:
        document.close()
