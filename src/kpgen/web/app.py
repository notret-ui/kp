import sqlite3
import secrets
import tempfile
import os
from pathlib import Path
from dataclasses import asdict
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from jinja2 import Environment, FileSystemLoader
from pydantic import BaseModel
from starlette.background import BackgroundTask
from kpgen.catalog.index import search, related_offers
from kpgen.models import Offer, LineItem, ServiceItem, Proposal, Client, Manager
from kpgen.store import ProposalStore
from kpgen.render.html import render_html
from kpgen.render.pdf import html_to_pdf
from kpgen.scraper.site import fetch_and_cache


class ClientIn(BaseModel):
    name: str
    date: str = ""


class ManagerIn(BaseModel):
    name: str
    role: str = "Старший менеджер"
    email: str = ""
    phone: str = ""


class ItemIn(BaseModel):
    offer_id: str
    qty: int = 1


class ServiceIn(BaseModel):
    title: str
    amount: int


class ProposalIn(BaseModel):
    client: ClientIn
    manager: ManagerIn
    items: list[ItemIn] = []
    services: list[ServiceIn] = []
    discount: int = 0

_STATIC = Path(__file__).parent.parent / "render" / "static"
_TEMPLATES = Path(__file__).parent.parent / "render" / "templates"

_jinja_env = Environment(loader=FileSystemLoader(str(_TEMPLATES)), autoescape=True)

def create_app(catalog_db: str, proposals_db: str, enrich_from_site: bool = False) -> FastAPI:
    app = FastAPI()
    app.mount("/static", StaticFiles(directory=str(_STATIC)), name="static")
    store = ProposalStore(proposals_db)

    @app.get("/", response_class=HTMLResponse)
    def form():
        tmpl = _jinja_env.get_template("form.html.j2")
        return tmpl.render(static="/static")

    def _catalog() -> sqlite3.Connection:
        return sqlite3.connect(catalog_db)

    def _offer_by_id(con, oid: str) -> Offer | None:
        res = search(con, oid)
        return next((o for o in res if o.offer_id == oid), None)

    @app.get("/api/search")
    def api_search(q: str):
        con = _catalog()
        try:
            return [asdict(o) for o in search(con, q)]
        finally:
            con.close()

    @app.post("/api/proposals")
    def create_proposal(payload: ProposalIn):
        con = _catalog()
        try:
            items = []
            for it in payload.items:
                offer = _offer_by_id(con, it.offer_id)
                if offer is None:
                    raise HTTPException(404, f"offer {it.offer_id} not found")
                items.append(LineItem(offer=offer, qty=it.qty))
        finally:
            con.close()
        if enrich_from_site:
            cache = sqlite3.connect(proposals_db)
            try:
                for li in items:
                    try:
                        extra = fetch_and_cache(li.offer.offer_id, li.offer.url, cache)
                        li.offer.extra_images = list(extra.get("images", []))[:6]
                        li.offer.long_description = extra.get("description", "")
                    except Exception:
                        pass
            finally:
                cache.close()
        related = []
        try:
            rcon = _catalog()
            try:
                related = related_offers(
                    rcon,
                    [li.offer.category_id for li in items],
                    [li.offer.offer_id for li in items],
                    limit=3,
                )
            finally:
                rcon.close()
        except Exception:
            related = []
        p = Proposal(
            id=secrets.token_urlsafe(16),  # ~128 бит: ID — единственный гейт к КП (ссылка-капабилити)
            client=Client(name=payload.client.name, date=payload.client.date),
            manager=Manager(
                name=payload.manager.name,
                role=payload.manager.role,
                email=payload.manager.email,
                phone=payload.manager.phone,
            ),
            items=items,
            services=[ServiceItem(title=s.title, amount=s.amount) for s in payload.services],
            discount=payload.discount,
            related=related,
        )
        store.save(p)
        return {"id": p.id}

    @app.get("/kp/{pid}.pdf")
    def proposal_pdf(pid: str):
        p = store.load(pid)
        if p is None:
            raise HTTPException(404, "proposal not found")
        html = render_html(p, static_base=str(_STATIC.as_uri()))
        fd, tmp = tempfile.mkstemp(suffix=".pdf")
        os.close(fd)
        html_to_pdf(html, tmp, base_url=None)
        return FileResponse(tmp, media_type="application/pdf", filename=f"kp-{pid}.pdf",
                            background=BackgroundTask(os.unlink, tmp))

    @app.get("/kp/{pid}", response_class=HTMLResponse)
    def view_proposal(pid: str):
        p = store.load(pid)
        if p is None:
            raise HTTPException(404, "proposal not found")
        return render_html(p, static_base="/static")

    return app
