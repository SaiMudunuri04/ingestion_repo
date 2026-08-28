FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN addgroup --system ingestion \
    && adduser --system --ingroup ingestion --no-create-home ingestion

COPY requirements.txt ./

RUN python -m pip install --no-cache-dir -r requirements.txt

COPY --chown=ingestion:ingestion src/ ./src/

USER ingestion

CMD ["python", "-m", "worker"]
