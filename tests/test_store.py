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
