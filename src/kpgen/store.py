import sqlite3
import json
from datetime import datetime
from dataclasses import asdict
from kpgen.models import Offer, LineItem, ServiceItem, Proposal, Client, Manager


class ProposalStore:
    def __init__(self, db_path: str):
        self.db_path = db_path
        con = sqlite3.connect(db_path)
        con.execute("CREATE TABLE IF NOT EXISTS proposals (id TEXT PRIMARY KEY, data TEXT)")
        cols = [r[1] for r in con.execute("PRAGMA table_info(proposals)").fetchall()]
        if "number" not in cols:
            con.execute("ALTER TABLE proposals ADD COLUMN number TEXT DEFAULT ''")
        con.commit()
        con.close()

    def next_number(self, today: str | None = None) -> str:
        """Следующий номер вида КП-ГГГГММДД-NNN (порядковый за текущий день)."""
        today = today or datetime.now().strftime("%Y%m%d")
        prefix = f"КП-{today}-"
        con = sqlite3.connect(self.db_path)
        n = con.execute("SELECT count(*) FROM proposals WHERE number LIKE ?", (prefix + "%",)).fetchone()[0]
        con.close()
        return f"{prefix}{n + 1:03d}"

    def save(self, p: Proposal) -> None:
        data = json.dumps(asdict(p), ensure_ascii=False)
        con = sqlite3.connect(self.db_path)
        con.execute("INSERT OR REPLACE INTO proposals (id, data, number) VALUES (?, ?, ?)",
                    (p.id, data, p.number))
        con.commit()
        con.close()

    def list_summaries(self) -> list[dict]:
        """Сводка по всем КП, новые сверху. {id, client_name, date, grand_total}."""
        from kpgen.pricing import compute_totals
        con = sqlite3.connect(self.db_path)
        rows = con.execute("SELECT id FROM proposals ORDER BY rowid DESC").fetchall()
        con.close()
        out = []
        for (pid,) in rows:
            p = self.load(pid)
            if p is None:
                continue
            out.append({
                "id": p.id,
                "number": p.number,
                "client_name": p.client.name,
                "date": p.client.date,
                "grand_total": compute_totals(p).grand_total,
            })
        return out

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
            items=[LineItem(offer=Offer(**{**{"extra_images": [], "long_description": ""}, **li["offer"]}), qty=li["qty"]) for li in d["items"]],
            services=[ServiceItem(**s) for s in d["services"]],
            discount=d["discount"],
            related=[Offer(**{**{"extra_images": [], "long_description": ""}, **o}) for o in d.get("related", [])],
            cross_sell=[Offer(**{**{"extra_images": [], "long_description": ""}, **o}) for o in d.get("cross_sell", [])],
            number=d.get("number", ""),
        )
