import sqlite3
import uuid
from pathlib import Path
from dataclasses import asdict
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from kpgen.catalog.index import search
from kpgen.models import Offer, LineItem, ServiceItem, Proposal, Client, Manager
from kpgen.store import ProposalStore
from kpgen.render.html import render_html
from kpgen.render.pdf import html_to_pdf

_STATIC = Path(__file__).parent.parent / "render" / "static"

def create_app(catalog_db: str, proposals_db: str) -> FastAPI:
    app = FastAPI()
    app.mount("/static", StaticFiles(directory=str(_STATIC)), name="static")
    store = ProposalStore(proposals_db)

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
    def create_proposal(payload: dict):
        con = _catalog()
        try:
            items = []
            for it in payload.get("items", []):
                offer = _offer_by_id(con, it["offer_id"])
                if offer is None:
                    raise HTTPException(404, f"offer {it['offer_id']} not found")
                items.append(LineItem(offer=offer, qty=int(it.get("qty", 1))))
        finally:
            con.close()
        p = Proposal(
            id=uuid.uuid4().hex[:10],
            client=Client(**payload["client"]),
            manager=Manager(**payload["manager"]),
            items=items,
            services=[ServiceItem(**s) for s in payload.get("services", [])],
            discount=int(payload.get("discount", 0)),
        )
        store.save(p)
        return {"id": p.id}

    @app.get("/kp/{pid}", response_class=HTMLResponse)
    def view_proposal(pid: str):
        p = store.load(pid)
        if p is None:
            raise HTTPException(404, "proposal not found")
        return render_html(p, static_base="/static")

    @app.get("/kp/{pid}.pdf")
    def proposal_pdf(pid: str):
        p = store.load(pid)
        if p is None:
            raise HTTPException(404, "proposal not found")
        html = render_html(p, static_base=str(_STATIC.as_uri()))
        out = Path(proposals_db).parent / f"kp-{pid}.pdf"
        html_to_pdf(html, str(out), base_url=None)
        return FileResponse(str(out), media_type="application/pdf", filename=f"kp-{pid}.pdf")

    return app
