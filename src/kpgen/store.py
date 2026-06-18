import sqlite3
import json
from dataclasses import asdict
from kpgen.models import Offer, LineItem, ServiceItem, Proposal, Client, Manager


class ProposalStore:
    def __init__(self, db_path: str):
        self.db_path = db_path
        con = sqlite3.connect(db_path)
        con.execute("CREATE TABLE IF NOT EXISTS proposals (id TEXT PRIMARY KEY, data TEXT)")
        con.commit()
        con.close()

    def save(self, p: Proposal) -> None:
        data = json.dumps(asdict(p), ensure_ascii=False)
        con = sqlite3.connect(self.db_path)
        con.execute("INSERT OR REPLACE INTO proposals VALUES (?, ?)", (p.id, data))
        con.commit()
        con.close()

    def load(self, pid: str) -> Proposal | None:
        con = sqlite3.connect(self.db_path)
        row = con.execute("SELECT data FROM proposals WHERE id = ?", (pid,)).fetchone()
        con.close()
        if row is None:
            return None
        d = json.loads(row[0])
        return Proposal(
            id=d["id"],
            client=Client(**d["client"]),
            manager=Manager(**d["manager"]),
            items=[LineItem(offer=Offer(**li["offer"]), qty=li["qty"]) for li in d["items"]],
            services=[ServiceItem(**s) for s in d["services"]],
            discount=d["discount"],
        )
