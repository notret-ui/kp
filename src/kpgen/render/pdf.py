from playwright.sync_api import sync_playwright


def html_to_pdf(html: str, out_path: str, base_url: str | None = None) -> None:
    """Рендер HTML в PDF. Слайды 16:9 landscape; печать фоновых цветов включена."""
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page()
        page.set_content(html, wait_until="networkidle")
        page.pdf(path=out_path, landscape=True, print_background=True,
                 width="1280px", height="720px",
                 margin={"top": "0", "bottom": "0", "left": "0", "right": "0"})
        browser.close()
