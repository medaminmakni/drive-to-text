"""Download Tesseract's most accurate language models (tessdata_best, Apache-2.0).

Linux packages and most installers ship the smaller "tessdata_fast" models. The benchmark
compares both. Files go to benchmarks/data/tessdata_best/ (git-ignored).

    python benchmarks/fetch_tessdata_best.py
"""

import urllib.request
from pathlib import Path

URL = "https://github.com/tesseract-ocr/tessdata_best/raw/main/{lang}.traineddata"
OUT = Path(__file__).parent / "data" / "tessdata_best"
LANGUAGES = ["ara", "fra", "eng"]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for lang in LANGUAGES:
        target = OUT / f"{lang}.traineddata"
        if target.exists():
            print(f"{lang}: already there")
            continue
        print(f"{lang}: downloading...")
        urllib.request.urlretrieve(URL.format(lang=lang), target)
        print(f"{lang}: {target.stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()
