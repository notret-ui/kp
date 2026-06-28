import dataclasses
import sqlite3
from kpgen.models import Offer, LineItem, ServiceItem, Proposal, Client, Manager
from kpgen.store import ProposalStore

def _proposal(pid="abc"):
    o1 = Offer("1", "Печь", 309900, 325699, "ТМФ", "157", "u", "p", "опис", {"Мощность": "9 кВт"})
    return Proposal(id=pid, client=Client("Дао", "20 августа 2025 года"),
                    manager=Manager("Сергей", email="s@pech.ru", phone="+7 999"),
                    items=[LineItem(o1, 2)], services=[ServiceItem("Монтаж", 18000)], discount=5000)

def test_next_number_increments_per_day(tmp_path):
    store = ProposalStore(str(tmp_path / "kp.sqlite"))
    n1 = store.next_number(today="20260628")
    assert n1 == "КП-20260628-001"
    p = _proposal("a1"); p.number = n1; store.save(p)
    assert store.next_number(today="20260628") == "КП-20260628-002"
    assert store.next_number(today="20260629") == "КП-20260629-001"  # новый день — с 001

def test_number_roundtrip(tmp_path):
    store = ProposalStore(str(tmp_path / "kp.sqlite"))
    p = _proposal("n1"); p.number = "КП-20260628-007"; store.save(p)
    assert store.load("n1").number == "КП-20260628-007"

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

def test_extra_fields_roundtrip(tmp_path):
    o = Offer("2", "Камин", 150000, None, "Вендор", "42", "https://www.pech.ru/k",
              "https://www.pech.ru/k.jpg", "описание", {},
              extra_images=["x.jpg", "y.jpg"], long_description="длинное")
    p = Proposal(id="xyz", client=Client("Иван", "1 января 2026 года"),
                 manager=Manager("Алексей"),
                 items=[LineItem(o, 1)], services=[], discount=0)
    store = ProposalStore(str(tmp_path / "kp.sqlite"))
    store.save(p)
    loaded = store.load("xyz")
    assert loaded.items[0].offer.extra_images == ["x.jpg", "y.jpg"]
    assert loaded.items[0].offer.long_description == "длинное"


def test_related_roundtrip(tmp_path):
    o_related = Offer("999", "Сопутствующая печь", 89900, None, "Вендор", "157",
                      "https://www.pech.ru/r", "pic.jpg", "описание", {})
    p = _proposal("rel1")
    p.related = [o_related]
    store = ProposalStore(str(tmp_path / "kp.sqlite"))
    store.save(p)
    loaded = store.load("rel1")
    assert len(loaded.related) == 1
    assert loaded.related[0].name == "Сопутствующая печь"


def test_list_summaries(tmp_path):
    store = ProposalStore(str(tmp_path / "t.db"))
    p1 = _proposal()
    p1 = dataclasses.replace(p1, id="p1")
    p2 = _proposal()
    p2 = dataclasses.replace(p2, id="p2")
    store.save(p1)
    store.save(p2)
    summaries = store.list_summaries()
    assert len(summaries) == 2
    # newest first (p2 was inserted last)
    assert summaries[0]["id"] == "p2"
    assert summaries[1]["id"] == "p1"
    assert summaries[0]["client_name"] == p2.client.name
    assert isinstance(summaries[0]["grand_total"], int)
