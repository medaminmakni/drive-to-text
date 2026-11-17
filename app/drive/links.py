"""Turn a Google Drive folder link into a folder id."""

import re
from urllib.parse import parse_qs, urlparse

from app.drive.errors import InvalidDriveLinkError

DRIVE_HOSTS = {"drive.google.com", "www.drive.google.com"}
# Drive ids only use letters, digits, "-" and "_". Accepting nothing else also means
# the id can be placed safely inside a Drive API query.
FOLDER_PATH = re.compile(r"^/drive/(?:u/\d+/)?folders/([A-Za-z0-9_-]{10,})/?$")
VALID_ID = re.compile(r"^[A-Za-z0-9_-]{10,}$")


def extract_folder_id(link: str) -> str:
    """Return the folder id from a public folder link.

    Accepted forms:
        https://drive.google.com/drive/folders/<id>?usp=sharing
        https://drive.google.com/drive/u/0/folders/<id>
        https://drive.google.com/open?id=<id>
    """
    text = (link or "").strip()
    if not text:
        raise InvalidDriveLinkError("Please paste a Google Drive folder link.")
    if "://" not in text:
        text = "https://" + text

    parsed = urlparse(text)
    if parsed.hostname not in DRIVE_HOSTS:
        raise InvalidDriveLinkError("This is not a Google Drive link.")

    if parsed.path.startswith("/file/"):
        raise InvalidDriveLinkError("This link points to a single file. Please share the folder link instead.")

    match = FOLDER_PATH.match(parsed.path)
    if match:
        return match.group(1)

    if parsed.path == "/open":
        folder_id = parse_qs(parsed.query).get("id", [""])[0]
        if VALID_ID.match(folder_id):
            return folder_id

    raise InvalidDriveLinkError("Could not find a folder id in this link.")
