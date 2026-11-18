"""What a folder listing contains, and which files are kept."""

from dataclasses import asdict, dataclass

# Only these files are kept. Drive sometimes reports a generic type
# (application/octet-stream) for uploads, so the extension is used as a fallback.
SUPPORTED_MIME_TYPES = {"application/pdf": "pdf", "image/png": "png", "image/jpeg": "jpg"}
EXTENSION_TO_MIME = {".pdf": "application/pdf", ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg"}


@dataclass(frozen=True)
class DriveFile:
    id: str
    name: str
    mime_type: str
    size: int | None  # in bytes; None when Drive does not report it

    @property
    def type_label(self) -> str:
        return SUPPORTED_MIME_TYPES.get(self.mime_type, "unknown")

    def to_dict(self) -> dict:
        return {**asdict(self), "type": self.type_label}


@dataclass(frozen=True)
class FolderListing:
    folder_id: str
    folder_name: str | None
    files: list[DriveFile]
    skipped: int  # items ignored because they are not PDFs or images (sub-folders included)


def supported_mime_type(mime_type: str, name: str) -> str | None:
    """The mime type to use for this file, or None if the file must be skipped."""
    if mime_type in SUPPORTED_MIME_TYPES:
        return mime_type
    lowered = name.lower()
    for extension, mapped in EXTENSION_TO_MIME.items():
        if lowered.endswith(extension):
            return mapped
    return None
