"""
Scraper for pech.ru product pages.

Extracts:
- Gallery images: from ``a[data-fancybox]`` anchors whose ``href`` attribute
  points to the medium-resolution product photo.  Relative URLs are resolved
  to ``https://www.pech.ru``.
- Long description: text content of all ``.kr_product_description_block``
  divs joined into a single string.

Results are cached in a SQLite table ``product_extra`` so each offer URL is
fetched at most once.
"""

from __future__ import annotations

import json
import sqlite3
from typing import Any

import httpx
from lxml import html as H

_BASE = "https://www.pech.ru"
_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)


def extract_gallery_and_description(page_html: str) -> dict[str, Any]:
    """Parse a pech.ru product page and return images and description.

    Selectors (verified against live markup on 2026-06-18):
    - Images: ``a[data-fancybox]`` — href contains a medium-res JPEG path;
      relative paths are resolved against ``https://www.pech.ru``.
    - Description: ``.kr_product_description_block`` divs — each block is a
      titled section (h3 + paragraph); all are joined with a single space.

    Returns:
        {"images": [str, ...], "description": str}
    """
    doc = H.fromstring(page_html)

    # --- Gallery images ---
    seen: set[str] = set()
    images: list[str] = []
    for anchor in doc.cssselect("a[data-fancybox]"):
        href = anchor.get("href") or ""
        if not href:
            continue
        if href.startswith("/"):
            href = _BASE + href
        if href not in seen:
            seen.add(href)
            images.append(href)

    # --- Description ---
    blocks = doc.cssselect(".kr_product_description_block")
    parts = []
    for block in blocks:
        text = block.text_content().strip()
        if text:
            parts.append(text)
    description = " ".join(parts)

    return {"images": images, "description": description}


def _ensure_table(con: sqlite3.Connection) -> None:
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS product_extra (
            offer_id    TEXT PRIMARY KEY,
            images      TEXT NOT NULL,
            description TEXT NOT NULL
        )
        """
    )
    con.commit()


def fetch_and_cache(
    offer_id: str,
    url: str,
    con: sqlite3.Connection,
) -> dict[str, Any]:
    """Fetch a pech.ru product page and cache the result in SQLite.

    On the first call for a given ``offer_id`` the URL is fetched via HTTP,
    parsed, and the result stored.  Subsequent calls return the cached row
    without making a network request.

    Args:
        offer_id: Primary key used for caching (must be unique per product).
        url: Full URL of the pech.ru product page.
        con: Open SQLite connection; the ``product_extra`` table is created
             automatically if it does not exist.

    Returns:
        {"images": [str, ...], "description": str}
    """
    _ensure_table(con)

    row = con.execute(
        "SELECT images, description FROM product_extra WHERE offer_id = ?",
        (offer_id,),
    ).fetchone()

    if row is not None:
        images_json, description = row
        return {"images": json.loads(images_json), "description": description}

    response = httpx.get(
        url,
        timeout=25,
        follow_redirects=True,
        headers={"User-Agent": _UA},
    )
    response.raise_for_status()

    data = extract_gallery_and_description(response.text)

    con.execute(
        "INSERT INTO product_extra (offer_id, images, description) VALUES (?, ?, ?)",
        (offer_id, json.dumps(data["images"], ensure_ascii=False), data["description"]),
    )
    con.commit()

    return data
