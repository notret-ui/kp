from kpgen.models import Offer, LineItem, ServiceItem, Proposal, Client, Manager
from kpgen.render.html import render_html

def _proposal():
    o1 = Offer("1", "Печь ТМФ Студент", 309900, 325699, "ТМФ", "157", "u",
               "https://www.pech.ru/p.jpg", "опис", {"Мощность": "9 кВт"})
    return Proposal(id="abc", client=Client("Дао", "20 августа 2025 года"),
                    manager=Manager("Сергей", email="s@pech.ru", phone="+7 999"),
                    items=[LineItem(o1, 1)], services=[ServiceItem("Монтаж", 18000)], discount=5000)

def test_render_has_pdf_download_button():
    html = render_html(_proposal(), static_base="/static")
    assert 'class="pdf-fab"' in html
    assert "/kp/abc.pdf" in html            # ссылка на PDF этого КП
    assert "@media print" in html            # кнопка скрыта в самом PDF

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

def test_render_includes_brand_slides():
    from kpgen.render.html import render_html
    html = render_html(_proposal(), static_base="/static")
    assert "2009" in html                      # about
    assert "Как заказать" in html               # steps
    assert "Адреса" in html                     # addresses
    assert "живой огонь" in html or "Живой огонь" in html  # hero

def test_render_gallery_and_description_slides():
    o = Offer(
        "3", "Камин тест", 200000, None, "Вендор", "99",
        "https://www.pech.ru/kamin",
        "https://www.pech.ru/kamin.jpg",
        "краткое описание",
        {"Вес": "120 кг"},
        extra_images=["https://www.pech.ru/a.jpg", "https://www.pech.ru/b.jpg"],
        long_description="Очень длинное описание камина для теста.",
    )
    p = Proposal(id="gal", client=Client("Тест", "18 июня 2026 года"),
                 manager=Manager("Менеджер"),
                 items=[LineItem(o, 1)], services=[], discount=0)
    html = render_html(p, static_base="/static")
    # gallery slide
    assert "https://www.pech.ru/a.jpg" in html
    # description slide
    assert "Очень длинное описание" in html
    assert "Описание товара" in html


def test_render_related_slide():
    from kpgen.render.html import render_html
    from kpgen.models import Offer
    p = _proposal()
    p.related = [Offer("999","Сопутствующая печь Ромотоп",99999,None,"Romotop","157","https://www.pech.ru/x","pic","d",{})]
    html = render_html(p, static_base="/static")
    assert "Товары в этой категории" in html
    assert "Сопутствующая печь Ромотоп" in html
    assert "99&nbsp;999" in html
