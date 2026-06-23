import sqlite3
from kpgen.models import Offer
from kpgen.catalog.index import build_index, search, related_offers

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


def test_related_offers_same_category_excludes_items():
    con = sqlite3.connect(":memory:")
    build_index(con, {
        "100": Offer("100","Печь А",50000,None,"V","157","u","p","d",{}),
        "101": Offer("101","Печь Б",70000,None,"V","157","u","p","d",{}),
        "200": Offer("200","Дымоход",8000,None,"V","200","u","p","d",{}),
    })
    res = related_offers(con, ["157"], ["100"], limit=3)
    ids = [o.offer_id for o in res]
    assert "101" in ids        # same category, not excluded
    assert "100" not in ids     # excluded (already in proposal)
    assert "200" not in ids     # different category

def test_cross_sell_offers_picks_from_groups():
    from kpgen.catalog.index import cross_sell_offers
    con = sqlite3.connect(":memory:")
    build_index(con, {
        "g1": Offer("g1", "Гриль угольный", 30000, None, "V", "160", "u", "pic", "d", {}),
        "k1": Offer("k1", "Уличная кухня", 90000, None, "V", "2153", "u", "pic", "d", {}),
        "f1": Offer("f1", "Садовый диван", 40000, None, "V", "2155", "u", "pic", "d", {}),
        "x1": Offer("x1", "Печь", 50000, None, "V", "157", "u", "pic", "d", {}),
    })
    res = cross_sell_offers(con, exclude_ids=[])
    cats = [o.category_id for o in res]
    assert "160" in cats and "2153" in cats and "2155" in cats   # по одному из каждой группы
    assert "157" not in cats                                      # печь (не смежная) не попадает
