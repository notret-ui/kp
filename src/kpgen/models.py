from dataclasses import dataclass, field

@dataclass
class Offer:
    offer_id: str
    name: str
    price: int
    old_price: int | None
    vendor: str
    category_id: str
    url: str
    picture: str
    description: str
    params: dict[str, str] = field(default_factory=dict)
    extra_images: list[str] = field(default_factory=list)
    long_description: str = ""

    @property
    def has_discount(self) -> bool:
        return self.old_price is not None and self.old_price > self.price

@dataclass
class LineItem:
    offer: Offer
    qty: int = 1

    @property
    def line_sum(self) -> int:
        return self.offer.price * self.qty

@dataclass
class ServiceItem:
    title: str
    amount: int  # рубли, может быть отрицательной для скидки

@dataclass
class Manager:
    name: str
    role: str = "Старший менеджер"
    email: str = ""
    phone: str = ""

@dataclass
class Client:
    name: str
    date: str  # уже отформатированная строка, напр. "20 августа 2025 года"

@dataclass
class Proposal:
    id: str
    client: Client
    manager: Manager
    items: list[LineItem] = field(default_factory=list)
    services: list[ServiceItem] = field(default_factory=list)
    discount: int = 0  # скидка на КП в целом, рубли (положительное число)
    related: list[Offer] = field(default_factory=list)
    cross_sell: list[Offer] = field(default_factory=list)  # доптовары смежных категорий
    number: str = ""  # человеческий номер вида КП-ГГГГММДД-NNN
