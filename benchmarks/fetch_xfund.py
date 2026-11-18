"""Download French forms from XFUND (scanned real forms, text labelled by humans).

    python benchmarks/fetch_xfund.py --count 20

Writes benchmarks/data/xfund_fr/ (git-ignored). Uses the validation split.
Source: https://github.com/doc-analysis/XFUND  Licence: CC BY-NC-SA 4.0 (non-commercial).
The data is only downloaded locally to evaluate OCR engines, never redistributed.
"""

import argparse
import io
import json
import sys
import urllib.request
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from sampleset import reading_order_text, save_sample, write_manifest  # noqa: E402

BASE = "https://github.com/doc-analysis/XFUND/releases/download/v1.0/{lang}.val.{ext}"
OUT = Path(__file__).parent / "data" / "xfund_fr"


def download(url: str) -> bytes:
    print(f"downloading {url}")
    with urllib.request.urlopen(url, timeout=300) as response:
        return response.read()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--count", type=int, default=20)
    args = parser.parse_args()

    labels = json.loads(download(BASE.format(lang="fr", ext="json")))
    images = zipfile.ZipFile(io.BytesIO(download(BASE.format(lang="fr", ext="zip"))))
    by_name = {Path(name).name: name for name in images.namelist()}

    rows = []
    for document in labels["documents"][: args.count]:
        file_name = document["img"]["fname"]
        blocks = [(entity["box"], entity["text"]) for entity in document["document"]]
        name = f"xfund_{Path(file_name).stem}{Path(file_name).suffix.lower()}"
        save_sample(OUT, name, images.read(by_name[file_name]), reading_order_text(blocks))
        rows.append({"file": name, "lang": "fra", "group": "forms_fr", "description": "XFUND French form"})
    write_manifest(OUT, rows)


if __name__ == "__main__":
    main()
