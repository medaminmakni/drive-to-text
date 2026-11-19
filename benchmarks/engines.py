"""OCR engines compared by the benchmark, behind one small interface.

Each engine gets an image path and the Tesseract language code of the sample
(for example "ara", "fra", "ara+fra") and returns the text it read.
Optional engines are imported lazily, so a missing package only disables that engine.
"""

import base64
import json
import urllib.request
from pathlib import Path


class EngineUnavailable(Exception):
    """The engine cannot run on this machine (package, binary or service missing)."""


class TesseractEngine:
    """Tesseract with a chosen model folder and page segmentation mode (psm).

    psm 3 (Tesseract's default) detects columns and blocks automatically.
    psm 6 reads the page as one block of text, line by line from top to bottom.
    """

    def __init__(self, name: str = "tesseract", tessdata_dir: str | None = None, psm: int | None = None):
        self.name = name
        self.tessdata_dir = tessdata_dir
        self.psm = psm
        try:
            import pytesseract

            pytesseract.get_tesseract_version()
        except Exception as exc:
            raise EngineUnavailable(f"Tesseract not usable: {exc}") from exc
        if tessdata_dir and not Path(tessdata_dir).is_dir():
            raise EngineUnavailable(f"tessdata folder not found: {tessdata_dir}")
        self._pytesseract = pytesseract

    def read(self, image_path: Path, lang: str) -> str:
        from PIL import Image

        config = f'--tessdata-dir "{self.tessdata_dir}"' if self.tessdata_dir else ""
        if self.psm is not None:
            config += f" --psm {self.psm}"
        with Image.open(image_path) as image:
            return self._pytesseract.image_to_string(image, lang=lang, config=config)


class EasyOcrEngine:
    """EasyOCR can only combine Arabic with English, so Arabic samples use ['ar', 'en']."""

    name = "easyocr"

    def __init__(self):
        try:
            import easyocr
        except ImportError as exc:
            raise EngineUnavailable("pip install easyocr") from exc
        self._easyocr = easyocr
        self._readers = {}

    def read(self, image_path: Path, lang: str) -> str:
        codes = ("ar", "en") if "ara" in lang else ("fr", "en") if "fra" in lang else ("en",)
        if codes not in self._readers:
            self._readers[codes] = self._easyocr.Reader(list(codes), gpu=False, verbose=False)
        lines = self._readers[codes].readtext(str(image_path), detail=0, paragraph=True)
        return "\n".join(lines)


class OllamaVisionEngine:
    """A vision-language model served by a local Ollama (https://ollama.com)."""

    DEFAULT_PROMPT = "Extract all the text in this image exactly as written, line by line. Output only the text."
    PROMPTS = {"glm-ocr": "Text Recognition:"}  # GLM-OCR expects its task prompt

    def __init__(self, model: str, url: str = "http://localhost:11434", timeout: int = 600):
        self.model = model
        self.name = f"ollama:{model}"
        self.url = url.rstrip("/")
        self.timeout = timeout
        try:
            with urllib.request.urlopen(f"{self.url}/api/tags", timeout=5) as response:
                models = [m["name"] for m in json.load(response).get("models", [])]
        except OSError as exc:
            raise EngineUnavailable(f"Ollama not reachable at {self.url}") from exc
        if not any(m == model or m.startswith(model + ":") for m in models):
            raise EngineUnavailable(f"model not pulled, run: ollama pull {model}")

    def read(self, image_path: Path, lang: str) -> str:
        prompt = self.PROMPTS.get(self.model.split(":")[0], self.DEFAULT_PROMPT)
        payload = {
            "model": self.model,
            "prompt": prompt,
            "images": [base64.b64encode(image_path.read_bytes()).decode()],
            "stream": False,
            "options": {"temperature": 0},
        }
        request = urllib.request.Request(
            f"{self.url}/api/generate",
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(request, timeout=self.timeout) as response:
            return json.load(response).get("response", "")


def build_engine(spec: str, tessdata_best: str | None = None, tessdata_fast: str | None = None):
    """Create an engine from a command-line name.

    Tesseract names accept a page segmentation mode suffix, for example tesseract-best@6.
    """
    if spec.startswith("tesseract"):
        base, _, psm = spec.partition("@")
        folders = {"tesseract": None, "tesseract-fast": tessdata_fast, "tesseract-best": tessdata_best}
        if base not in folders:
            raise EngineUnavailable(f"unknown engine '{spec}'")
        if base != "tesseract" and not folders[base]:
            raise EngineUnavailable(f"no model folder given for {base}")
        return TesseractEngine(spec, folders[base], int(psm) if psm else None)
    if spec == "easyocr":
        return EasyOcrEngine()
    if spec.startswith("ollama:"):
        return OllamaVisionEngine(spec.split(":", 1)[1])
    raise EngineUnavailable(f"unknown engine '{spec}'")
