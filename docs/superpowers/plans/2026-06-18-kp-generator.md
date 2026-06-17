# Генератор КП «Печь.ру» — План реализации

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Локальное приложение, где менеджер собирает КП из товаров pech.ru и получает веб-ссылку `/kp/<id>` и PDF, оформленные по дизайн-системе из `prototype/`.

**Architecture:** Чистое ядро (парсер фида, индекс, прайсинг, модели) без зависимостей от веба; поверх — FastAPI с Jinja2-шаблонами (перенос из `prototype/preview/`) и Playwright для PDF из того же HTML. Данные о товарах — из YML-фида (SQLite FTS-индекс), КП — в отдельной SQLite-таблице.

**Tech Stack:** Python 3.11+, FastAPI, Uvicorn, Jinja2, Playwright (Chromium), SQLite (FTS5, через stdlib `sqlite3`), pytest. Парсинг XML — `lxml`. HTTP — `httpx`.

---

## File Structure

```
pyproject.toml                 # зависимости, конфиг pytest
.env.example                   # уже есть
src/kpgen/
  __init__.py
  config.py                    # загрузка env (URLs фидов, пути к БД/данным)
  models.py                    # dataclasses: Offer, LineItem, ServiceItem, Proposal, Manager, Client
  feed/
    __init__.py
    parser.py                  # YML offer -> Offer
  catalog/
    __init__.py
    index.py                   # build_index(offers) + search(query) на SQLite FTS5
  pricing.py                   # расчёт сумм, скидок, итога (чистые функции)
  store.py                     # SQLite CRUD для Proposal (save/load)
  scraper/
    __init__.py
    site.py                    # добор фото/описания с сайта + кэш (опционально, фаза 9)
  render/
    __init__.py
    html.py                    # Proposal -> HTML (Jinja2)
    pdf.py                     # HTML -> PDF (Playwright)
    templates/                 # Jinja2-шаблоны слайдов (перенос из prototype)
    static/                    # css/шрифты/иконки (перенос из дизайн-системы)
  web/
    __init__.py
    app.py                     # FastAPI: маршруты
tests/
  conftest.py
  fixtures/                    # маленькие срезы XML
  test_feed_parser.py
  test_catalog_index.py
  test_pricing.py
  test_store.py
  test_render_html.py
  test_render_pdf.py
  test_web.py
```

Файлы фидов для офлайн-разработки: `/Users/alex/Documents/Sites/Parsing/Kamindom/data/pech_products.xml`, `pech_sklade.xml`. В тестах используем маленькие фикстуры (несколько offer), не полный фид.

---

## Phase 1 — Каркас проекта

### Task 1: pyproject и зависимости

**Files:**
- Create: `pyproject.toml`
- Create: `src/kpgen/__init__.py`
- Create: `tests/__init__.py`

- [ ] **Step 1: Создать `pyproject.toml`**

```toml
[project]
name = "kpgen"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
  "fastapi>=0.110",
  "uvicorn[standard]>=0.29",
  "jinja2>=3.1",
  "lxml>=5.2",
  "httpx>=0.27",
  "playwright>=1.44",
  "python-multipart>=0.0.9",
]

[project.optional-dependencies]
dev = ["pytest>=8.2", "pytest-asyncio>=0.23"]

[tool.pytest.ini_options]
pythonpath = ["src"]
testpaths = ["tests"]
asyncio_mode = "auto"

[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"
```

- [ ] **Step 2: Создать пустые `src/kpgen/__init__.py` и `tests/__init__.py`**

```python
# src/kpgen/__init__.py
```

- [ ] **Step 3: Установить окружение**

Run:
```bash
python3 -m venv .venv && . .venv/bin/activate && pip install -e ".[dev]" && python -m playwright install chromium
```
Expected: установка без ошибок, Chromium скачан.

- [ ] **Step 4: Проверить, что pytest стартует**

Run: `. .venv/bin/activate && pytest -q`
Expected: `no tests ran` (или 0 collected) — без ошибок импорта.

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml src/kpgen/__init__.py tests/__init__.py
git commit -m "chore: scaffold kpgen package and deps"
```

### Task 2: Конфиг из окружения

**Files:**
- Create: `src/kpgen/config.py`
- Test: `tests/test_config.py`

- [ ] **Step 1: Написать падающий тест**

```python
# tests/test_config.py
import os
from kpgen.config import Config

def test_config_defaults(monkeypatch):
    monkeypatch.delenv("PECH_XML_URL", raising=False)
    cfg = Config.from_env()
    assert cfg.pech_xml_url == "https://www.pech.ru/list-products-1.xml"
    assert cfg.pech_sklade_xml_url == "https://www.pech.ru/pech-na-sklade.xml"
    assert cfg.db_path.endswith("kpgen.sqlite")

def test_config_env_override(monkeypatch):
    monkeypatch.setenv("PECH_XML_URL", "http://example/feed.xml")
    cfg = Config.from_env()
    assert cfg.pech_xml_url == "http://example/feed.xml"
```

- [ ] **Step 2: Запустить — убедиться, что падает**

Run: `pytest tests/test_config.py -v`
Expected: FAIL (ModuleNotFoundError: kpgen.config)

- [ ] **Step 3: Реализация**

```python
# src/kpgen/config.py
import os
from dataclasses import dataclass

@dataclass
class Config:
    pech_xml_url: str
    pech_sklade_xml_url: str
    db_path: str
    data_dir: str

    @classmethod
    def from_env(cls) -> "Config":
        return cls(
            pech_xml_url=os.getenv("PECH_XML_URL", "https://www.pech.ru/list-products-1.xml"),
            pech_sklade_xml_url=os.getenv("PECH_SKLADE_XML_URL", "https://www.pech.ru/pech-na-sklade.xml"),
            db_path=os.getenv("KPGEN_DB", os.path.join(os.getcwd(), "data", "kpgen.sqlite")),
            data_dir=os.getenv("KPGEN_DATA_DIR", os.path.join(os.getcwd(), "data")),
        )
```

- [ ] **Step 4: Запустить тест — должно пройти**

Run: `pytest tests/test_config.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add src/kpgen/config.py tests/test_config.py
git commit -m "feat: env-based config"
```

---

## Phase 2 — Модели и парсер фида

### Task 3: Доменные модели

**Files:**
- Create: `src/kpgen/models.py`
- Test: `tests/test_models.py`

- [ ] **Step 1: Падающий тест**

```python
# tests/test_models.py
from kpgen.models import Offer, LineItem, ServiceItem, Manager, Client, Proposal

def test_offer_minimal():
    o = Offer(offer_id="23954", name="Печь камин Guca Iskra", price=50000,
              old_price=None, vendor="Guca", category_id="157",
              url="https://www.pech.ru/x", picture="https://www.pech.ru/p.jpg",
              description="desc", params={"Мощность": "9 кВт"})
    assert o.offer_id == "23954"
    assert o.has_discount is False

def test_offer_discount_flag():
    o = Offer(offer_id="1", name="x", price=80, old_price=100, vendor="", category_id="",
              url="", picture="", description="", params={})
    assert o.has_discount is True

def test_lineitem_sum():
    o = Offer(offer_id="1", name="x", price=100, old_price=None, vendor="", category_id="",
              url="", picture="", description="", params={})
    li = LineItem(offer=o, qty=3)
    assert li.line_sum == 300
```

- [ ] **Step 2: Запустить — падает**

Run: `pytest tests/test_models.py -v`
Expected: FAIL (ModuleNotFoundError)

- [ ] **Step 3: Реализация**

```python
# src/kpgen/models.py
from dataclasses import dataclass, field

@dataclass
class Offer:
    offer_id: str
    name: str
    price: int
    old_price: int | None
    vendor: str
    category_id: str
    url: str
    picture: str
    description: str
    params: dict[str, str] = field(default_factory=dict)

    @property
    def has_discount(self) -> bool:
        return self.old_price is not None and self.old_price > self.price

@dataclass
class LineItem:
    offer: Offer
    qty: int = 1

    @property
    def line_sum(self) -> int:
        return self.offer.price * self.qty

@dataclass
class ServiceItem:
    title: str
    amount: int  # рубли, может быть отрицательной для скидки

@dataclass
class Manager:
    name: str
    role: str = "Старший менеджер"
    email: str = ""
    phone: str = ""

@dataclass
class Client:
    name: str
    date: str  # уже отформатированная строка, напр. "20 августа 2025 года"

@dataclass
class Proposal:
    id: str
    client: Client
    manager: Manager
    items: list[LineItem] = field(default_factory=list)
    services: list[ServiceItem] = field(default_factory=list)
    discount: int = 0  # скидка на КП в целом, рубли (положительное число)
```

- [ ] **Step 4: Тест проходит**

Run: `pytest tests/test_models.py -v`
Expected: PASS (3 passed)

- [ ] **Step 5: Commit**

```bash
git add src/kpgen/models.py tests/test_models.py
git commit -m "feat: domain models"
```

### Task 4: Фикстуры фида

**Files:**
- Create: `tests/fixtures/products_small.xml`
- Create: `tests/fixtures/sklade_small.xml`

- [ ] **Step 1: Создать `tests/fixtures/products_small.xml`** (структура основного фида: offer с params и без oldprice)

```xml
<?xml version="1.0" encoding="utf-8"?>
<yml_catalog><shop><offers>
<offer id="23954" type="vendor.model" available="true">
  <name>Печь камин Guca Iskra</name>
  <description>Чугунная печь-камин.</description>
  <vendor>Guca</vendor>
  <url>https://www.pech.ru/catalog/guca-iskra/</url>
  <picture>https://www.pech.ru/upload/guca.jpg</picture>
  <price>50000</price>
  <currencyId>RUR</currencyId>
  <categoryId>157</categoryId>
  <delivery>true</delivery>
  <param name="Мощность">9 кВт</param>
  <param name="Высота">1015 мм</param>
</offer>
</offers></shop></yml_catalog>
```

- [ ] **Step 2: Создать `tests/fixtures/sklade_small.xml`** (фид «на складе»: price = со скидкой, oldprice = РРЦ)

```xml
<?xml version="1.0" encoding="utf-8"?>
<yml_catalog><shop><offers>
<offer id="23954" type="vendor.model" available="true">
  <name>Печь камин Guca Iskra</name>
  <description>Чугунная печь-камин.</description>
  <vendor>Guca</vendor>
  <url>https://www.pech.ru/catalog/guca-iskra/</url>
  <picture>https://www.pech.ru/upload/guca.jpg</picture>
  <price>45000</price>
  <oldprice>50000</oldprice>
  <currencyId>RUR</currencyId>
  <categoryId>157</categoryId>
  <delivery>true</delivery>
</offer>
</offers></shop></yml_catalog>
```

- [ ] **Step 3: Commit**

```bash
git add tests/fixtures/products_small.xml tests/fixtures/sklade_small.xml
git commit -m "test: small feed fixtures"
```

### Task 5: Парсер фида

**Files:**
- Create: `src/kpgen/feed/__init__.py`
- Create: `src/kpgen/feed/parser.py`
- Test: `tests/test_feed_parser.py`

- [ ] **Step 1: Падающий тест**

```python
# tests/test_feed_parser.py
from pathlib import Path
from kpgen.feed.parser import parse_offers, merge_sklade

FX = Path(__file__).parent / "fixtures"

def test_parse_main_feed():
    offers = parse_offers(str(FX / "products_small.xml"))
    assert len(offers) == 1
    o = offers["23954"]
    assert o.name == "Печь камин Guca Iskra"
    assert o.price == 50000
    assert o.old_price is None
    assert o.vendor == "Guca"
    assert o.params["Мощность"] == "9 кВт"

def test_merge_sklade_sets_old_price():
    offers = parse_offers(str(FX / "products_small.xml"))
    merge_sklade(offers, str(FX / "sklade_small.xml"))
    o = offers["23954"]
    assert o.price == 45000        # цена со скидкой из sklade
    assert o.old_price == 50000    # РРЦ
    assert o.has_discount is True
```

- [ ] **Step 2: Запустить — падает**

Run: `pytest tests/test_feed_parser.py -v`
Expected: FAIL (ModuleNotFoundError)

- [ ] **Step 3: Реализация**

```python
# src/kpgen/feed/__init__.py
```
```python
# src/kpgen/feed/parser.py
from lxml import etree
from kpgen.models import Offer

def _text(el, tag: str) -> str:
    child = el.find(tag)
    return child.text.strip() if child is not None and child.text else ""

def _int_or_none(s: str) -> int | None:
    s = s.strip()
    if not s:
        return None
    try:
        return int(round(float(s.replace(",", "."))))
    except ValueError:
        return None

def parse_offers(path: str) -> dict[str, Offer]:
    """Основной фид -> {offer_id: Offer}. Потоковый парсинг (фид большой)."""
    offers: dict[str, Offer] = {}
    context = etree.iterparse(path, events=("end",), tag="offer")
    for _, el in context:
        oid = el.get("id")
        if oid:
            params = {p.get("name"): (p.text or "").strip()
                      for p in el.findall("param") if p.get("name")}
            offers[oid] = Offer(
                offer_id=oid,
                name=_text(el, "name"),
                price=_int_or_none(_text(el, "price")) or 0,
                old_price=_int_or_none(_text(el, "oldprice")),
                vendor=_text(el, "vendor"),
                category_id=_text(el, "categoryId"),
                url=_text(el, "url"),
                picture=_text(el, "picture"),
                description=_text(el, "description"),
                params=params,
            )
        el.clear()
    return offers

def merge_sklade(offers: dict[str, Offer], sklade_path: str) -> None:
    """Фид «на складе»: price = со скидкой, oldprice = РРЦ. Обновляем на месте."""
    context = etree.iterparse(sklade_path, events=("end",), tag="offer")
    for _, el in context:
        oid = el.get("id")
        if oid and oid in offers:
            price = _int_or_none(_text(el, "price"))
            old = _int_or_none(_text(el, "oldprice"))
            if price is not None:
                offers[oid].price = price
            if old is not None:
                offers[oid].old_price = old
        el.clear()
```

- [ ] **Step 4: Тест проходит**

Run: `pytest tests/test_feed_parser.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add src/kpgen/feed/ tests/test_feed_parser.py
git commit -m "feat: YML feed parser with sklade merge"
```

---

## Phase 3 — Каталог: SQLite FTS-индекс и поиск

### Task 6: Построение индекса и поиск

**Files:**
- Create: `src/kpgen/catalog/__init__.py`
- Create: `src/kpgen/catalog/index.py`
- Test: `tests/test_catalog_index.py`

- [ ] **Step 1: Падающий тест**

```python
# tests/test_catalog_index.py
import sqlite3
from kpgen.models import Offer
from kpgen.catalog.index import build_index, search

def _offers():
    return {
        "23954": Offer("23954", "Печь камин Guca Iskra", 50000, None, "Guca", "157",
                       "u", "p", "d", {}),
        "1001": Offer("1001", "Дымоход сэндвич нержавеющий", 8000, None, "Феникс", "200",
                      "u", "p", "d", {}),
    }

def test_search_by_name():
    con = sqlite3.connect(":memory:")
    build_index(con, _offers())
    res = search(con, "камин")
    assert [o.offer_id for o in res] == ["23954"]

def test_search_by_offer_id():
    con = sqlite3.connect(":memory:")
    build_index(con, _offers())
    res = search(con, "1001")
    assert res[0].offer_id == "1001"

def test_search_by_vendor():
    con = sqlite3.connect(":memory:")
    build_index(con, _offers())
    res = search(con, "Феникс")
    assert res[0].offer_id == "1001"
```

- [ ] **Step 2: Запустить — падает**

Run: `pytest tests/test_catalog_index.py -v`
Expected: FAIL (ModuleNotFoundError)

- [ ] **Step 3: Реализация**

```python
# src/kpgen/catalog/__init__.py
```
```python
# src/kpgen/catalog/index.py
import sqlite3
import json
from kpgen.models import Offer

def build_index(con: sqlite3.Connection, offers: dict[str, Offer]) -> None:
    con.execute("DROP TABLE IF EXISTS offers")
    con.execute("DROP TABLE IF EXISTS offers_fts")
    con.execute("""
        CREATE TABLE offers (
            offer_id TEXT PRIMARY KEY, name TEXT, price INTEGER, old_price INTEGER,
            vendor TEXT, category_id TEXT, url TEXT, picture TEXT,
            description TEXT, params TEXT
        )""")
    con.execute("""
        CREATE VIRTUAL TABLE offers_fts USING fts5(
            offer_id, name, vendor, content='offers', content_rowid='rowid')""")
    rows = [(o.offer_id, o.name, o.price, o.old_price, o.vendor, o.category_id,
             o.url, o.picture, o.description, json.dumps(o.params, ensure_ascii=False))
            for o in offers.values()]
    con.executemany("INSERT INTO offers VALUES (?,?,?,?,?,?,?,?,?,?)", rows)
    con.execute("""INSERT INTO offers_fts(rowid, offer_id, name, vendor)
                   SELECT rowid, offer_id, name, vendor FROM offers""")
    con.commit()

def _row_to_offer(r: sqlite3.Row) -> Offer:
    return Offer(r["offer_id"], r["name"], r["price"], r["old_price"], r["vendor"],
                 r["category_id"], r["url"], r["picture"], r["description"],
                 json.loads(r["params"]))

def search(con: sqlite3.Connection, query: str, limit: int = 20) -> list[Offer]:
    con.row_factory = sqlite3.Row
    q = query.strip()
    if not q:
        return []
    # точное совпадение по offer_id имеет приоритет
    exact = con.execute("SELECT * FROM offers WHERE offer_id = ?", (q,)).fetchone()
    results: list[Offer] = [_row_to_offer(exact)] if exact else []
    fts_q = " ".join(f'"{t}"*' for t in q.split())
    rows = con.execute("""
        SELECT o.* FROM offers_fts f JOIN offers o ON o.rowid = f.rowid
        WHERE offers_fts MATCH ? ORDER BY rank LIMIT ?""", (fts_q, limit)).fetchall()
    for r in rows:
        o = _row_to_offer(r)
        if not exact or o.offer_id != exact["offer_id"]:
            results.append(o)
    return results[:limit]
```

- [ ] **Step 4: Тест проходит**

Run: `pytest tests/test_catalog_index.py -v`
Expected: PASS (3 passed)

- [ ] **Step 5: Commit**

```bash
git add src/kpgen/catalog/ tests/test_catalog_index.py
git commit -m "feat: SQLite FTS catalog index and search"
```

### Task 7: CLI для построения индекса из реального фида

**Files:**
- Create: `src/kpgen/catalog/cli.py`
- Test: `tests/test_catalog_cli.py`

- [ ] **Step 1: Падающий тест** (на маленькой фикстуре)

```python
# tests/test_catalog_cli.py
import sqlite3
from pathlib import Path
from kpgen.catalog.cli import build_db

FX = Path(__file__).parent / "fixtures"

def test_build_db(tmp_path):
    db = tmp_path / "kp.sqlite"
    n = build_db(str(db), str(FX / "products_small.xml"), str(FX / "sklade_small.xml"))
    assert n == 1
    con = sqlite3.connect(str(db))
    price = con.execute("SELECT price FROM offers WHERE offer_id='23954'").fetchone()[0]
    assert price == 45000  # из sklade
```

- [ ] **Step 2: Запустить — падает**

Run: `pytest tests/test_catalog_cli.py -v`
Expected: FAIL (ModuleNotFoundError)

- [ ] **Step 3: Реализация**

```python
# src/kpgen/catalog/cli.py
import sqlite3
import sys
from kpgen.feed.parser import parse_offers, merge_sklade
from kpgen.catalog.index import build_index

def build_db(db_path: str, main_xml: str, sklade_xml: str | None) -> int:
    offers = parse_offers(main_xml)
    if sklade_xml:
        merge_sklade(offers, sklade_xml)
    con = sqlite3.connect(db_path)
    build_index(con, offers)
    con.close()
    return len(offers)

if __name__ == "__main__":
    # Использование: python -m kpgen.catalog.cli <db> <main.xml> [sklade.xml]
    db, main_xml = sys.argv[1], sys.argv[2]
    sklade = sys.argv[3] if len(sys.argv) > 3 else None
    print("offers:", build_db(db, main_xml, sklade))
```

- [ ] **Step 4: Тест проходит**

Run: `pytest tests/test_catalog_cli.py -v`
Expected: PASS (1 passed)

- [ ] **Step 5: Smoke на реальном фиде (вручную, не тест)**

Run:
```bash
python -m kpgen.catalog.cli data/kpgen.sqlite \
  /Users/alex/Documents/Sites/Parsing/Kamindom/data/pech_products.xml \
  /Users/alex/Documents/Sites/Parsing/Kamindom/data/pech_sklade.xml
```
Expected: `offers: <большое число>` (десятки тысяч), без ошибок.

- [ ] **Step 6: Commit**

```bash
git add src/kpgen/catalog/cli.py tests/test_catalog_cli.py
git commit -m "feat: build catalog DB from feed (CLI)"
```

---

## Phase 4 — Прайсинг (чистая логика)

### Task 8: Расчёт сумм и итога

**Files:**
- Create: `src/kpgen/pricing.py`
- Test: `tests/test_pricing.py`

- [ ] **Step 1: Падающий тест**

```python
# tests/test_pricing.py
from kpgen.models import Offer, LineItem, ServiceItem, Proposal, Client, Manager
from kpgen.pricing import compute_totals

def _proposal():
    o1 = Offer("1", "Печь", 309900, 325699, "", "", "", "", "", {})
    o2 = Offer("2", "Дымоход", 28400, None, "", "", "", "", "", {})
    return Proposal(
        id="x", client=Client("Дао", "20 августа 2025 года"),
        manager=Manager("Сергей"),
        items=[LineItem(o1, 1), LineItem(o2, 1)],
        services=[ServiceItem("Доставка", 2500), ServiceItem("Монтаж", 18000)],
        discount=18200,
    )

def test_totals():
    t = compute_totals(_proposal())
    assert t.items_sum == 338300       # 309900 + 28400
    assert t.services_sum == 20500     # 2500 + 18000
    assert t.discount == 18200
    assert t.grand_total == 340600     # 338300 + 20500 - 18200

def test_grand_total_never_negative():
    p = _proposal()
    p.discount = 10_000_000
    t = compute_totals(p)
    assert t.grand_total == 0
```

- [ ] **Step 2: Запустить — падает**

Run: `pytest tests/test_pricing.py -v`
Expected: FAIL (ModuleNotFoundError)

- [ ] **Step 3: Реализация**

```python
# src/kpgen/pricing.py
from dataclasses import dataclass
from kpgen.models import Proposal

@dataclass
class Totals:
    items_sum: int
    services_sum: int
    discount: int
    grand_total: int

def compute_totals(p: Proposal) -> Totals:
    items_sum = sum(li.line_sum for li in p.items)
    services_sum = sum(s.amount for s in p.services)
    grand = items_sum + services_sum - p.discount
    return Totals(items_sum, services_sum, p.discount, max(0, grand))
```

- [ ] **Step 4: Тест проходит**

Run: `pytest tests/test_pricing.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add src/kpgen/pricing.py tests/test_pricing.py
git commit -m "feat: pricing totals"
```

---

## Phase 5 — Хранение КП

### Task 9: SQLite-стор для Proposal

**Files:**
- Create: `src/kpgen/store.py`
- Test: `tests/test_store.py`

- [ ] **Step 1: Падающий тест**

```python
# tests/test_store.py
import sqlite3
from kpgen.models import Offer, LineItem, ServiceItem, Proposal, Client, Manager
from kpgen.store import ProposalStore

def _proposal(pid="abc"):
    o1 = Offer("1", "Печь", 309900, 325699, "ТМФ", "157", "u", "p", "опис", {"Мощность": "9 кВт"})
    return Proposal(id=pid, client=Client("Дао", "20 августа 2025 года"),
                    manager=Manager("Сергей", email="s@pech.ru", phone="+7 999"),
                    items=[LineItem(o1, 2)], services=[ServiceItem("Монтаж", 18000)], discount=5000)

def test_save_and_load_roundtrip(tmp_path):
    store = ProposalStore(str(tmp_path / "kp.sqlite"))
    store.save(_proposal("abc"))
    loaded = store.load("abc")
    assert loaded.client.name == "Дао"
    assert loaded.items[0].offer.name == "Печь"
    assert loaded.items[0].qty == 2
    assert loaded.services[0].amount == 18000
    assert loaded.discount == 5000
    assert loaded.items[0].offer.params["Мощность"] == "9 кВт"

def test_load_missing_returns_none(tmp_path):
    store = ProposalStore(str(tmp_path / "kp.sqlite"))
    assert store.load("nope") is None
```

- [ ] **Step 2: Запустить — падает**

Run: `pytest tests/test_store.py -v`
Expected: FAIL (ModuleNotFoundError)

- [ ] **Step 3: Реализация** (КП сериализуем как JSON-блоб — структура вложенная, отдельные таблицы избыточны)

```python
# src/kpgen/store.py
import sqlite3
import json
from dataclasses import asdict
from kpgen.models import Offer, LineItem, ServiceItem, Proposal, Client, Manager

class ProposalStore:
    def __init__(self, db_path: str):
        self.db_path = db_path
        con = sqlite3.connect(db_path)
        con.execute("CREATE TABLE IF NOT EXISTS proposals (id TEXT PRIMARY KEY, data TEXT)")
        con.commit()
        con.close()

    def save(self, p: Proposal) -> None:
        data = json.dumps(asdict(p), ensure_ascii=False)
        con = sqlite3.connect(self.db_path)
        con.execute("INSERT OR REPLACE INTO proposals VALUES (?, ?)", (p.id, data))
        con.commit()
        con.close()

    def load(self, pid: str) -> Proposal | None:
        con = sqlite3.connect(self.db_path)
        row = con.execute("SELECT data FROM proposals WHERE id = ?", (pid,)).fetchone()
        con.close()
        if row is None:
            return None
        d = json.loads(row[0])
        return Proposal(
            id=d["id"],
            client=Client(**d["client"]),
            manager=Manager(**d["manager"]),
            items=[LineItem(offer=Offer(**li["offer"]), qty=li["qty"]) for li in d["items"]],
            services=[ServiceItem(**s) for s in d["services"]],
            discount=d["discount"],
        )
```

- [ ] **Step 4: Тест проходит**

Run: `pytest tests/test_store.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add src/kpgen/store.py tests/test_store.py
git commit -m "feat: proposal SQLite store"
```

---

## Phase 6 — Рендер HTML

### Task 10: Перенос статики и шаблонов из prototype

**Files:**
- Create: `src/kpgen/render/__init__.py`
- Create: `src/kpgen/render/static/` (копии из дизайн-системы)
- Create: `src/kpgen/render/templates/kp.html.j2`

- [ ] **Step 1: Скопировать CSS прототипа в статику**

Run:
```bash
mkdir -p src/kpgen/render/static src/kpgen/render/templates
cp prototype/colors_and_type.css src/kpgen/render/static/
cp prototype/preview/kp-slides.css prototype/preview/kp-mobile.css src/kpgen/render/static/
```

- [ ] **Step 2: Скопировать шрифты и sprite из дизайн-системы**

Через DesignSync прочитать `fonts/*.otf` и `assets/sprite.svg` из проекта `cffe7775-571d-4414-8a6a-6fa40431bdac` и положить в `src/kpgen/render/static/fonts/` и `src/kpgen/render/static/`. (Если DesignSync недоступен — взять из локального экспорта дизайн-системы.) В `colors_and_type.css` пути к шрифтам должны указывать на `fonts/`.

- [ ] **Step 3: Создать Jinja2-шаблон `kp.html.j2`**

Перенести разметку из `prototype/preview/kp-slide-*.html`, обернув в один документ: цикл по слайдам. Каркас:

```jinja
<!DOCTYPE html>
<html lang="ru"><head><meta charset="utf-8">
<link rel="stylesheet" href="{{ static }}/colors_and_type.css">
<link rel="stylesheet" href="{{ static }}/kp-slides.css">
</head><body>
<svg style="display:none"><symbol id="flame" viewBox="0 0 32 40"><path d="M16 1c2 8 12 11 12 22 0 8-6 16-12 16S4 33 4 24c0-7 5-10 7-15 1 4 3 6 4 6 0-6-1-9 1-14z"/></symbol></svg>

{# Слайд 1 — Обложка #}
<div class="slide">
  <div class="content">
    <h1 class="kp-h1">Печь.ру&nbsp;— искусство тепла и&nbsp;уюта в&nbsp;каждом&nbsp;доме!</h1>
    <p class="kp-lead">Коммерческое предложение для&nbsp;{{ p.client.name }}.<br>Подготовлено {{ p.client.date }}.</p>
    {# ... преимущества ... #}
  </div>
  {% include "_sidebar.html.j2" %}
</div>

{# Слайды-карточки товаров #}
{% for li in p.items %}
<div class="slide">
  <div class="content">
    <div class="prod">
      <div class="prod__photo" style="background-image:url('{{ li.offer.picture }}')"></div>
      <div>
        <h2 class="prod__name">{{ li.offer.name }}</h2>
        <div class="spec-h">Характеристики</div>
        <div class="spec">
          {% for k, v in li.offer.params.items() %}
          <div class="r"><span class="k">{{ k }}</span><span class="v">{{ v }}</span></div>
          {% endfor %}
        </div>
        <div class="price-wrap">
          <div class="price">{{ li.offer.price | rub }}&nbsp;<small>₽</small></div>
          {% if li.offer.has_discount %}<div class="price-old">{{ li.offer.old_price | rub }}&nbsp;₽</div>{% endif %}
        </div>
      </div>
    </div>
  </div>
  {% include "_sidebar.html.j2" %}
</div>
{% endfor %}

{# Слайд Итоги #}
<div class="slide">
  <div class="content">
    <h1 class="kp-h1">Итоги предложения</h1>
    <table class="totals"><thead><tr><th colspan="2">Наименование</th><th class="num">Кол-во</th><th class="num">Цена</th><th class="num">Сумма</th></tr></thead>
    <tbody>
      {% for li in p.items %}
      <tr><td><div class="thumb"></div></td><td class="nm">{{ li.offer.name }}</td><td class="num">{{ li.qty }}</td><td class="num">{{ li.offer.price | rub }}&nbsp;₽</td><td class="num sum">{{ li.line_sum | rub }}&nbsp;₽</td></tr>
      {% endfor %}
      {% for s in p.services %}
      <tr class="svc"><td></td><td class="nm">{{ s.title }}</td><td class="num">—</td><td class="num"></td><td class="num sum">{{ s.amount | rub }}&nbsp;₽</td></tr>
      {% endfor %}
      {% if p.discount %}<tr class="discount"><td></td><td class="nm">Скидка на&nbsp;предложение</td><td class="num">—</td><td class="num"></td><td class="num sum">−{{ p.discount | rub }}&nbsp;₽</td></tr>{% endif %}
    </tbody></table>
    <div class="grand"><div class="grand__l">Итого к&nbsp;оплате</div><div class="grand__v">{{ totals.grand_total | rub }}&nbsp;₽</div></div>
  </div>
  {% include "_sidebar.html.j2" %}
</div>

{# Слайд контактов #}
{% include "_contacts.html.j2" %}
</body></html>
```

Также создать `src/kpgen/render/templates/_sidebar.html.j2` и `_contacts.html.j2` (разметка сайдбара и контактов из соответствующих `prototype/preview/*.html`).

- [ ] **Step 4: Commit**

```bash
git add src/kpgen/render/
git commit -m "feat: render static assets and Jinja KP template"
```

### Task 11: Функция рендера HTML

**Files:**
- Create: `src/kpgen/render/html.py`
- Test: `tests/test_render_html.py`

- [ ] **Step 1: Падающий тест**

```python
# tests/test_render_html.py
from kpgen.models import Offer, LineItem, ServiceItem, Proposal, Client, Manager
from kpgen.render.html import render_html

def _proposal():
    o1 = Offer("1", "Печь ТМФ Студент", 309900, 325699, "ТМФ", "157", "u",
               "https://www.pech.ru/p.jpg", "опис", {"Мощность": "9 кВт"})
    return Proposal(id="abc", client=Client("Дао", "20 августа 2025 года"),
                    manager=Manager("Сергей", email="s@pech.ru", phone="+7 999"),
                    items=[LineItem(o1, 1)], services=[ServiceItem("Монтаж", 18000)], discount=5000)

def test_render_contains_key_fields():
    html = render_html(_proposal(), static_base="/static")
    assert "Печь ТМФ Студент" in html
    assert "Дао" in html
    assert "9 кВт" in html
    assert "Итого к" in html
    assert "322&nbsp;900" in html or "322 900" in html  # 309900+18000-5000

def test_rub_filter_formatting():
    html = render_html(_proposal(), static_base="/static")
    assert "309&nbsp;900" in html  # цена с неразрывными пробелами по разрядам
```

- [ ] **Step 2: Запустить — падает**

Run: `pytest tests/test_render_html.py -v`
Expected: FAIL (ModuleNotFoundError)

- [ ] **Step 3: Реализация**

```python
# src/kpgen/render/html.py
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape
from kpgen.models import Proposal
from kpgen.pricing import compute_totals

_TPL_DIR = Path(__file__).parent / "templates"

def _rub(value: int) -> str:
    """123900 -> '123&nbsp;900' (разряды неразрывным пробелом)."""
    s = f"{int(value):,}".replace(",", " ")
    return s

def _env() -> Environment:
    env = Environment(loader=FileSystemLoader(str(_TPL_DIR)),
                      autoescape=select_autoescape(["html", "j2"]))
    env.filters["rub"] = _rub
    return env

def render_html(p: Proposal, static_base: str = "/static") -> str:
    env = _env()
    tpl = env.get_template("kp.html.j2")
    return tpl.render(p=p, totals=compute_totals(p), static=static_base)
```

> Примечание: в шаблоне `rub` возвращает `&nbsp;`, поэтому для соответствующих ячеек использовать `| rub | safe`, либо помечать фильтр через `Markup`. Если autoescape экранирует `&nbsp;`, обернуть результат `_rub` в `markupsafe.Markup`.

- [ ] **Step 4: Тест проходит**

Run: `pytest tests/test_render_html.py -v`
Expected: PASS (2 passed). Если падает на экранировании `&nbsp;` — обернуть `_rub` в `markupsafe.Markup(s)` и повторить.

- [ ] **Step 5: Commit**

```bash
git add src/kpgen/render/html.py tests/test_render_html.py
git commit -m "feat: render proposal to HTML"
```

---

## Phase 7 — PDF через Playwright

### Task 12: HTML -> PDF

**Files:**
- Create: `src/kpgen/render/pdf.py`
- Test: `tests/test_render_pdf.py`

- [ ] **Step 1: Падающий тест** (проверяем, что получается валидный PDF; landscape)

```python
# tests/test_render_pdf.py
from kpgen.render.pdf import html_to_pdf

def test_html_to_pdf_produces_pdf(tmp_path):
    html = "<html><body><div style='width:1280px;height:720px;background:#ff6955'>КП</div></body></html>"
    out = tmp_path / "kp.pdf"
    html_to_pdf(html, str(out), base_url=None)
    data = out.read_bytes()
    assert data[:4] == b"%PDF"
    assert len(data) > 1000
```

- [ ] **Step 2: Запустить — падает**

Run: `pytest tests/test_render_pdf.py -v`
Expected: FAIL (ModuleNotFoundError)

- [ ] **Step 3: Реализация**

```python
# src/kpgen/render/pdf.py
from playwright.sync_api import sync_playwright

def html_to_pdf(html: str, out_path: str, base_url: str | None = None) -> None:
    """Рендер HTML в PDF. Слайды 16:9 landscape; печать фоновых цветов включена."""
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page()
        page.set_content(html, wait_until="networkidle")
        if base_url:
            # для подгрузки относительной статики через сервер используем goto(base_url)
            page.goto(base_url, wait_until="networkidle")
        page.pdf(path=out_path, landscape=True, print_background=True,
                 width="1280px", height="720px", margin={"top": "0", "bottom": "0", "left": "0", "right": "0"})
        browser.close()
```

- [ ] **Step 4: Тест проходит**

Run: `pytest tests/test_render_pdf.py -v`
Expected: PASS (1 passed). Требует установленного Chromium (Task 1, Step 3).

- [ ] **Step 5: Commit**

```bash
git add src/kpgen/render/pdf.py tests/test_render_pdf.py
git commit -m "feat: HTML to PDF via Playwright"
```

---

## Phase 8 — Веб-приложение (FastAPI)

### Task 13: Поисковый API и приложение

**Files:**
- Create: `src/kpgen/web/__init__.py`
- Create: `src/kpgen/web/app.py`
- Test: `tests/test_web.py`

- [ ] **Step 1: Падающий тест**

```python
# tests/test_web.py
import sqlite3
from pathlib import Path
from fastapi.testclient import TestClient
from kpgen.catalog.cli import build_db
from kpgen.web.app import create_app

FX = Path(__file__).parent / "fixtures"

def _app(tmp_path):
    catalog_db = tmp_path / "catalog.sqlite"
    build_db(str(catalog_db), str(FX / "products_small.xml"), str(FX / "sklade_small.xml"))
    proposals_db = tmp_path / "proposals.sqlite"
    return create_app(catalog_db=str(catalog_db), proposals_db=str(proposals_db))

def test_search_endpoint(tmp_path):
    client = TestClient(_app(tmp_path))
    r = client.get("/api/search", params={"q": "камин"})
    assert r.status_code == 200
    assert r.json()[0]["offer_id"] == "23954"

def test_create_and_get_proposal(tmp_path):
    client = TestClient(_app(tmp_path))
    payload = {
        "client": {"name": "Дао", "date": "20 августа 2025 года"},
        "manager": {"name": "Сергей", "email": "s@pech.ru", "phone": "+7 999"},
        "items": [{"offer_id": "23954", "qty": 1}],
        "services": [{"title": "Монтаж", "amount": 18000}],
        "discount": 5000,
    }
    r = client.post("/api/proposals", json=payload)
    assert r.status_code == 200
    pid = r.json()["id"]
    page = client.get(f"/kp/{pid}")
    assert page.status_code == 200
    assert "Печь камин Guca Iskra" in page.text
    assert "Дао" in page.text
```

- [ ] **Step 2: Запустить — падает**

Run: `pytest tests/test_web.py -v`
Expected: FAIL (ModuleNotFoundError)

- [ ] **Step 3: Реализация**

```python
# src/kpgen/web/__init__.py
```
```python
# src/kpgen/web/app.py
import sqlite3
import uuid
from pathlib import Path
from dataclasses import asdict
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from kpgen.catalog.index import search
from kpgen.models import Offer, LineItem, ServiceItem, Proposal, Client, Manager
from kpgen.store import ProposalStore
from kpgen.render.html import render_html
from kpgen.render.pdf import html_to_pdf

_STATIC = Path(__file__).parent.parent / "render" / "static"

def create_app(catalog_db: str, proposals_db: str) -> FastAPI:
    app = FastAPI()
    app.mount("/static", StaticFiles(directory=str(_STATIC)), name="static")
    store = ProposalStore(proposals_db)

    def _catalog() -> sqlite3.Connection:
        return sqlite3.connect(catalog_db)

    def _offer_by_id(con, oid: str) -> Offer | None:
        res = search(con, oid)
        return next((o for o in res if o.offer_id == oid), None)

    @app.get("/api/search")
    def api_search(q: str):
        con = _catalog()
        try:
            return [asdict(o) for o in search(con, q)]
        finally:
            con.close()

    @app.post("/api/proposals")
    def create_proposal(payload: dict):
        con = _catalog()
        try:
            items = []
            for it in payload.get("items", []):
                offer = _offer_by_id(con, it["offer_id"])
                if offer is None:
                    raise HTTPException(404, f"offer {it['offer_id']} not found")
                items.append(LineItem(offer=offer, qty=int(it.get("qty", 1))))
        finally:
            con.close()
        p = Proposal(
            id=uuid.uuid4().hex[:10],
            client=Client(**payload["client"]),
            manager=Manager(**payload["manager"]),
            items=items,
            services=[ServiceItem(**s) for s in payload.get("services", [])],
            discount=int(payload.get("discount", 0)),
        )
        store.save(p)
        return {"id": p.id}

    @app.get("/kp/{pid}", response_class=HTMLResponse)
    def view_proposal(pid: str):
        p = store.load(pid)
        if p is None:
            raise HTTPException(404, "proposal not found")
        return render_html(p, static_base="/static")

    @app.get("/kp/{pid}.pdf")
    def proposal_pdf(pid: str):
        p = store.load(pid)
        if p is None:
            raise HTTPException(404, "proposal not found")
        html = render_html(p, static_base=str(_STATIC.as_uri()))
        out = Path(proposals_db).parent / f"kp-{pid}.pdf"
        html_to_pdf(html, str(out), base_url=None)
        return FileResponse(str(out), media_type="application/pdf", filename=f"kp-{pid}.pdf")

    return app
```

- [ ] **Step 4: Тест проходит**

Run: `pytest tests/test_web.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add src/kpgen/web/ tests/test_web.py
git commit -m "feat: FastAPI app — search, create, view, PDF"
```

### Task 14: Точка входа и форма менеджера

**Files:**
- Create: `src/kpgen/web/main.py`
- Create: `src/kpgen/render/templates/form.html.j2`
- Test: ручной smoke

- [ ] **Step 1: Точка входа**

```python
# src/kpgen/web/main.py
import os
from kpgen.web.app import create_app

app = create_app(
    catalog_db=os.getenv("KPGEN_CATALOG_DB", "data/kpgen.sqlite"),
    proposals_db=os.getenv("KPGEN_PROPOSALS_DB", "data/proposals.sqlite"),
)
```

- [ ] **Step 2: Создать форму** `form.html.j2` на `/` — поиск товаров (`/api/search`), добавление позиций, поля клиента/менеджера/услуг/скидки, кнопка отправки на `/api/proposals`, затем редирект на `/kp/<id>`. Стилизовать токенами дизайн-системы. Подключить маршрут `GET /` в `app.py`, отдающий эту форму.

- [ ] **Step 3: Smoke-запуск**

Run:
```bash
uvicorn kpgen.web.main:app --reload --port 8000
```
Expected: открыть http://localhost:8000 — форма; собрать КП из 1–2 товаров; получить `/kp/<id>` и скачать `/kp/<id>.pdf`.

- [ ] **Step 4: Commit**

```bash
git add src/kpgen/web/main.py src/kpgen/render/templates/form.html.j2
git commit -m "feat: manager form and app entrypoint"
```

---

## Phase 9 — Добор данных с сайта (опционально, после MVP)

### Task 15: Скрапер доп. фото и описания + кэш

**Files:**
- Create: `src/kpgen/scraper/__init__.py`
- Create: `src/kpgen/scraper/site.py`
- Test: `tests/test_scraper.py`

- [ ] **Step 1: Падающий тест** (на сохранённом HTML-фрагменте страницы товара в `tests/fixtures/product_page.html`)

```python
# tests/test_scraper.py
from pathlib import Path
from kpgen.scraper.site import extract_gallery_and_description

FX = Path(__file__).parent / "fixtures"

def test_extract():
    html = (FX / "product_page.html").read_text(encoding="utf-8")
    data = extract_gallery_and_description(html)
    assert len(data["images"]) >= 1
    assert "камин" in data["description"].lower()
```

- [ ] **Step 2: Создать фикстуру** `tests/fixtures/product_page.html` — сохранить реальную страницу товара pech.ru (минимальный срез с галереей и описанием).

- [ ] **Step 3: Запустить — падает**

Run: `pytest tests/test_scraper.py -v`
Expected: FAIL (ModuleNotFoundError)

- [ ] **Step 4: Реализация** — `extract_gallery_and_description(html) -> {"images": [...], "description": "..."}` через `lxml.html` (CSS/XPath по разметке pech.ru), плюс `fetch_and_cache(offer_id, url, con)` с таблицей кэша `product_extra(offer_id PRIMARY KEY, images TEXT, description TEXT)`. HTTP через `httpx`.

```python
# src/kpgen/scraper/site.py
import json
import sqlite3
import httpx
from lxml import html as lxml_html

def extract_gallery_and_description(page_html: str) -> dict:
    doc = lxml_html.fromstring(page_html)
    images = [img.get("src") for img in doc.cssselect(".product-gallery img") if img.get("src")]
    desc_nodes = doc.cssselect(".product-description")
    description = desc_nodes[0].text_content().strip() if desc_nodes else ""
    return {"images": images, "description": description}

def fetch_and_cache(offer_id: str, url: str, con: sqlite3.Connection) -> dict:
    con.execute("CREATE TABLE IF NOT EXISTS product_extra (offer_id TEXT PRIMARY KEY, images TEXT, description TEXT)")
    row = con.execute("SELECT images, description FROM product_extra WHERE offer_id=?", (offer_id,)).fetchone()
    if row:
        return {"images": json.loads(row[0]), "description": row[1]}
    resp = httpx.get(url, timeout=20, follow_redirects=True)
    data = extract_gallery_and_description(resp.text)
    con.execute("INSERT OR REPLACE INTO product_extra VALUES (?,?,?)",
                (offer_id, json.dumps(data["images"], ensure_ascii=False), data["description"]))
    con.commit()
    return data
```

> Селекторы `.product-gallery img` / `.product-description` — заглушки; уточнить по реальной разметке pech.ru при создании фикстуры в Step 2 и поправить тест/код вместе.

- [ ] **Step 5: Тест проходит**

Run: `pytest tests/test_scraper.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/kpgen/scraper/ tests/test_scraper.py tests/fixtures/product_page.html
git commit -m "feat: site scraper for extra photos and description"
```

---

## Что НЕ входит в этот план (YAGNI / позже)

- Авторизация и мультипользовательский режим (добавится при переезде на сервер).
- Остальные мобильные слайды как отдельные файлы — мобайл реализуется адаптивным CSS в одном шаблоне.
- Полный перенос всех 11 типов слайдов в шаблон сразу — в Task 10 переносится критический путь (обложка, карточки, итоги, контакты); остальные типы (о компании, галереи, описание, шаги, адреса) добавляются по тому же образцу отдельными include-шаблонами после прохождения MVP. Каждый — копия соответствующего `prototype/preview/*.html` с подстановкой данных.
- Периодическое обновление фида по расписанию (cron) — пока запуск CLI вручную.

## Зависимости фаз

Фазы 2→3→4→5 независимы между собой после Phase 1, но 6 (рендер) зависит от моделей (2) и прайсинга (4); 7 (PDF) от 6; 8 (веб) от 3,5,6,7. Phase 9 — после MVP.
