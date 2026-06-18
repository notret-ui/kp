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


# C1 — FTS search must not crash when query contains a double-quote
def test_search_quote_in_query_does_not_raise():
    con = sqlite3.connect(":memory:")
    build_index(con, _offers())
    # both forms must return a list (possibly empty), never raise
    result1 = search(con, 'камин"')
    assert isinstance(result1, list)
    result2 = search(con, '"')
    assert isinstance(result2, list)
