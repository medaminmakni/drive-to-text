import pytest

from app.extraction.models import ExtractionError
from app.extraction.routing import Pipeline, choose_pipeline
from tests.factories import image_bytes, native_pdf


@pytest.mark.parametrize(
    "data, mime, expected",
    [
        (native_pdf("hello"), "application/pdf", Pipeline.PDF),
        (image_bytes("hi", "PNG"), "image/png", Pipeline.IMAGE),
        (image_bytes("hi", "JPEG"), "image/jpeg", Pipeline.IMAGE),
        (native_pdf("hello"), "image/png", Pipeline.PDF),  # the content wins over a wrong type
        (image_bytes("hi", "PNG"), "application/pdf", Pipeline.IMAGE),
        (b"junk" + native_pdf("hello"), "", Pipeline.PDF),  # a few bytes before the header are allowed
    ],
)
def test_pipeline_is_chosen_from_the_content(data, mime, expected):
    assert choose_pipeline(data, mime) is expected


def test_unknown_content_is_rejected():
    with pytest.raises(ExtractionError, match="Unsupported file type"):
        choose_pipeline(b"PK\x03\x04 a zip file", "application/zip")


def test_empty_file_is_rejected():
    with pytest.raises(ExtractionError, match="empty"):
        choose_pipeline(b"", "application/pdf")
