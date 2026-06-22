#!/bin/sh
set -e
: "${KPGEN_CATALOG_DB:=/app/data/kpgen.sqlite}"
mkdir -p "$(dirname "$KPGEN_CATALOG_DB")"
if [ ! -f "$KPGEN_CATALOG_DB" ]; then
  echo "Каталог не найден — строю из фида pech.ru..."
  python -m kpgen.catalog.refresh
fi
exec "$@"
