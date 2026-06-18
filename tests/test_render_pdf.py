from kpgen.render.pdf import html_to_pdf

def test_html_to_pdf_produces_pdf(tmp_path):
    html = "<html><body><div style='width:1280px;height:720px;background:#ff6955'>КП</div></body></html>"
    out = tmp_path / "kp.pdf"
    html_to_pdf(html, str(out), base_url=None)
    data = out.read_bytes()
    assert data[:4] == b"%PDF"
    assert len(data) > 1000
