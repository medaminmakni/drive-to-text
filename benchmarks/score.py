"""Rebuild one comparison table from several benchmark runs.

Engines can be run separately (for example GLM-OCR on a GPU machine, Tesseract elsewhere,
or one sample folder at a time). This script re-scores the saved raw outputs against the
current ground truth and prints a single summary:

    python benchmarks/score.py --runs benchmarks/results benchmarks/results_tesseract-best \
        --samples benchmarks/samples benchmarks/data/misraj
"""

import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from metrics import cer, wer, word_f1  # noqa: E402
from run import load_samples, make_summary  # noqa: E402

HERE = Path(__file__).parent


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--runs", nargs="+", type=Path, required=True, help="result folders written by run.py")
    parser.add_argument("--samples", nargs="+", type=Path, default=[HERE / "samples"])
    parser.add_argument("--out", type=Path, default=HERE / "results" / "combined.md")
    args = parser.parse_args()

    samples = {sample["file"]: sample for sample in load_samples(args.samples)}
    rows, seen = [], set()
    for run in args.runs:
        with (run / "results.csv").open(encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                key = (row["engine"], row["file"])
                sample = samples.get(row["file"])
                if sample is None or key in seen:
                    continue  # not in the current sample set, or already counted from another run
                seen.add(key)
                if not row["error"]:
                    output = run / "outputs" / row["engine"].replace(":", "_") / f"{Path(row['file']).stem}.txt"
                    text = output.read_text(encoding="utf-8")
                    row.update(
                        cer=round(cer(text, sample["truth"]), 4),
                        wer=round(wer(text, sample["truth"]), 4),
                        word_f1=round(word_f1(text, sample["truth"]), 4),
                    )
                row["group"] = sample["group"]
                row["seconds"] = float(row["seconds"])
                rows.append(row)

    summary = make_summary(rows)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(summary, encoding="utf-8")
    print(summary)


if __name__ == "__main__":
    main()
