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


def download(url: str, target: Path) -> None:
    """Download to a temporary file first, so an interrupted download never looks complete."""
    partial = target.with_suffix(".part")
    with urllib.request.urlopen(url, timeout=120) as response:
        expected = int(response.headers.get("Content-Length") or 0)
        partial.write_bytes(response.read())
    if expected and partial.stat().st_size != expected:
        partial.unlink()
        raise OSError(f"incomplete download for {target.name}, please run the script again")
    partial.replace(target)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for lang in LANGUAGES:
        target = OUT / f"{lang}.traineddata"
        if target.exists():
            print(f"{lang}: already there")
            continue
        print(f"{lang}: downloading...")
        download(URL.format(lang=lang), target)
        print(f"{lang}: {target.stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()
