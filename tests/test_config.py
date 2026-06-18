import os
from kpgen.config import Config

def test_config_defaults(monkeypatch):
    monkeypatch.delenv("PECH_XML_URL", raising=False)
    cfg = Config.from_env()
    assert cfg.pech_xml_url == "https://www.pech.ru/list-products-1.xml"
    assert cfg.pech_sklade_xml_url == "https://www.pech.ru/pech-na-sklade.xml"
    assert cfg.db_path.endswith("kpgen.sqlite")

def test_config_env_override(monkeypatch):
    monkeypatch.setenv("PECH_XML_URL", "http://example/feed.xml")
    cfg = Config.from_env()
    assert cfg.pech_xml_url == "http://example/feed.xml"
