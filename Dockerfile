# python:3.12 — пакет требует Python >=3.11 (образ Playwright -jammy несёт только 3.10).
# Chromium и его системные зависимости ставит сам Playwright через --with-deps.
FROM python:3.12-slim-bookworm

WORKDIR /app
COPY pyproject.toml ./
COPY src ./src
RUN pip install --no-cache-dir . && python -m playwright install --with-deps chromium

COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

ENV KPGEN_CATALOG_DB=/app/data/kpgen.sqlite \
    KPGEN_PROPOSALS_DB=/app/data/proposals.sqlite
EXPOSE 8000
ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["uvicorn", "kpgen.web.main:app", "--host", "0.0.0.0", "--port", "8000"]
