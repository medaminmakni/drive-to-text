"""Google Drive API v3 client for public folders, authenticated with an API key only."""

import logging

import requests

from app.drive.errors import DriveServiceError, FileTooLargeError, FolderNotAccessibleError
from app.drive.models import DriveFile, FolderListing, supported_mime_type

logger = logging.getLogger(__name__)

FILES_URL = "https://www.googleapis.com/drive/v3/files"
FOLDER_MIME_TYPE = "application/vnd.google-apps.folder"
PAGE_SIZE = 1000
CHUNK_SIZE = 64 * 1024


class DriveApiClient:
    """Lists and downloads files of a public folder.

    The HTTP session is a parameter so tests can replace Google with fake responses.
    """

    def __init__(self, api_key: str, timeout: float = 30, session: requests.Session | None = None):
        self._api_key = api_key
        self._timeout = timeout
        self._session = session or requests.Session()

    # ---- listing ---------------------------------------------------------------

    def list_folder(self, folder_id: str) -> FolderListing:
        folder = self._get_folder(folder_id)
        files: list[DriveFile] = []
        skipped = 0

        for item in self._iter_children(folder_id):
            name = item.get("name", item["id"])
            mime_type = supported_mime_type(item.get("mimeType", ""), name)
            if mime_type is None:
                skipped += 1
                continue
            size = item.get("size")
            files.append(DriveFile(item["id"], name, mime_type, int(size) if size is not None else None))

        files.sort(key=lambda file: file.name.lower())
        return FolderListing(folder_id, folder.get("name"), files, skipped)

    def _get_folder(self, folder_id: str) -> dict:
        """Check that the id is a public folder before listing it.

        With an API key, listing a private folder does not fail: it returns an empty list.
        Reading the folder itself first is what lets us say "private" instead of "empty".
        """
        folder = self._get_json(f"{FILES_URL}/{folder_id}", {"fields": "id, name, mimeType", "supportsAllDrives": "true"})
        if folder.get("mimeType") != FOLDER_MIME_TYPE:
            raise FolderNotAccessibleError("This link points to a file, not a folder.")
        return folder

    def _iter_children(self, folder_id: str):
        params = {
            "q": f"'{folder_id}' in parents and trashed = false",
            "fields": "nextPageToken, files(id, name, mimeType, size)",
            "pageSize": PAGE_SIZE,
            "supportsAllDrives": "true",
            "includeItemsFromAllDrives": "true",
        }
        while True:
            page = self._get_json(FILES_URL, params)
            yield from page.get("files", [])
            token = page.get("nextPageToken")
            if not token:
                return
            params = {**params, "pageToken": token}

    # ---- download --------------------------------------------------------------

    def download(self, file: DriveFile, max_bytes: int) -> bytes:
        """Download a file, refusing anything above max_bytes without reading it all."""
        if file.size is not None and file.size > max_bytes:
            raise FileTooLargeError(_too_large(max_bytes))

        try:
            response = self._session.get(
                f"{FILES_URL}/{file.id}",
                params={"alt": "media", "supportsAllDrives": "true", "key": self._api_key},
                timeout=self._timeout,
                stream=True,
            )
        except requests.RequestException as exc:
            raise DriveServiceError("Could not reach Google Drive to download the file.") from exc

        with response:
            if response.status_code != 200:
                raise _error_from(response)
            content = bytearray()
            for chunk in response.iter_content(CHUNK_SIZE):
                content.extend(chunk)
                if len(content) > max_bytes:  # size was unknown, stop as soon as it is too big
                    raise FileTooLargeError(_too_large(max_bytes))
        return bytes(content)

    # ---- HTTP helpers ------------------------------------------------------------

    def _get_json(self, url: str, params: dict) -> dict:
        try:
            response = self._session.get(url, params={**params, "key": self._api_key}, timeout=self._timeout)
        except requests.RequestException as exc:
            raise DriveServiceError("Could not reach Google Drive. Check your internet connection.") from exc
        if response.status_code != 200:
            raise _error_from(response)
        return response.json()


def _error_from(response: requests.Response) -> Exception:
    """Map a Drive API error response to a clear, user-facing error."""
    reason, message = _error_details(response)
    logger.warning("Drive API error %s: %s %s", response.status_code, reason, message)

    if response.status_code == 404:
        return FolderNotAccessibleError(
            'Folder not found. Check the link and share the folder as "Anyone with the link".'
        )
    if "API key not valid" in message or reason == "keyInvalid":
        return DriveServiceError("The Google API key is not valid. Check GOOGLE_API_KEY in your .env file.")
    if reason in ("accessNotConfigured", "SERVICE_DISABLED") or "has not been used in project" in message:
        return DriveServiceError("The Google Drive API is not enabled for this API key's project.")
    if reason in ("rateLimitExceeded", "userRateLimitExceeded", "dailyLimitExceeded") or response.status_code == 429:
        return DriveServiceError("Google Drive rate limit reached. Please try again in a minute.")
    if response.status_code == 403:
        return FolderNotAccessibleError("Access denied. The folder or file is probably not public.")
    return DriveServiceError(f"Google Drive returned an unexpected error ({response.status_code}).")


def _error_details(response: requests.Response) -> tuple[str, str]:
    try:
        error = response.json().get("error", {})
    except ValueError:
        return "", response.text[:200]
    errors = error.get("errors") or [{}]
    return errors[0].get("reason", "") or error.get("status", ""), error.get("message", "")


def _too_large(max_bytes: int) -> str:
    return f"File is larger than the {max_bytes // (1024 * 1024)} MB limit."
