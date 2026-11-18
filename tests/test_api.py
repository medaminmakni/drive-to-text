import time

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient  # noqa: E402

from app.config import Settings  # noqa: E402
from app.drive.errors import FolderNotAccessibleError  # noqa: E402
from app.drive.models import DriveFile, FolderListing  # noqa: E402
from app.extraction.ocr import OcrResult  # noqa: E402
from app.main import create_app  # noqa: E402
from tests.factories import image_bytes, native_pdf  # noqa: E402

FOLDER_ID = "1AbCdEfGhIjKlMnOpQ"
URL = f"https://drive.google.com/drive/folders/{FOLDER_ID}"
FILES = [DriveFile("pdf1", "contrat.pdf", "application/pdf", 1200), DriveFile("img1", "recu.png", "image/png", 3400)]
CONTENT = {"pdf1": native_pdf("Contrat de location Sfax 2026"), "img1": image_bytes("x")}


class FakeDrive:
    def list_folder(self, folder_id):
        if folder_id != FOLDER_ID:
            raise FolderNotAccessibleError('Folder not found. Share it as "Anyone with the link".')
        return FolderListing(FOLDER_ID, "Test folder", FILES, skipped=1)

    def download(self, file, max_bytes):
        return CONTENT[file.id]


class FakeOcr:
    def __init__(self, name, available=True, reliable_for_arabic=True, languages=("eng", "fra", "ara")):
        self.name, self.label = name, f"{name} engine"
        self.available, self.reliable_for_arabic = available, reliable_for_arabic
        self.languages = list(languages)

    def is_available(self):
        return self.available

    def installed_languages(self):
        return self.languages

    def read(self, image, lang, page_mode):
        return OcrResult(f"text read by {self.name}", 88.0)


@pytest.fixture
def client():
    engines = {"tesseract": FakeOcr("tesseract"), "glm-ocr": FakeOcr("glm-ocr", available=False, reliable_for_arabic=False)}
    app = create_app(Settings(google_api_key="test"), drive=FakeDrive(), engines=engines)
    with TestClient(app) as test_client:
        yield test_client


def wait(client, batch_id):
    for _ in range(200):
        state = client.get(f"/api/batches/{batch_id}").json()
        if state["status"] == "completed":
            return state
        time.sleep(0.02)
    raise AssertionError("the batch did not finish")


def test_config_lists_engines_languages_and_page_modes(client):
    data = client.get("/api/config").json()
    assert [(e["name"], e["available"]) for e in data["engines"]] == [("tesseract", True), ("glm-ocr", False)]
    assert data["default_engine"] == "tesseract"
    assert [(lang["code"], lang["installed"]) for lang in data["languages"]] == [
        ("eng", True),
        ("fra", True),
        ("ara", True),
    ]
    assert [mode["value"] for mode in data["page_modes"]] == ["auto", "single_block"]


def test_missing_tesseract_language_is_listed_and_refused():
    engines = {"tesseract": FakeOcr("tesseract", languages=["eng"])}
    app = create_app(Settings(google_api_key="test"), drive=FakeDrive(), engines=engines)
    with TestClient(app) as client:
        languages = client.get("/api/config").json()["languages"]
        assert [(lang["code"], lang["installed"]) for lang in languages] == [
            ("eng", True),
            ("fra", False),
            ("ara", False),
        ]
        response = client.post("/api/batches", json={"url": URL, "file_ids": ["img1"], "lang": "ara+eng"})
        assert response.status_code == 400
        assert "Arabic is not installed" in response.json()["detail"]


def test_list_folder(client):
    data = client.post("/api/folders", json={"url": URL}).json()
    assert data["folder_name"] == "Test folder" and data["skipped"] == 1
    assert data["files"][0] == {"id": "pdf1", "name": "contrat.pdf", "mime_type": "application/pdf",
                                "size": 1200, "type": "pdf"}


@pytest.mark.parametrize(
    "url, status",
    [("https://example.com/x", 400), ("https://drive.google.com/drive/folders/1PrivateFolder00", 404)],
)
def test_bad_or_private_links_return_clear_errors(client, url, status):
    response = client.post("/api/folders", json={"url": url})
    assert response.status_code == status
    assert isinstance(response.json()["detail"], str)


def test_full_batch_flow_and_export(client):
    response = client.post("/api/batches", json={"url": URL, "file_ids": ["pdf1", "img1"], "lang": "fra"})
    assert response.status_code == 202
    state = wait(client, response.json()["batch_id"])

    by_name = {file["name"]: file for file in state["files"]}
    assert by_name["contrat.pdf"]["result"]["method"] == "pdf_parser"
    assert "Contrat de location" in by_name["contrat.pdf"]["result"]["text"]
    assert by_name["recu.png"]["result"]["method"] == "ocr"
    assert by_name["recu.png"]["result"]["confidence"] == 88.0
    assert state["options"]["lang"] == "fra"

    export = client.get(f"/api/batches/{state['batch_id']}/export")
    assert "attachment" in export.headers["content-disposition"]
    assert export.json()["batch_id"] == state["batch_id"]


@pytest.mark.parametrize(
    "body, message",
    [
        ({"file_ids": ["other"]}, "no longer in this folder"),
        ({"file_ids": ["pdf1"], "lang": "deu"}, "Unsupported OCR language"),
        ({"file_ids": ["pdf1"], "engine": "glm-ocr"}, "not available"),
    ],
)
def test_batch_rejects_bad_requests(client, body, message):
    response = client.post("/api/batches", json={"url": URL, **body})
    assert response.status_code == 400
    assert message in response.json()["detail"]


def test_batch_needs_at_least_one_file(client):
    assert client.post("/api/batches", json={"url": URL, "file_ids": []}).status_code == 422


def test_unknown_batch_returns_404(client):
    assert client.get("/api/batches/nope").status_code == 404


def test_missing_api_key_is_explained():
    app = create_app(Settings(google_api_key=None), engines={"tesseract": FakeOcr("tesseract")})
    with TestClient(app) as test_client:
        response = test_client.post("/api/folders", json={"url": URL})
    assert response.status_code == 502
    assert "GOOGLE_API_KEY" in response.json()["detail"]
