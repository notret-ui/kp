import sqlite3
import sys
from kpgen.feed.parser import parse_offers, merge_sklade
from kpgen.catalog.index import build_index

def build_db(db_path: str, main_xml: str, sklade_xml: str | None) -> int:
    offers = parse_offers(main_xml)
    if sklade_xml:
        merge_sklade(offers, sklade_xml)
    con = sqlite3.connect(db_path)
    build_index(con, offers)
    con.close()
    return len(offers)

if __name__ == "__main__":
    # Использование: python -m kpgen.catalog.cli <db> <main.xml> [sklade.xml]
    db, main_xml = sys.argv[1], sys.argv[2]
    sklade = sys.argv[3] if len(sys.argv) > 3 else None
    print("offers:", build_db(db, main_xml, sklade))
