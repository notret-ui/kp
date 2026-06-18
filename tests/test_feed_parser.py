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
    assert o.price == 45000
    assert o.old_price == 50000
    assert o.has_discount is True
