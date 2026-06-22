from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape
from markupsafe import Markup
from kpgen.models import Proposal
from kpgen.pricing import compute_totals

_TPL_DIR = Path(__file__).parent / "templates"

def _rub(value: int) -> Markup:
    """123900 -> '123&nbsp;900' (разряды неразрывным пробелом), не экранируется."""
    s = f"{int(value):,}".replace(",", "&nbsp;")
    return Markup(s)

def _env() -> Environment:
    env = Environment(loader=FileSystemLoader(str(_TPL_DIR)),
                      autoescape=select_autoescape(["html", "j2"]))
    env.filters["rub"] = _rub
    return env

def render_html(p: Proposal, static_base: str = "/static") -> str:
    env = _env()
    tpl = env.get_template("kp.html.j2")
    return tpl.render(p=p, totals=compute_totals(p), static=static_base)
