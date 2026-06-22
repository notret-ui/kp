import os
from kpgen.web.app import create_app

app = create_app(
    catalog_db=os.getenv("KPGEN_CATALOG_DB", "data/kpgen.sqlite"),
    proposals_db=os.getenv("KPGEN_PROPOSALS_DB", "data/proposals.sqlite"),
    enrich_from_site=True,
)
