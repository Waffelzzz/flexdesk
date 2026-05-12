FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100

RUN apt-get update && apt-get install -y --no-install-recommends \
    fonts-dejavu-core \
    postgresql-client \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /tmp/*

WORKDIR /app
COPY . .
RUN pip install --no-cache-dir uv
RUN uv pip install --system --no-cache -r requirements.txt
RUN chmod +x entrypoint.sh

EXPOSE 8000

CMD ["bash", "/app/entrypoint.sh"]
