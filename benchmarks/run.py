"""Compare OCR engines on samples with a known ground truth.

Usage (from the repository root):
    python benchmarks/run.py --engines tesseract tesseract-best easyocr ollama:glm-ocr

Each sample folder contains images, one .txt ground truth per image (same name) and a
manifest.csv with the columns: file, lang, group, description.
Results go to benchmarks/results/: results.csv, summary.md and the raw outputs.
"""

import argparse
import csv
import statistics
import sys
import time
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from engines import EngineUnavailable, build_engine  # noqa: E402
from metrics import cer, wer, word_f1  # noqa: E402

HERE = Path(__file__).parent


def load_samples(folders: list[Path]) -> list[dict]:
    samples = []
    for folder in folders:
        manifest = folder / "manifest.csv"
        if not manifest.exists():
            print(f"skip {folder}: no manifest.csv")
            continue
        with manifest.open(encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                image = folder / row["file"]
                truth = image.with_suffix(".txt")
                samples.append({**row, "image": image, "truth": truth.read_text(encoding="utf-8")})
    return samples


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--engines", nargs="+", default=["tesseract"])
    parser.add_argument("--samples", nargs="+", type=Path, default=[HERE / "samples"],
                        help="sample folders (default: benchmarks/samples)")
    parser.add_argument("--tessdata-best", default=str(HERE / "data" / "tessdata_best"))
    parser.add_argument("--tessdata-fast", default=str(HERE / "data" / "tessdata_fast"),
                        help="folder with the standard (fast) models, if Tesseract's own folder lacks a language")
    parser.add_argument("--out", type=Path, default=HERE / "results")
    args = parser.parse_args()

    samples = load_samples(args.samples)
    if not samples:
        sys.exit("No samples found.")

    engines = []
    for spec in args.engines:
        try:
            engines.append(build_engine(spec, args.tessdata_best, args.tessdata_fast))
        except EngineUnavailable as exc:
            print(f"[skip] {spec}: {exc}")
    if not engines:
        sys.exit("No engine available.")

    rows = []
    for engine in engines:
        out_dir = args.out / "outputs" / engine.name.replace(":", "_")
        out_dir.mkdir(parents=True, exist_ok=True)
        for sample in samples:
            started = time.perf_counter()
            try:
                text, error = engine.read(sample["image"], sample["lang"]), ""
            except Exception as exc:  # one failing sample must not stop the benchmark
                text, error = "", f"{type(exc).__name__}: {exc}"
            seconds = time.perf_counter() - started
            (out_dir / f"{sample['image'].stem}.txt").write_text(text, encoding="utf-8")
            row = {
                "engine": engine.name,
                "file": sample["file"],
                "group": sample["group"],
                "cer": round(cer(text, sample["truth"]), 4) if not error else "",
                "wer": round(wer(text, sample["truth"]), 4) if not error else "",
                "word_f1": round(word_f1(text, sample["truth"]), 4) if not error else "",
                "seconds": round(seconds, 2),
                "error": error,
            }
            rows.append(row)
            shown = f"CER {row['cer']:.3f}  word F1 {row['word_f1']:.3f}" if not error else f"ERROR {error}"
            print(f"{engine.name:22} {sample['file']:32} {shown:30} {seconds:6.2f}s")

    args.out.mkdir(parents=True, exist_ok=True)
    with (args.out / "results.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    summary = make_summary(rows)
    (args.out / "summary.md").write_text(summary, encoding="utf-8")
    print("\n" + summary)


def make_summary(rows: list[dict]) -> str:
    """Mean CER per engine and sample group, plus mean seconds per image."""
    groups = sorted({row["group"] for row in rows})
    by_cell = defaultdict(list)
    seconds = defaultdict(list)
    f1 = defaultdict(list)
    failures = defaultdict(int)
    for row in rows:
        if row["error"]:
            failures[row["engine"]] += 1
            continue
        by_cell[(row["engine"], row["group"])].append(row["cer"])
        by_cell[(row["engine"], "all")].append(row["cer"])
        seconds[row["engine"]].append(row["seconds"])
        f1[row["engine"]].append(row["word_f1"])

    header = ["Engine", *[f"CER {g}" for g in groups], "CER all", "word F1 all", "s / image", "failed"]
    lines = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    for engine in dict.fromkeys(row["engine"] for row in rows):
        cells = [engine]
        for group in [*groups, "all"]:
            values = by_cell.get((engine, group))
            cells.append(f"{statistics.mean(values):.3f}" if values else "n/a")
        cells.append(f"{statistics.mean(f1[engine]):.3f}" if f1[engine] else "n/a")
        cells.append(f"{statistics.mean(seconds[engine]):.2f}" if seconds[engine] else "n/a")
        cells.append(str(failures[engine]))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines) + ("\n\nCER = character error rate, lower is better (also counts reading-order mistakes). "
                                   "Word F1 = share of the right words found in any order, higher is better. "
                                   "Arabic diacritics, alef forms and digits are normalized before scoring.\n")


if __name__ == "__main__":
    main()
