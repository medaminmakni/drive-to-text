"""Download Arabic book passages from KITAB-Bench (Hindawi subset, text labelled by humans).

    python benchmarks/fetch_kitab.py --count 20

Writes benchmarks/data/kitab_hindawi/ (git-ignored).
Source: https://huggingface.co/datasets/ahmedheakl/arocrbench_hindawi, part of KITAB-Bench
(https://github.com/mbzuai-oryx/KITAB-Bench, ACL 2025). Using the same subset as the paper
makes our numbers comparable with the published ones. Only downloaded locally, never redistributed.
"""

import argparse
import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from sampleset import save_sample, write_manifest  # noqa: E402

ROWS_API = "https://datasets-server.huggingface.co/rows"
DATASET = "ahmedheakl/arocrbench_hindawi"
OUT = Path(__file__).parent / "data" / "kitab_hindawi"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--count", type=int, default=20)
    args = parser.parse_args()

    query = urllib.parse.urlencode(
        {"dataset": DATASET, "config": "default", "split": "train", "offset": 0, "length": min(args.count, 100)}
    )
    with urllib.request.urlopen(f"{ROWS_API}?{query}", timeout=60) as response:
        items = [item["row"] for item in json.load(response)["rows"]]

    rows = []
    for index, row in enumerate(items):
        with urllib.request.urlopen(row["image"]["src"], timeout=60) as response:
            image = response.read()
        suffix = ".png" if image.startswith(b"\x89PNG") else ".jpg"
        name = f"kitab_hindawi_{index:03d}{suffix}"
        save_sample(OUT, name, image, row["text"])
        rows.append({"file": name, "lang": "ara", "group": "arabic_books", "description": "KITAB-Bench Hindawi passage"})
        print(f"saved {name}")
    write_manifest(OUT, rows)


if __name__ == "__main__":
    main()
