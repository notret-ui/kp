from pathlib import Path
from kpgen.scraper.site import extract_gallery_and_description

FX = Path(__file__).parent / "fixtures"


def test_extract():
    html = (FX / "product_page.html").read_text(encoding="utf-8")
    data = extract_gallery_and_description(html)
    assert len(data["images"]) >= 1
    assert len(data["description"]) > 20   # non-trivial description text


def test_extract_images_are_absolute():
    """Images should be absolute URLs (relative /... paths are resolved)."""
    html = (FX / "product_page.html").read_text(encoding="utf-8")
    data = extract_gallery_and_description(html)
    for img in data["images"]:
        assert img.startswith("https://"), f"Expected absolute URL, got: {img}"


def test_extract_deduplicates_images():
    """Duplicate fancybox hrefs should appear only once in the result."""
    html = """
    <html><body>
      <a data-fancybox="gallery" href="/upload/img1.jpg"><img src="/t/img1.jpg"/></a>
      <a data-fancybox="gallery" href="/upload/img1.jpg"><img src="/t/img1.jpg"/></a>
      <a data-fancybox="gallery" href="/upload/img2.jpg"><img src="/t/img2.jpg"/></a>
    </body></html>
    """
    data = extract_gallery_and_description(html)
    assert len(data["images"]) == 2
