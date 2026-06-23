# python:3.12 — пакет требует Python >=3.11 (образ Playwright -jammy несёт только 3.10).
# Chromium и его системные зависимости ставит сам Playwright через --with-deps.
FROM python:3.12-slim-bookworm

WORKDIR /app

# 1) Зависимости + Chromium — отдельным слоем (кэшируется, не пересобирается при правках кода)
RUN pip install --no-cache-dir \
      "fastapi>=0.110" "uvicorn[standard]>=0.29" "jinja2>=3.1" "lxml>=5.2" \
      "httpx>=0.27" "playwright>=1.44" "python-multipart>=0.0.9" \
    && python -m playwright install --with-deps chromium

# 2) Код приложения — меняется часто, ставим только сам пакет (зависимости уже стоят)
COPY pyproject.toml ./
COPY src ./src
RUN pip install --no-cache-dir --no-deps .

COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

ENV KPGEN_CATALOG_DB=/app/data/kpgen.sqlite \
    KPGEN_PROPOSALS_DB=/app/data/proposals.sqlite
EXPOSE 8000
ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["uvicorn", "kpgen.web.main:app", "--host", "0.0.0.0", "--port", "8000"]
