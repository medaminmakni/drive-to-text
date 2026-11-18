import time

from app.batches import BatchManager
from app.drive.errors import FileTooLargeError
from app.drive.models import DriveFile
from app.extraction.models import ExtractionError, ExtractionResult, ExtractOptions, Method, PageMode, PageResult


class FakeDrive:
    def __init__(self, contents):
        self.contents = contents

    def download(self, file, max_bytes):
        content = self.contents[file.id]
        if isinstance(content, Exception):
            raise content
        return content


class FakeExtractor:
    def __init__(self):
        self.options = []

    def extract(self, data, mime_type="", options=None):
        self.options.append(options)
        if data == b"broken":
            raise ExtractionError("This PDF is damaged or not a valid PDF.")
        if data == b"bug":
            raise RuntimeError("unexpected")
        return ExtractionResult(pages=[PageResult(1, data.decode(), Method.PDF_PARSER)])


def files(*ids):
    return [DriveFile(i, f"{i}.pdf", "application/pdf", 10) for i in ids]


def wait(manager, batch_id, timeout=5):
    deadline = time.time() + timeout
    while time.time() < deadline:
        state = manager.snapshot(batch_id)
        if state["status"] == "completed":
            return state
        time.sleep(0.02)
    raise AssertionError("the batch did not finish")


def test_one_failing_file_never_stops_the_batch():
    drive = FakeDrive({"ok": b"hello", "bad": b"broken", "big": FileTooLargeError("too big"), "bug": b"bug"})
    manager = BatchManager(drive, FakeExtractor(), max_file_bytes=1000, max_workers=2)

    state = wait(manager, manager.start("f", "Folder", files("ok", "bad", "big", "bug"), ExtractOptions()).id)
    by_id = {file["id"]: file for file in state["files"]}

    assert by_id["ok"]["status"] == "done"
    assert by_id["ok"]["result"]["text"] == "hello" and by_id["ok"]["result"]["method"] == "pdf_parser"
    assert by_id["bad"]["status"] == "failed" and "damaged" in by_id["bad"]["error"]
    assert by_id["big"]["error"] == "too big"
    assert by_id["bug"]["error"] == "Unexpected error while processing this file."
    assert state["counts"] == {"pending": 0, "processing": 0, "done": 1, "failed": 3}
    assert all(file["duration_ms"] is not None for file in state["files"])
    manager.shutdown()


def test_options_reach_the_extractor_and_the_snapshot():
    extractor = FakeExtractor()
    manager = BatchManager(FakeDrive({"a": b"x"}), extractor, max_file_bytes=1000)
    options = ExtractOptions(lang="ara+fra", page_mode=PageMode.SINGLE_BLOCK, engine="tesseract")

    state = wait(manager, manager.start("f", "Invoices", files("a"), options).id)

    assert extractor.options == [options]
    assert state["options"] == {"lang": "ara+fra", "page_mode": "single_block", "engine": "tesseract"}
    assert state["folder_name"] == "Invoices"
    assert state["files"][0]["type"] == "pdf"
    manager.shutdown()


def test_new_batch_starts_with_pending_files():
    manager = BatchManager(FakeDrive({"a": b"x"}), FakeExtractor(), max_file_bytes=1000, max_workers=1)
    batch = manager.start("f", None, files("a"), ExtractOptions())
    assert batch.to_dict()["files"][0]["status"] in ("pending", "processing", "done")
    manager.shutdown()


def test_unknown_batch():
    manager = BatchManager(FakeDrive({}), FakeExtractor(), max_file_bytes=1000)
    assert manager.snapshot("nope") is None
    manager.shutdown()
