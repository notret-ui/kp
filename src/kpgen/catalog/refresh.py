import os
import tempfile
import httpx
from kpgen.catalog.cli import build_db


def _download(url: str, dest: str) -> None:
    with httpx.stream("GET", url, timeout=120, follow_redirects=True) as r:
        r.raise_for_status()
        with open(dest, "wb") as f:
            for chunk in r.iter_bytes():
                f.write(chunk)


def build_from_feeds(db_path: str, main_url: str, sklade_url: str | None,
                     download=_download) -> int:
    """Скачивает фид(ы) во временные файлы и строит каталог. `download` инъектируется для тестов."""
    tmpdir = tempfile.mkdtemp()
    main_xml = os.path.join(tmpdir, "main.xml")
    download(main_url, main_xml)
    sklade_xml = None
    if sklade_url:
        sklade_xml = os.path.join(tmpdir, "sklade.xml")
        download(sklade_url, sklade_xml)
    return build_db(db_path, main_xml, sklade_xml)


def main() -> None:
    db = os.getenv("KPGEN_CATALOG_DB", "data/kpgen.sqlite")
    main_url = os.getenv("PECH_XML_URL", "https://www.pech.ru/list-products-1.xml")
    sklade_url = os.getenv("PECH_SKLADE_XML_URL", "https://www.pech.ru/pech-na-sklade.xml")
    os.makedirs(os.path.dirname(db) or ".", exist_ok=True)
    n = build_from_feeds(db, main_url, sklade_url)
    print(f"catalog built: {n} offers -> {db}")


if __name__ == "__main__":
    main()
