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
    assert t.items_sum == 338300
    assert t.services_sum == 20500
    assert t.discount == 18200
    assert t.grand_total == 340600

def test_grand_total_never_negative():
    p = _proposal()
    p.discount = 10_000_000
    t = compute_totals(p)
    assert t.grand_total == 0
