"""Optional OCR engine: a vision-language model served by a local Ollama (decision 007).

Off unless Ollama runs and the model is pulled (`ollama pull glm-ocr`). Our benchmark
showed GLM-OCR is excellent on French/English but invents text on Arabic, and it gives
no confidence score, so the pipeline flags its Arabic pages for review.
"""

import base64
import io
import json
import logging
import urllib.error
import urllib.request

from PIL import Image

from app.extraction.models import ExtractionError, PageMode
from app.extraction.ocr import OcrResult, prepare

logger = logging.getLogger(__name__)

# Each model has its own task prompt. GLM-OCR expects "Text Recognition:".
PROMPTS = {"glm-ocr": "Text Recognition:"}
DEFAULT_PROMPT = "Extract all the text in this image exactly as written, line by line. Output only the text."


class OllamaVisionOcr:
    reliable_for_arabic = False  # measured in benchmarks/README.md

    def __init__(self, model: str = "glm-ocr", url: str = "http://localhost:11434", timeout: float = 600):
        self.model = model
        self.name = model
        self.label = f"{model} via Ollama (optional AI model, slower, best for French/English layouts)"
        self._url = url.rstrip("/")
        self._timeout = timeout

    def is_available(self) -> bool:
        """True when Ollama answers and the model has been pulled."""
        try:
            with urllib.request.urlopen(f"{self._url}/api/tags", timeout=3) as response:
                names = [model["name"] for model in json.load(response).get("models", [])]
        except (OSError, ValueError):
            return False
        return any(name == self.model or name.startswith(self.model + ":") for name in names)

    def read(self, image: Image.Image, lang: str, page_mode: PageMode = PageMode.AUTO) -> OcrResult:
        buffer = io.BytesIO()
        prepare(image).save(buffer, format="PNG")
        payload = {
            "model": self.model,
            "prompt": PROMPTS.get(self.model.split(":")[0], DEFAULT_PROMPT),
            "images": [base64.b64encode(buffer.getvalue()).decode()],
            "stream": False,
            "options": {"temperature": 0},  # no creativity: we want a transcription
        }
        request = urllib.request.Request(
            f"{self._url}/api/generate",
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(request, timeout=self._timeout) as response:
                text = json.load(response).get("response", "")
        except (OSError, ValueError) as exc:
            logger.warning("Ollama call failed: %s", exc)
            raise ExtractionError(f"The {self.model} model did not answer. Is Ollama running?") from exc
        return OcrResult(text=text.strip(), confidence=None)
