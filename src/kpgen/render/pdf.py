import os
import tempfile
from playwright.sync_api import sync_playwright


def html_to_pdf(html: str, out_path: str, base_url: str | None = None) -> None:
    """Рендер HTML в PDF. Слайды 16:9 landscape; печать фоновых цветов включена.

    HTML пишется во временный .html-файл и открывается через page.goto("file://..."),
    чтобы у страницы был file://-origin: только тогда Chromium подгружает внешние
    ресурсы (CSS-вёрстка слайдов, шрифты Museo). page.set_content создаёт страницу с
    origin about:blank, из которой такие подресурсы не грузятся (вёрстка и шрифты пропадают).
    """
    fd, tmp_html = tempfile.mkstemp(suffix=".html")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(html)
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page()
            page.goto("file://" + tmp_html, wait_until="networkidle")
            # width=1280 / height=720 уже задают ландшафтную страницу 16:9.
            # landscape=True вместе с явными width/height МЕНЯЕТ их местами
            # (страница становится портретной 720×1280) — поэтому его не указываем.
            page.pdf(path=out_path, print_background=True,
                     width="1280px", height="720px",
                     margin={"top": "0", "bottom": "0", "left": "0", "right": "0"})
            browser.close()
    finally:
        os.unlink(tmp_html)
