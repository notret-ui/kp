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
