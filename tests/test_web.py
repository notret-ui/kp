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

def test_form_page(tmp_path):
    client = TestClient(_app(tmp_path))
    r = client.get("/")
    assert r.status_code == 200
    assert "коммерческого предложения" in r.text

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
