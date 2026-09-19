import os
from app.sources.base import MarketplaceAdapter
from app.domain.models import SearchQuery


class AutoRuAdapter(MarketplaceAdapter):
    name = "autoru"
    capabilities = {"listing_search": False, "catalog": True}

    def search(self, query: SearchQuery) -> list:
        # Auto.ru's documented breadcrumbs API is catalog/reference data,
        # not a general public marketplace-listing search endpoint.
        # Keep catalog access in autoru_catalog.py and never fabricate listings.
        return []


adapter = AutoRuAdapter()
