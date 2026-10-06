# Flood Risk DSS backend (FastAPI)
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /srv/app

# psycopg2-binary needs libpq headers only at build for source builds;
# we install the binary wheel, but keep gcc for safety with pinned wheels.
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY app ./app

EXPOSE 8000

# Overridable at runtime (see docker-compose.yml / docs/deployment.md).
# --proxy-headers trusts X-Forwarded-For/Proto from the nginx reverse proxy
# documented in docs/deployment-guide.md (nginx terminates TLS).
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2", "--proxy-headers"]
