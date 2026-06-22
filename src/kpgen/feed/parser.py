from lxml import etree
from kpgen.models import Offer


def _text(el, tag: str) -> str:
    child = el.find(tag)
    return child.text.strip() if child is not None and child.text else ""


def _full_text(el, tag: str) -> str:
    child = el.find(tag)
    if child is None:
        return ""
    return "".join(child.itertext()).strip()


def _int_or_none(s: str) -> int | None:
    s = s.strip().replace("\xa0", "").replace(" ", "").replace(",", ".")
    if not s:
        return None
    try:
        v = int(round(float(s)))
    except ValueError:
        return None
    return v if v >= 0 else None   # negative price is invalid


def parse_offers(path: str) -> dict[str, Offer]:
    """Основной фид -> {offer_id: Offer}. Потоковый парсинг (фид большой)."""
    offers: dict[str, Offer] = {}
    context = etree.iterparse(path, events=("end",), tag="offer")
    for _, el in context:
        oid = el.get("id")
        if oid:
            params = {p.get("name"): (p.text or "").strip()
                      for p in el.findall("param") if p.get("name")}
            offers[oid] = Offer(
                offer_id=oid,
                name=_text(el, "name"),
                price=_int_or_none(_text(el, "price")) or 0,
                old_price=_int_or_none(_text(el, "oldprice")),
                vendor=_text(el, "vendor"),
                category_id=_text(el, "categoryId"),
                url=_text(el, "url"),
                picture=_text(el, "picture"),
                description=_full_text(el, "description"),
                params=params,
            )
        el.clear()
        while el.getprevious() is not None:
            del el.getparent()[0]
    return offers


def merge_sklade(offers: dict[str, Offer], sklade_path: str) -> None:
    """Фид «на складе»: price = со скидкой, oldprice = РРЦ. Обновляем на месте."""
    context = etree.iterparse(sklade_path, events=("end",), tag="offer")
    for _, el in context:
        oid = el.get("id")
        if oid and oid in offers:
            price = _int_or_none(_text(el, "price"))
            old = _int_or_none(_text(el, "oldprice"))
            if price is not None:
                offers[oid].price = price
            if old is not None:
                offers[oid].old_price = old
        el.clear()
        while el.getprevious() is not None:
            del el.getparent()[0]
