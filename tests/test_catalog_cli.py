import sqlite3
from pathlib import Path
from kpgen.catalog.cli import build_db

FX = Path(__file__).parent / "fixtures"

def test_build_db(tmp_path):
    db = tmp_path / "kp.sqlite"
    n = build_db(str(db), str(FX / "products_small.xml"), str(FX / "sklade_small.xml"))
    assert n == 1
    con = sqlite3.connect(str(db))
    price = con.execute("SELECT price FROM offers WHERE offer_id='23954'").fetchone()[0]
    assert price == 45000  # из sklade
