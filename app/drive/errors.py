"""Errors raised while reading Google Drive. Every message can be shown to the user as is."""


class DriveError(Exception):
    """Base class for all Drive problems."""


class InvalidDriveLinkError(DriveError):
    """The text is not a usable Google Drive folder link."""


class FolderNotAccessibleError(DriveError):
    """The folder does not exist, is not public, or the link points to a file."""


class DriveServiceError(DriveError):
    """Google Drive could not be reached or refused the request (key, quota, outage)."""


class FileTooLargeError(DriveError):
    """The file is bigger than the configured download limit."""
