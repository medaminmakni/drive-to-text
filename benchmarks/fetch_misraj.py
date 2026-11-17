"""Download a subset of Misraj-DocOCR (400 real Arabic document pages, Apache-2.0).

The pages and their ground truth are written to benchmarks/data/misraj/ (git-ignored),
in the same format as benchmarks/samples, so run.py can use them:

    python benchmarks/fetch_misraj.py --count 20
    python benchmarks/run.py --samples benchmarks/samples benchmarks/data/misraj --engines tesseract

Dataset: https://huggingface.co/datasets/Misraj/Misraj-DocOCR
It is read through the public Hugging Face dataset viewer API, so no extra package is needed.
"""

import argparse
import csv
import json
import re
import urllib.parse
import urllib.request
from pathlib import Path

ROWS_API = "https://datasets-server.huggingface.co/rows"
DATASET = "Misraj/Misraj-DocOCR"
OUT = Path(__file__).parent / "data" / "misraj"


def markdown_to_text(markdown: str) -> str:
    """The ground truth is Markdown. Keep the words, drop the formatting."""
    text = re.sub(r"<[^>]+>", " ", markdown)                       # html tags (<br>, <table>...)
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", text)              # images
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)           # links -> link text
    text = re.sub(r"^\s*\|?\s*:?-{3,}.*$", " ", text, flags=re.M)  # table separator rows
    text = re.sub(r"^\s{0,3}#{1,6}\s*", "", text, flags=re.M)      # headings
    text = re.sub(r"(\*\*|__|\*|`)", "", text)                     # bold, italic, code
    text = text.replace("|", " ")
    return "\n".join(line.strip() for line in text.splitlines() if line.strip()) + "\n"


def fetch_rows(offset: int, length: int) -> list[dict]:
    query = urllib.parse.urlencode(
        {"dataset": DATASET, "config": "default", "split": "train", "offset": offset, "length": length}
    )
    with urllib.request.urlopen(f"{ROWS_API}?{query}", timeout=60) as response:
        return [item["row"] for item in json.load(response)["rows"]]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--count", type=int, default=20, help="number of pages to download (max 400)")
    parser.add_argument("--offset", type=int, default=0)
    args = parser.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    manifest = []
    remaining, offset = args.count, args.offset
    while remaining > 0:
        rows = fetch_rows(offset, min(remaining, 100))
        if not rows:
            break
        for row in rows:
            name = f"misraj_{row['uuid'][:8]}.jpg"
            with urllib.request.urlopen(row["image"]["src"], timeout=60) as response:
                (OUT / name).write_bytes(response.read())
            (OUT / name).with_suffix(".txt").write_text(markdown_to_text(row["markdown"]), encoding="utf-8")
            manifest.append({"file": name, "lang": "ara", "group": "arabic_real", "description": "Misraj-DocOCR page"})
            print(f"saved {name}")
        remaining -= len(rows)
        offset += len(rows)

    with (OUT / "manifest.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["file", "lang", "group", "description"])
        writer.writeheader()
        writer.writerows(manifest)
    print(f"{len(manifest)} pages in {OUT}")


if __name__ == "__main__":
    main()
