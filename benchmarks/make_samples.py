"""Generate the benchmark samples in benchmarks/samples (images + exact ground truth).

The text is rendered by a real browser engine (Chromium, through Playwright) so that
Arabic letters are joined and ordered correctly. Some images are then degraded to look
like scans or phone photos. Development tool only: the generated files are committed,
so running the benchmark does not need Playwright.

    pip install playwright pillow && playwright install chromium
    python benchmarks/make_samples.py
"""

import csv
import random
from pathlib import Path

from PIL import Image, ImageEnhance, ImageFilter, ImageOps
from playwright.sync_api import sync_playwright

OUT = Path(__file__).parent / "samples"

AR_NOTICE = [
    "الجمهورية التونسية",
    "وزارة المالية",
    "إعلام بالدفع",
    "يتعين على الشركة المذكورة أعلاه تسديد المبلغ المطلوب قبل تاريخ الاستحقاق.",
    "المبلغ المطلوب: ألف وثمانمائة وخمسون دينارا",
    "تاريخ الاستحقاق: الخامس من شهر ديسمبر",
    "وفي صورة عدم الدفع يتم تطبيق خطايا التأخير طبقا للتشريع الجاري به العمل.",
]
AR_FR_CERTIFICATE = [
    ("ar", "الجمهورية التونسية"),
    ("fr", "République Tunisienne"),
    ("ar", "بلدية صفاقس"),
    ("fr", "Municipalité de Sfax"),
    ("ar", "شهادة إقامة"),
    ("fr", "Certificat de résidence"),
    ("ar", "الاسم واللقب: محمد أمين المكني"),
    ("fr", "Nom et prénom : Mohamed Amin Makni"),
    ("ar", "العنوان: شارع الحبيب بورقيبة، صفاقس"),
    ("fr", "Adresse : Avenue Habib Bourguiba, Sfax"),
]
FR_INVOICE = [
    "FACTURE N° 2026-0117",
    "Fournisseur : Bureau Plus SARL, Route de Tunis km 4, Sfax",
    "Client : Atlas Services, 12 avenue Habib Bourguiba, Sfax",
    "Ramette papier A4 : 20 x 14,500 = 290,000 TND",
    "Cartouche toner noir : 4 x 185,000 = 740,000 TND",
    "Total TTC : 1 447,040 TND",
    "Arrêtée la présente facture à la somme de mille quatre cent quarante-sept dinars.",
]
EN_RECEIPT = [
    "DELIVERY NOTE BL-5521",
    "Delivered to: Atlas Services, Sfax",
    "Date: 28/10/2026",
    "Items: 12 boxes of printer paper",
    "Received in good condition.",
]


def page(lines, font="DejaVu Sans", size=26):
    """HTML page where each line keeps its own direction (Arabic right, French left)."""
    rows = []
    for item in lines:
        lang, text = item if isinstance(item, tuple) else (None, item)
        direction = "rtl" if (lang or ("ar" if any("؀" <= c <= "ۿ" for c in text) else "fr")) == "ar" else "ltr"
        rows.append(f'<p dir="{direction}" style="text-align:{"right" if direction == "rtl" else "left"}">{text}</p>')
    return (f'<html><body style="margin:0;padding:40px 50px;width:1100px;background:#fff;color:#111;'
            f'font-family:\'{font}\';font-size:{size}px;line-height:1.5">{"".join(rows)}</body></html>')


def truth(lines):
    return "\n".join(item[1] if isinstance(item, tuple) else item for item in lines) + "\n"


def scan(image, angle, seed):
    rng = random.Random(seed)
    image = image.convert("L").rotate(angle, expand=True, fillcolor=255, resample=Image.BICUBIC)
    image = ImageEnhance.Contrast(image).enhance(0.85).filter(ImageFilter.GaussianBlur(0.8))
    pixels = image.load()
    width, height = image.size
    for _ in range(width * height // 300):
        pixels[rng.randrange(width), rng.randrange(height)] = rng.randint(140, 220)
    return image.resize((int(width * 0.75), int(height * 0.75)))


def photo(image, angle):
    image = ImageOps.expand(image.convert("RGB"), border=50, fill=(210, 202, 188))
    image = image.rotate(angle, expand=True, fillcolor=(95, 90, 82), resample=Image.BICUBIC)
    shade = Image.linear_gradient("L").resize(image.size).point(lambda v: 165 + v * 90 // 255)
    image = Image.composite(image, Image.new("RGB", image.size, (0, 0, 0)), shade)
    return ImageEnhance.Brightness(image).enhance(1.05)


SAMPLES = [
    # file, lines, font, transform, tesseract lang, group, description
    ("ar_notice_clean.png", AR_NOTICE, "DejaVu Sans", None, "ara", "arabic", "Printed Arabic notice, clean"),
    ("ar_notice_serif_scan.png", AR_NOTICE, "FreeSerif", ("scan", 0.8), "ara", "arabic", "Arabic, serif font, scanned look"),
    ("ar_notice_photo.jpg", AR_NOTICE, "DejaVu Sans", ("photo", 2.0), "ara", "arabic", "Arabic, phone photo look"),
    ("mixed_certificate_clean.png", AR_FR_CERTIFICATE, "DejaVu Sans", None, "ara+fra", "mixed", "Arabic + French certificate"),
    ("mixed_certificate_scan.png", AR_FR_CERTIFICATE, "FreeSerif", ("scan", -0.7), "ara+fra", "mixed", "Arabic + French, scanned look"),
    ("fr_invoice_clean.png", FR_INVOICE, "DejaVu Sans", None, "fra", "latin", "French invoice, clean"),
    ("fr_invoice_scan.png", FR_INVOICE, "FreeSerif", ("scan", 0.9), "fra", "latin", "French invoice, scanned look"),
    ("en_delivery_photo.jpg", EN_RECEIPT, "DejaVu Sans", ("photo", -1.8), "eng", "latin", "English delivery note, photo look"),
]


def main():
    OUT.mkdir(exist_ok=True)
    rows = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        tab = browser.new_page(viewport={"width": 1200, "height": 400})
        for index, (name, lines, font, transform, lang, group, description) in enumerate(SAMPLES):
            tab.set_content(page(lines, font))
            raw = OUT / "_render.png"
            tab.screenshot(path=str(raw), full_page=True)
            image = Image.open(raw)
            if transform and transform[0] == "scan":
                image = scan(image, transform[1], seed=index)
            elif transform and transform[0] == "photo":
                image = photo(image, transform[1])
            target = OUT / name
            image.convert("RGB").save(target, quality=85) if target.suffix == ".jpg" else image.save(target)
            target.with_suffix(".txt").write_text(truth(lines), encoding="utf-8")
            rows.append({"file": name, "lang": lang, "group": group, "description": description})
        browser.close()
    (OUT / "_render.png").unlink()
    with (OUT / "manifest.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["file", "lang", "group", "description"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"{len(rows)} samples written to {OUT}")


if __name__ == "__main__":
    main()
