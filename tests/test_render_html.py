from kpgen.models import Offer, LineItem, ServiceItem, Proposal, Client, Manager
from kpgen.render.html import render_html

def _proposal():
    o1 = Offer("1", "Печь ТМФ Студент", 309900, 325699, "ТМФ", "157", "u",
               "https://www.pech.ru/p.jpg", "опис", {"Мощность": "9 кВт"})
    return Proposal(id="abc", client=Client("Дао", "20 августа 2025 года"),
                    manager=Manager("Сергей", email="s@pech.ru", phone="+7 999"),
                    items=[LineItem(o1, 1)], services=[ServiceItem("Монтаж", 18000)], discount=5000)

def test_render_contains_key_fields():
    html = render_html(_proposal(), static_base="/static")
    assert "Печь ТМФ Студент" in html
    assert "Дао" in html
    assert "9 кВт" in html
    assert "Итого к" in html

def test_render_grand_total_present():
    # 309900 + 18000 - 5000 = 322900
    html = render_html(_proposal(), static_base="/static")
    assert ("322&nbsp;900" in html) or ("322 900" in html)

def test_rub_filter_formatting():
    html = render_html(_proposal(), static_base="/static")
    assert "309&nbsp;900" in html  # price with nbsp thousands separators, not escaped
