import json

import pytest
import requests

from app.drive.client import DriveApiClient
from app.drive.errors import DriveServiceError, FileTooLargeError, FolderNotAccessibleError
from app.drive.models import DriveFile

FOLDER = {"id": "folder1", "name": "Invoices", "mimeType": "application/vnd.google-apps.folder"}


class FakeResponse:
    def __init__(self, status_code=200, payload=None, content=b""):
        self.status_code = status_code
        self._payload = payload if payload is not None else {}
        self._content = content
        self.text = json.dumps(self._payload)

    def json(self):
        return self._payload

    def iter_content(self, chunk_size):
        for start in range(0, len(self._content), chunk_size):
            yield self._content[start : start + chunk_size]

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class FakeSession:
    """Plays the role of Google: answers each request with the next queued response."""

    def __init__(self, *responses):
        self.responses = list(responses)
        self.calls = []

    def get(self, url, params=None, **kwargs):
        self.calls.append((url, params))
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


def client_with(*responses):
    session = FakeSession(*responses)
    return DriveApiClient("test-key", session=session), session


def drive_error(status, reason="", message=""):
    return FakeResponse(status, {"error": {"code": status, "message": message, "errors": [{"reason": reason}]}})


# ---- listing --------------------------------------------------------------------

def test_keeps_only_pdfs_and_images_sorted_by_name():
    children = {"files": [
        {"id": "a", "name": "scan.JPG", "mimeType": "image/jpeg", "size": "2048"},
        {"id": "b", "name": "notes.docx", "mimeType": "application/vnd.openxmlformats"},
        {"id": "c", "name": "Contract.pdf", "mimeType": "application/pdf", "size": "1000"},
        {"id": "d", "name": "photo.png", "mimeType": "application/octet-stream", "size": "10"},
        {"id": "e", "name": "Archive", "mimeType": "application/vnd.google-apps.folder"},
    ]}
    client, session = client_with(FakeResponse(payload=FOLDER), FakeResponse(payload=children))

    listing = client.list_folder("folder1")

    assert listing.folder_name == "Invoices"
    assert [f.name for f in listing.files] == ["Contract.pdf", "photo.png", "scan.JPG"]
    assert listing.files[1].mime_type == "image/png"  # generic type fixed from the extension
    assert listing.files[0].size == 1000
    assert listing.skipped == 2  # the .docx and the sub-folder
    assert session.calls[1][1]["q"] == "'folder1' in parents and trashed = false"
    assert session.calls[1][1]["key"] == "test-key"


def test_follows_every_page():
    page1 = {"files": [{"id": "a", "name": "a.pdf", "mimeType": "application/pdf"}], "nextPageToken": "next"}
    page2 = {"files": [{"id": "b", "name": "b.pdf", "mimeType": "application/pdf"}]}
    responses = [FakeResponse(payload=payload) for payload in (FOLDER, page1, page2)]
    client, session = client_with(*responses)

    listing = client.list_folder("folder1")

    assert [f.id for f in listing.files] == ["a", "b"]
    assert listing.files[0].size is None
    assert session.calls[2][1]["pageToken"] == "next"


def test_empty_public_folder():
    client, _ = client_with(FakeResponse(payload=FOLDER), FakeResponse(payload={"files": []}))
    listing = client.list_folder("folder1")
    assert listing.files == [] and listing.skipped == 0


def test_private_or_missing_folder_is_reported_not_listed_as_empty():
    client, session = client_with(drive_error(404, "notFound", "File not found: folder1."))
    with pytest.raises(FolderNotAccessibleError, match="Anyone with the link"):
        client.list_folder("folder1")
    assert len(session.calls) == 1  # the listing call is never made


def test_link_to_a_file_is_rejected():
    client, _ = client_with(FakeResponse(payload={"id": "x", "name": "a.pdf", "mimeType": "application/pdf"}))
    with pytest.raises(FolderNotAccessibleError, match="not a folder"):
        client.list_folder("x")


@pytest.mark.parametrize(
    "response, message",
    [
        (drive_error(400, "badRequest", "API key not valid. Please pass a valid API key."), "API key is not valid"),
        (drive_error(403, "accessNotConfigured", "Google Drive API has not been used in project 123"), "not enabled"),
        (drive_error(403, "userRateLimitExceeded", "Rate limit"), "rate limit"),
        (drive_error(429, "", "Too many requests"), "rate limit"),
        (drive_error(403, "forbidden", "Forbidden"), "not public"),
        (drive_error(500, "backendError", "Internal error"), "unexpected error \\(500\\)"),
    ],
)
def test_google_errors_become_clear_messages(response, message):
    client, _ = client_with(response)
    with pytest.raises((DriveServiceError, FolderNotAccessibleError), match=message):
        client.list_folder("folder1")


def test_no_internet_is_reported():
    client, _ = client_with(requests.ConnectionError("offline"))
    with pytest.raises(DriveServiceError, match="Could not reach Google Drive"):
        client.list_folder("folder1")


# ---- download -------------------------------------------------------------------

def test_download_returns_the_bytes():
    client, session = client_with(FakeResponse(content=b"%PDF-1.7 content"))
    data = client.download(DriveFile("a", "a.pdf", "application/pdf", 16), max_bytes=1000)
    assert data == b"%PDF-1.7 content"
    assert session.calls[0][1]["alt"] == "media"


def test_download_refuses_a_known_large_file_without_calling_google():
    client, session = client_with()
    with pytest.raises(FileTooLargeError, match="1 MB limit"):
        client.download(DriveFile("a", "big.pdf", "application/pdf", 5 * 1024 * 1024), max_bytes=1024 * 1024)
    assert session.calls == []


def test_download_stops_when_an_unknown_size_goes_over_the_limit():
    client, _ = client_with(FakeResponse(content=b"x" * 300_000))
    with pytest.raises(FileTooLargeError):
        client.download(DriveFile("a", "a.png", "image/png", None), max_bytes=100_000)


def test_download_of_a_private_file():
    client, _ = client_with(drive_error(404, "notFound", "File not found"))
    with pytest.raises(FolderNotAccessibleError):
        client.download(DriveFile("a", "a.pdf", "application/pdf", 10), max_bytes=1000)
