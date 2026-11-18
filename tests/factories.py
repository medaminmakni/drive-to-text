"""Build small PDFs and images in memory for the tests (no fixture files needed)."""

from io import BytesIO

from PIL import Image, ImageDraw, ImageFont


def native_pdf(*page_texts: str) -> bytes:
    """A real PDF with a text layer, one line of Helvetica text per page."""
    objects = []
    page_ids = []
    font_id = 3 + 2 * len(page_texts)
    for index, text in enumerate(page_texts):
        page_id, content_id = 3 + 2 * index, 4 + 2 * index
        page_ids.append(page_id)
        escaped = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        stream = f"BT /F1 18 Tf 72 720 Td ({escaped}) Tj ET".encode()
        objects.append(
            (page_id, f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
                      f"/Resources << /Font << /F1 {font_id} 0 R >> >> /Contents {content_id} 0 R >>".encode())
        )
        objects.append((content_id, b"<< /Length %d >>\nstream\n" % len(stream) + stream + b"\nendstream"))
    kids = " ".join(f"{pid} 0 R" for pid in page_ids)
    objects = [
        (1, b"<< /Type /Catalog /Pages 2 0 R >>"),
        (2, f"<< /Type /Pages /Kids [{kids}] /Count {len(page_ids)} >>".encode()),
        *objects,
        (font_id, b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"),
    ]

    out = BytesIO()
    out.write(b"%PDF-1.4\n")
    offsets = {}
    for obj_id, body in sorted(objects):
        offsets[obj_id] = out.tell()
        out.write(b"%d 0 obj\n" % obj_id + body + b"\nendobj\n")
    xref = out.tell()
    count = max(offsets) + 1
    out.write(b"xref\n0 %d\n0000000000 65535 f \n" % count)
    for obj_id in range(1, count):
        out.write(b"%010d 00000 n \n" % offsets[obj_id])
    out.write(b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (count, xref))
    return out.getvalue()


def text_image(text: str) -> Image.Image:
    image = Image.new("RGB", (1400, 220), "white")
    draw = ImageDraw.Draw(image)
    draw.text((40, 60), text, fill="black", font=ImageFont.load_default(size=72))
    return image


def image_bytes(text: str, fmt: str = "PNG") -> bytes:
    out = BytesIO()
    text_image(text).save(out, format=fmt)
    return out.getvalue()


def scanned_pdf(text: str) -> bytes:
    """A PDF that only contains a picture of the text (no text layer), like a scan."""
    out = BytesIO()
    text_image(text).save(out, format="PDF", resolution=150)
    return out.getvalue()
