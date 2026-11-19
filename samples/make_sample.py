"""Rebuild samples/sample-output.json from a public Drive folder, through the running API.

    python samples/make_sample.py <folder link> [--out file.json] [--lang eng+fra+ara] [--api http://localhost:8000]

It does what the web page does: list the folder, select every PDF and image, start a
batch, wait for it, then save the JSON export. Standard library only.
"""

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).parent


def call(api: str, method: str, path: str, body: dict | None = None) -> dict:
    data = json.dumps(body).encode() if body is not None else None
    request = urllib.request.Request(api + path, data=data, method=method, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        sys.exit(f"{method} {path} failed ({exc.code}): {exc.read().decode(errors='replace')}")
    except urllib.error.URLError as exc:
        sys.exit(f"Cannot reach the API at {api} ({exc.reason}). Is the backend running?")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("folder", help="public Google Drive folder link")
    parser.add_argument("--lang", default="eng+fra+ara", help="OCR languages (default: eng+fra+ara)")
    parser.add_argument("--api", default="http://localhost:8000", help="backend address")
    parser.add_argument("--out", default="sample-output.json", help="file name, saved next to this script")
    args = parser.parse_args()
    api = args.api.rstrip("/") + "/api"

    listing = call(api, "POST", "/folders", {"url": args.folder})
    files = listing["files"]
    print(f"{listing['folder_name']}: {len(files)} files, {listing['skipped']} skipped")
    if not files:
        sys.exit("No PDF or image in this folder.")

    batch = call(api, "POST", "/batches", {"url": args.folder, "file_ids": [f["id"] for f in files], "lang": args.lang})
    while batch["status"] != "completed":
        time.sleep(1)
        batch = call(api, "GET", f"/batches/{batch['batch_id']}")
        counts = batch["counts"]
        left = counts["pending"] + counts["processing"]
        print(f"\r  done {counts['done']}, failed {counts['failed']}, left {left}  ", end="")
    print()

    export = call(api, "GET", f"/batches/{batch['batch_id']}/export")
    output = HERE / args.out
    output.write_text(json.dumps(export, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    for file in export["files"]:
        result = file["result"] or {}
        confidence = result.get("confidence")
        print(
            f"  {file['status']:6} {file['name'][:32]:32} {result.get('method') or '-':15}"
            f" conf {'-' if confidence is None else round(confidence):>3}"
            f"  {'REVIEW' if result.get('needs_review') else ''}  {file['error'] or ''}"
        )
    print(f"Saved {output}")


if __name__ == "__main__":
    main()
