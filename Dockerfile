# Backend: FastAPI + Tesseract with the English, French and Arabic models.
FROM python:3.12-slim-bookworm

# Tesseract OCR engine and language models (Apache-2.0), from Debian packages.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        tesseract-ocr tesseract-ocr-eng tesseract-ocr-fra tesseract-ocr-ara \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY app ./app

# Files are processed in parallel (MAX_WORKERS), one Tesseract process each. By default every
# Tesseract process also starts one OpenMP thread per CPU core, and they fight for the CPU:
# one thread per process is much faster here (measured, see docs/DECISIONS.md, 012).
ENV OMP_THREAD_LIMIT=1

# Do not run as root.
RUN useradd --create-home --uid 1000 app
USER app

EXPOSE 8000
HEALTHCHECK --interval=10s --timeout=5s --start-period=15s --retries=5 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health', timeout=3)"
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
