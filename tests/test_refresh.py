import shutil
import sqlite3
from pathlib import Path

from kpgen.catalog.refresh import build_from_feeds

FX = Path(__file__).parent / "fixtures"


def test_build_from_feeds_with_fake_downloader(tmp_path):
    mapping = {
        "http://x/main": FX / "products_small.xml",
        "http://x/sklade": FX / "sklade_small.xml",
    }

    def fake_dl(url, dest):
        shutil.copy(mapping[url], dest)

    db = tmp_path / "c.sqlite"
    n = build_from_feeds(str(db), "http://x/main", "http://x/sklade", download=fake_dl)
    assert n == 1
    con = sqlite3.connect(str(db))
    assert con.execute("SELECT price FROM offers WHERE offer_id='23954'").fetchone()[0] == 45000
