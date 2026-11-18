"""Write a downloaded dataset in the benchmark's sample-folder format.

A sample folder holds one image and one .txt ground truth per document, plus a
manifest.csv with the columns: file, lang, group, description.
"""

import csv
from pathlib import Path

FIELDS = ["file", "lang", "group", "description"]


def save_sample(folder: Path, name: str, image: bytes, truth: str) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    (folder / name).write_bytes(image)
    (folder / name).with_suffix(".txt").write_text(truth.strip() + "\n", encoding="utf-8")


def write_manifest(folder: Path, rows: list[dict]) -> None:
    with (folder / "manifest.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"{len(rows)} documents in {folder}")


def reading_order_text(blocks: list[tuple[list[float], str]]) -> str:
    """Join text blocks top to bottom, then left to right.

    Forms have no single correct reading order, so this is only an approximation.
    That is why word F1 (order-free) is the main score for forms.
    """
    def key(block):
        (x0, y0, _x1, y1), _text = block
        return (round(((y0 + y1) / 2) / 15), x0)  # same 15-pixel band = same line

    return "\n".join(text for _box, text in sorted(blocks, key=key) if text.strip())
