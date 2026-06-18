import sqlite3
import json
from kpgen.models import Offer

def build_index(con: sqlite3.Connection, offers: dict[str, Offer]) -> None:
    con.execute("DROP TABLE IF EXISTS offers")
    con.execute("DROP TABLE IF EXISTS offers_fts")
    con.execute("""
        CREATE TABLE offers (
            offer_id TEXT PRIMARY KEY, name TEXT, price INTEGER, old_price INTEGER,
            vendor TEXT, category_id TEXT, url TEXT, picture TEXT,
            description TEXT, params TEXT
        )""")
    con.execute("""
        CREATE VIRTUAL TABLE offers_fts USING fts5(
            offer_id, name, vendor, content='offers', content_rowid='rowid')""")
    rows = [(o.offer_id, o.name, o.price, o.old_price, o.vendor, o.category_id,
             o.url, o.picture, o.description, json.dumps(o.params, ensure_ascii=False))
            for o in offers.values()]
    con.executemany("INSERT INTO offers VALUES (?,?,?,?,?,?,?,?,?,?)", rows)
    con.execute("""INSERT INTO offers_fts(rowid, offer_id, name, vendor)
                   SELECT rowid, offer_id, name, vendor FROM offers""")
    con.commit()

def _row_to_offer(r: sqlite3.Row) -> Offer:
    return Offer(r["offer_id"], r["name"], r["price"], r["old_price"], r["vendor"],
                 r["category_id"], r["url"], r["picture"], r["description"],
                 json.loads(r["params"]))

def search(con: sqlite3.Connection, query: str, limit: int = 20) -> list[Offer]:
    con.row_factory = sqlite3.Row
    q = query.strip()
    if not q:
        return []
    exact = con.execute("SELECT * FROM offers WHERE offer_id = ?", (q,)).fetchone()
    results: list[Offer] = [_row_to_offer(exact)] if exact else []
    fts_q = " ".join(f'"{t}"*' for t in q.split())
    rows = con.execute("""
        SELECT o.* FROM offers_fts f JOIN offers o ON o.rowid = f.rowid
        WHERE offers_fts MATCH ? ORDER BY rank LIMIT ?""", (fts_q, limit)).fetchall()
    for r in rows:
        o = _row_to_offer(r)
        if not exact or o.offer_id != exact["offer_id"]:
            results.append(o)
    return results[:limit]
