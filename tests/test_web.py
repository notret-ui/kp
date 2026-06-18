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

def test_proposal_pdf_download(tmp_path):
    client = TestClient(_app(tmp_path))
    payload = {
        "client": {"name": "Дао", "date": "20 августа 2025 года"},
        "manager": {"name": "Сергей", "email": "s@pech.ru", "phone": "+7 999"},
        "items": [{"offer_id": "23954", "qty": 1}],
        "services": [], "discount": 0,
    }
    pid = client.post("/api/proposals", json=payload).json()["id"]
    r = client.get(f"/kp/{pid}.pdf")
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/pdf"
    assert r.content[:4] == b"%PDF"

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


def test_malformed_payload_returns_422(tmp_path):
    client = TestClient(_app(tmp_path))
    # missing required client.name
    r = client.post("/api/proposals", json={"manager": {"name": "X"}, "items": []})
    assert r.status_code == 422


def test_service_amount_must_be_int(tmp_path):
    client = TestClient(_app(tmp_path))
    payload = {"client": {"name": "Дао", "date": "d"}, "manager": {"name": "S"},
               "items": [], "services": [{"title": "Монтаж", "amount": 18000}], "discount": 0}
    r = client.post("/api/proposals", json=payload)
    assert r.status_code == 200


def test_pdf_not_persisted_in_data_dir(tmp_path):
    client = TestClient(_app(tmp_path))
    payload = {"client": {"name": "Дао", "date": "d"}, "manager": {"name": "S"},
               "items": [{"offer_id": "23954", "qty": 1}], "services": [], "discount": 0}
    pid = client.post("/api/proposals", json=payload).json()["id"]
    r = client.get(f"/kp/{pid}.pdf")
    assert r.status_code == 200 and r.content[:4] == b"%PDF"
    leftover = list(tmp_path.glob("kp-*.pdf"))
    assert leftover == []
