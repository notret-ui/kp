from pathlib import Path
from kpgen.render.pdf import html_to_pdf

def test_html_to_pdf_produces_pdf(tmp_path):
    html = "<html><body><div style='width:1280px;height:720px;background:#ff6955'>КП</div></body></html>"
    out = tmp_path / "kp.pdf"
    html_to_pdf(html, str(out), base_url=None)
    data = out.read_bytes()
    assert data[:4] == b"%PDF"
    assert len(data) > 1000

def test_pdf_loads_external_css_and_fonts(tmp_path):
    """Регресс-гард: PDF должен подгружать внешние CSS+шрифты (file://-origin).
    При set_content (origin about:blank) подресурсы не грузятся и Museo не
    встраивается — тогда PDF получается ~50КБ. Со встроенными шрифтами он заметно
    крупнее (>100КБ). Рендерим реальное КП со static_base на каталог статики."""
    from kpgen.render.html import render_html
    from tests.test_render_html import _proposal
    static_uri = (Path("src/kpgen/render/static").resolve()).as_uri()
    html = render_html(_proposal(), static_base=static_uri)
    out = tmp_path / "kp_styled.pdf"
    html_to_pdf(html, str(out))
    data = out.read_bytes()
    assert data[:4] == b"%PDF"
    assert len(data) > 100_000, "PDF слишком мал — шрифты/стили не встроились (регресс file://-загрузки)"
