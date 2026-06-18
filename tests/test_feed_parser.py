from pathlib import Path
from kpgen.feed.parser import parse_offers, merge_sklade, _int_or_none

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


# I1 — streaming parse memory cleanup regression guard
def test_parse_main_feed_after_cleanup_still_correct():
    """el.clear() + sibling removal must not break parsing correctness."""
    offers = parse_offers(str(FX / "products_small.xml"))
    assert len(offers) == 1
    o = offers["23954"]
    assert o.offer_id == "23954"
    assert o.name == "Печь камин Guca Iskra"
    assert o.price == 50000


# I2 — price with thousands-separator space / NBSP parses correctly
def test_int_or_none_space_separator():
    assert _int_or_none("50 000") == 50000

def test_int_or_none_nbsp_separator():
    assert _int_or_none("45\xa0000") == 45000

def test_int_or_none_negative_is_none():
    assert _int_or_none("-100") is None

def test_int_or_none_empty_is_none():
    assert _int_or_none("") is None


# I3 — description with inline markup returns full text
def test_parse_description_with_inline_markup(tmp_path):
    xml = (
        '<?xml version="1.0" encoding="utf-8"?>'
        "<yml_catalog><shop><offers>"
        '<offer id="1">'
        "  <name>Test</name>"
        "  <price>1000</price>"
        "  <vendor>X</vendor>"
        "  <categoryId>1</categoryId>"
        "  <url>u</url>"
        "  <picture>p</picture>"
        "  <description>Привет <b>мир</b> хвост</description>"
        "</offer>"
        "</offers></shop></yml_catalog>"
    )
    feed = tmp_path / "feed.xml"
    feed.write_text(xml, encoding="utf-8")
    offers = parse_offers(str(feed))
    desc = offers["1"].description
    assert "Привет" in desc
    assert "хвост" in desc
