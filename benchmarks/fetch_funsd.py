"""Download English forms from FUNSD (noisy scanned forms, text labelled by humans).

    python benchmarks/fetch_funsd.py --count 20

Writes benchmarks/data/funsd/ (git-ignored). Uses the test split.
Source: https://guillaumejaume.github.io/FUNSD/  Licence: non-commercial research use.
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

URL = "https://guillaumejaume.github.io/FUNSD/dataset.zip"
OUT = Path(__file__).parent / "data" / "funsd"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--count", type=int, default=20)
    args = parser.parse_args()

    print(f"downloading {URL}")
    with urllib.request.urlopen(URL, timeout=300) as response:
        archive = zipfile.ZipFile(io.BytesIO(response.read()))

    annotations = sorted(n for n in archive.namelist() if "testing_data/annotations/" in n and n.endswith(".json"))
    rows = []
    for annotation in annotations[: args.count]:
        stem = Path(annotation).stem
        form = json.loads(archive.read(annotation))["form"]
        blocks = [(entity["box"], entity["text"]) for entity in form]
        image = archive.read(annotation.replace("/annotations/", "/images/").replace(".json", ".png"))
        name = f"funsd_{stem}.png"
        save_sample(OUT, name, image, reading_order_text(blocks))
        rows.append({"file": name, "lang": "eng", "group": "forms_en", "description": "FUNSD English form"})
    write_manifest(OUT, rows)


if __name__ == "__main__":
    main()
