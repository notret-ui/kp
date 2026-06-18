from dataclasses import dataclass
from kpgen.models import Proposal

@dataclass
class Totals:
    items_sum: int
    services_sum: int
    discount: int
    grand_total: int

def compute_totals(p: Proposal) -> Totals:
    items_sum = sum(li.line_sum for li in p.items)
    services_sum = sum(s.amount for s in p.services)
    grand = items_sum + services_sum - p.discount
    return Totals(items_sum, services_sum, p.discount, max(0, grand))
