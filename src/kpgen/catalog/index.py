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
    fts_q = " ".join(f'"{t.replace(chr(34), chr(34)*2)}"*' for t in q.split())
    rows = con.execute("""
        SELECT o.* FROM offers_fts f JOIN offers o ON o.rowid = f.rowid
        WHERE offers_fts MATCH ? ORDER BY rank LIMIT ?""", (fts_q, limit)).fetchall()
    for r in rows:
        o = _row_to_offer(r)
        if not exact or o.offer_id != exact["offer_id"]:
            results.append(o)
    return results[:limit]

def related_offers(con: sqlite3.Connection, category_ids, exclude_ids, limit: int = 3) -> list[Offer]:
    """Сопутствующие: другие товары тех же категорий, кроме уже добавленных."""
    con.row_factory = sqlite3.Row
    cats = [c for c in dict.fromkeys(category_ids) if c]
    if not cats:
        return []
    ph = ",".join("?" * len(cats))
    rows = con.execute(
        f"SELECT * FROM offers WHERE category_id IN ({ph}) ORDER BY price DESC", cats
    ).fetchall()
    seen = set(exclude_ids)
    out: list[Offer] = []
    for r in rows:
        if r["offer_id"] in seen:
            continue
        out.append(_row_to_offer(r))
        seen.add(r["offer_id"])
        if len(out) >= limit:
            break
    return out
