"""Batch processing: the selected files are downloaded and extracted in background threads.

Each file has its own status (pending -> processing -> done | failed) and its own error
handling, so one failing file never stops the rest of the batch (decision 009).
Batches are kept in memory, which is enough for a proof of concept (decision 010).
"""

import logging
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Protocol

from app.drive.errors import DriveError
from app.drive.models import DriveFile
from app.extraction.models import ExtractionError, ExtractionResult, ExtractOptions

logger = logging.getLogger(__name__)


class FileStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    DONE = "done"
    FAILED = "failed"


class Downloader(Protocol):
    def download(self, file: DriveFile, max_bytes: int) -> bytes: ...


class TextExtractor(Protocol):
    def extract(self, data: bytes, mime_type: str = "", options: ExtractOptions | None = None) -> ExtractionResult: ...


@dataclass
class FileJob:
    file: DriveFile
    status: FileStatus = FileStatus.PENDING
    error: str | None = None
    duration_ms: int | None = None
    result: ExtractionResult | None = None

    def to_dict(self) -> dict:
        return {
            "id": self.file.id,
            "name": self.file.name,
            "type": self.file.type_label,
            "size": self.file.size,
            "status": self.status.value,
            "error": self.error,
            "duration_ms": self.duration_ms,
            "result": self.result.to_dict() if self.result else None,
        }


@dataclass
class Batch:
    id: str
    folder_id: str
    folder_name: str | None
    options: ExtractOptions
    jobs: list[FileJob]
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat(timespec="seconds"))

    @property
    def completed(self) -> bool:
        return all(job.status in (FileStatus.DONE, FileStatus.FAILED) for job in self.jobs)

    def to_dict(self) -> dict:
        counts = {status.value: 0 for status in FileStatus}
        for job in self.jobs:
            counts[job.status.value] += 1
        return {
            "batch_id": self.id,
            "folder_id": self.folder_id,
            "folder_name": self.folder_name,
            "created_at": self.created_at,
            "options": {
                "lang": self.options.lang,
                "page_mode": self.options.page_mode.value,
                "engine": self.options.engine,
            },
            "status": "completed" if self.completed else "running",
            "counts": counts,
            "files": [job.to_dict() for job in self.jobs],
        }


class BatchManager:
    def __init__(self, downloader: Downloader, extractor: TextExtractor, max_file_bytes: int, max_workers: int = 3):
        self._downloader = downloader
        self._extractor = extractor
        self._max_file_bytes = max_file_bytes
        self._executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="batch")
        self._batches: dict[str, Batch] = {}
        self._lock = threading.Lock()  # workers update jobs while the API reads them

    def start(self, folder_id: str, folder_name: str | None, files: list[DriveFile], options: ExtractOptions) -> Batch:
        batch = Batch(uuid.uuid4().hex[:12], folder_id, folder_name, options, [FileJob(file) for file in files])
        with self._lock:
            self._batches[batch.id] = batch
        for job in batch.jobs:
            self._executor.submit(self._process, job, options)
        return batch

    def snapshot(self, batch_id: str) -> dict | None:
        """A consistent copy of the batch, safe to send while workers are still running."""
        with self._lock:
            batch = self._batches.get(batch_id)
            return batch.to_dict() if batch else None

    def shutdown(self) -> None:
        self._executor.shutdown(wait=False, cancel_futures=True)

    def _update(self, job: FileJob, **changes) -> None:
        with self._lock:
            for name, value in changes.items():
                setattr(job, name, value)

    def _process(self, job: FileJob, options: ExtractOptions) -> None:
        started = time.perf_counter()
        self._update(job, status=FileStatus.PROCESSING)
        try:
            data = self._downloader.download(job.file, self._max_file_bytes)
            result = self._extractor.extract(data, job.file.mime_type, options)
        except (DriveError, ExtractionError) as exc:  # expected problems: their message is user-facing
            self._update(job, status=FileStatus.FAILED, error=str(exc), duration_ms=_ms_since(started))
        except Exception:  # a bug must not crash the worker or the batch
            logger.exception("Unexpected error while processing %s", job.file.name)
            self._update(
                job,
                status=FileStatus.FAILED,
                error="Unexpected error while processing this file.",
                duration_ms=_ms_since(started),
            )
        else:
            self._update(job, status=FileStatus.DONE, result=result, duration_ms=_ms_since(started))


def _ms_since(started: float) -> int:
    return round((time.perf_counter() - started) * 1000)
