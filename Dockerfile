# ---- Sentiment API image ----
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=5000

WORKDIR /app

# Install dependencies first so this layer is cached between code changes
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Application code and every saved model version (rollback = change MODEL_VERSION)
COPY sentiment/ sentiment/
COPY app/ app/
COPY models/ models/

# Optional: pin the served model at build time (default: "current" in models/registry.json)
ARG MODEL_VERSION=""
ENV MODEL_VERSION=${MODEL_VERSION}

RUN useradd --create-home appuser && chown -R appuser /app
USER appuser

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request,os; urllib.request.urlopen(f'http://127.0.0.1:{os.environ.get(\"PORT\",\"5000\")}/health', timeout=4)" || exit 1

CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT} --workers 2 --threads 4 --timeout 60 app.wsgi:app"]
