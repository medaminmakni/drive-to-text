"""Choose the pipeline for a file from its content (decision 008)."""

from enum import Enum

from app.extraction.models import ExtractionError

PDF_SIGNATURE = b"%PDF-"
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
JPEG_SIGNATURE = b"\xff\xd8\xff"


class Pipeline(str, Enum):
    PDF = "pdf"
    IMAGE = "image"


def choose_pipeline(data: bytes, mime_type: str = "") -> Pipeline:
    """Look at the first bytes ("magic bytes") first, then at the declared type.

    Every format starts with a fixed signature, which is more reliable than a file
    name or a mime type: a PDF renamed .png still goes to the PDF parser.
    """
    if not data:
        raise ExtractionError("The file is empty.")
    if PDF_SIGNATURE in data[:1024]:  # the spec allows a little junk before the header
        return Pipeline.PDF
    if data.startswith(PNG_SIGNATURE) or data.startswith(JPEG_SIGNATURE):
        return Pipeline.IMAGE
    if mime_type == "application/pdf":
        return Pipeline.PDF
    if mime_type in ("image/png", "image/jpeg"):
        return Pipeline.IMAGE
    raise ExtractionError("Unsupported file type. Only PDF, PNG and JPG files are processed.")
