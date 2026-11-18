import pytest

from app.drive.errors import InvalidDriveLinkError
from app.drive.links import extract_folder_id

FOLDER_ID = "1AbCdEfGhIjKlMnOpQrStUv"


@pytest.mark.parametrize(
    "link",
    [
        f"https://drive.google.com/drive/folders/{FOLDER_ID}",
        f"https://drive.google.com/drive/folders/{FOLDER_ID}?usp=sharing",
        f"https://drive.google.com/drive/folders/{FOLDER_ID}/",
        f"https://drive.google.com/drive/u/1/folders/{FOLDER_ID}",
        f"drive.google.com/drive/folders/{FOLDER_ID}",
        f"https://drive.google.com/open?id={FOLDER_ID}",
        f"   https://drive.google.com/drive/folders/{FOLDER_ID}   ",
    ],
)
def test_accepts_the_real_folder_link_formats(link):
    assert extract_folder_id(link) == FOLDER_ID


@pytest.mark.parametrize(
    "link, message",
    [
        ("", "paste a Google Drive folder link"),
        ("hello", "not a Google Drive link"),
        (f"https://evil.com/drive/folders/{FOLDER_ID}", "not a Google Drive link"),
        (f"https://drive.google.com/file/d/{FOLDER_ID}/view", "single file"),
        ("https://drive.google.com/drive/my-drive", "Could not find a folder id"),
        ("https://drive.google.com/open?id=short", "Could not find a folder id"),
        ("https://drive.google.com/drive/folders/abc' or name contains 'x", "Could not find a folder id"),
    ],
)
def test_rejects_bad_links_with_a_clear_message(link, message):
    with pytest.raises(InvalidDriveLinkError, match=message):
        extract_folder_id(link)
