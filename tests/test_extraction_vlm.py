import base64
import io
import json

from PIL import Image

from app.extraction.models import ExtractionError
from app.extraction.vlm import OllamaVisionOcr
from tests.factories import text_image


class FakeHttpResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def test_not_available_when_ollama_is_not_running():
    assert OllamaVisionOcr(url="http://127.0.0.1:9").is_available() is False


def test_available_only_when_the_model_is_pulled(monkeypatch):
    tags = json.dumps({"models": [{"name": "glm-ocr:latest"}]}).encode()
    monkeypatch.setattr("urllib.request.urlopen", lambda *a, **k: FakeHttpResponse(tags))
    assert OllamaVisionOcr("glm-ocr").is_available()
    assert not OllamaVisionOcr("qwen2.5vl").is_available()


def test_read_sends_the_glm_prompt_and_returns_text_without_confidence(monkeypatch):
    sent = {}

    def fake_urlopen(request, timeout):
        sent.update(json.loads(request.data))
        return FakeHttpResponse(json.dumps({"response": " Facture 2026 \n"}).encode())

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    result = OllamaVisionOcr("glm-ocr").read(text_image("x"), "fra")

    assert result.text == "Facture 2026" and result.confidence is None
    assert sent["prompt"] == "Text Recognition:" and sent["options"]["temperature"] == 0
    assert Image.open(io.BytesIO(base64.b64decode(sent["images"][0]))).format == "PNG"


def test_unreachable_model_gives_a_clear_error(monkeypatch):
    def broken(*a, **k):
        raise OSError("connection refused")

    monkeypatch.setattr("urllib.request.urlopen", broken)
    try:
        OllamaVisionOcr("glm-ocr").read(text_image("x"), "fra")
    except ExtractionError as exc:
        assert "Is Ollama running" in str(exc)
    else:
        raise AssertionError("expected an ExtractionError")
