import os
from dataclasses import dataclass

@dataclass
class Config:
    pech_xml_url: str
    pech_sklade_xml_url: str
    db_path: str
    data_dir: str

    @classmethod
    def from_env(cls) -> "Config":
        return cls(
            pech_xml_url=os.getenv("PECH_XML_URL", "https://www.pech.ru/list-products-1.xml"),
            pech_sklade_xml_url=os.getenv("PECH_SKLADE_XML_URL", "https://www.pech.ru/pech-na-sklade.xml"),
            db_path=os.getenv("KPGEN_DB", os.path.join(os.getcwd(), "data", "kpgen.sqlite")),
            data_dir=os.getenv("KPGEN_DATA_DIR", os.path.join(os.getcwd(), "data")),
        )
