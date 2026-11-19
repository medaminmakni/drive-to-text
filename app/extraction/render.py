"""Turn PDF pages into images for OCR, with pypdfium2 (Apache-2.0 / BSD-3-Clause, decision 005)."""

import math
from collections.abc import Iterator

import pypdfium2 as pdfium
from PIL import Image

from app.extraction.models import ExtractionError


def render_pages(
    data: bytes, page_indexes: list[int], dpi: int = 300, max_pixels: int = 0
) -> Iterator[tuple[int, Image.Image]]:
    """Yield (index, image) for each requested page, one at a time to keep memory low.

    PDF sizes are in points (72 per inch), so scale = dpi / 72. A page can declare any
    size (a poster, or a hostile 200 x 200 inch page): with ``max_pixels``, the scale is
    lowered so the rendered image never exceeds that many pixels.
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
                image = page.render(scale=_scale(page.get_size(), dpi, max_pixels)).to_pil()
            finally:
                page.close()
            yield index, image
    finally:
        document.close()


def _scale(size: tuple[float, float], dpi: int, max_pixels: int) -> float:
    scale = dpi / 72
    width, height = size
    if max_pixels and width * height * scale * scale > max_pixels:
        scale = math.sqrt(max_pixels / (width * height))
    return scale
