FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app ./app
COPY ingestion ./ingestion
COPY migrations ./migrations
COPY alembic.ini .
COPY dashboard.py .

# Run as an unprivileged user rather than root.
RUN useradd --create-home --uid 1000 appuser
USER appuser

EXPOSE 8000 8501
